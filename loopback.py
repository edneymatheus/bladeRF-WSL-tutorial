#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
loopback.py  —  bladeRF TX0 -> RX0 com FFT em tempo real

Objetivo:
  • Transmitir um tom contínuo no TX0
  • Receber no RX0
  • Plotar o espectro em tempo real
  • Ao desconectar o cabo do RX, o pico deve cair para o ruído

Observações importantes:
  • Use: TX0 -> atenuador 20~30 dB -> RX0
  • O tom é deslocado em baseband (+40 kHz por padrão) para evitar o pico em DC
  • Em RF continua sendo um CW único

Exemplo:
  python3 loopback_live.py --freq 100e6 --fs 3e6 --tone 40e3 --tx_gain -20 --rx_gain 20
"""

import argparse
import threading
import time
import logging
import sys

import numpy as np
import matplotlib.pyplot as plt
from bladerf import _bladerf


# ──────────────────────────────────────────────────────────────
#  ▒▒  Argumentos
# ──────────────────────────────────────────────────────────────
ap = argparse.ArgumentParser()

ap.add_argument('--freq', type=float, default=100e6,
                help='frequência central RF (Hz)')
ap.add_argument('--fs', type=float, default=3e6,
                help='sample rate (Hz)')
ap.add_argument('--bw', type=float, default=None,
                help='bandwidth (Hz). Default = fs/2')
ap.add_argument('--tone', type=float, default=40e3,
                help='offset do tom em baseband (Hz). Evite 0 Hz.')
ap.add_argument('--nsamp', type=int, default=4096,
                help='amostras por bloco / FFT')
ap.add_argument('--amp', type=int, default=512,
                help='amplitude SC16_Q11 do tom (máx seguro: < 2047)')
ap.add_argument('--tx_gain', type=int, default=-20,
                help='ganho TX0')
ap.add_argument('--rx_gain', type=int, default=20,
                help='ganho RX0')
ap.add_argument('--window', choices=['hanning', 'bharris'], default='bharris',
                help='janela FFT')
ap.add_argument('--throw', type=int, default=4,
                help='blocos descartados no início')
ap.add_argument('--ylim_min', type=float, default=-140,
                help='limite inferior do eixo Y (dBFS)')
ap.add_argument('--ylim_max', type=float, default=10,
                help='limite superior do eixo Y (dBFS)')
ap.add_argument('--timeout_ms', type=int, default=3500,
                help='timeout do stream')
ap.add_argument('--log', default='WARNING')

args = ap.parse_args()
logging.basicConfig(level=getattr(logging, args.log.upper()))

if args.bw is None:
    args.bw = args.fs / 2


# ──────────────────────────────────────────────────────────────
#  ▒▒  Estado global
# ──────────────────────────────────────────────────────────────
running = threading.Event()


# ──────────────────────────────────────────────────────────────
#  ▒▒  Funções auxiliares
# ──────────────────────────────────────────────────────────────
def rssi_block_dbfs(i, q):
    p = np.mean(i.astype(np.float64)**2 + q.astype(np.float64)**2)
    return 10*np.log10(p/(2047.0**2) + 1e-12)

def blackman_harris(N):
    n = np.arange(N)
    return (0.35875
            - 0.48829*np.cos(2*np.pi*n/(N-1))
            + 0.14128*np.cos(4*np.pi*n/(N-1))
            - 0.01168*np.cos(6*np.pi*n/(N-1)))

def make_window(N, kind):
    return blackman_harris(N) if kind == 'bharris' else np.hanning(N)

def make_tone_payload(nsamp, fs, f_tone, amp):
    t = np.arange(nsamp) / fs
    sig = (amp / 2047.0) * np.exp(1j * 2*np.pi * f_tone * t)

    i16 = np.round(sig.real * 2047).astype(np.int16)
    q16 = np.round(sig.imag * 2047).astype(np.int16)

    inter = np.empty(nsamp * 2, dtype=np.int16)
    inter[0::2] = i16
    inter[1::2] = q16
    return inter.tobytes()

def configure_device(sdr, tx_ch, rx_ch):
    # Frequências
    sdr.set_frequency(tx_ch, int(args.freq))
    sdr.set_frequency(rx_ch, int(args.freq))

    # Taxas e banda
    sdr.set_sample_rate(tx_ch, int(args.fs))
    sdr.set_sample_rate(rx_ch, int(args.fs))
    sdr.set_bandwidth(tx_ch, int(args.bw))
    sdr.set_bandwidth(rx_ch, int(args.bw))

    # Ganhos
    sdr.set_gain(tx_ch, int(args.tx_gain))
    sdr.set_gain(rx_ch, int(args.rx_gain))

    # RX manual
    try:
        sdr.set_gain_mode(rx_ch, _bladerf.GainMode.Manual)
    except Exception:
        pass

    # Streams síncronos
    sdr.sync_config(
        _bladerf.ChannelLayout.TX_X1,
        _bladerf.Format.SC16_Q11,
        16, args.nsamp, 8, args.timeout_ms
    )

    sdr.sync_config(
        _bladerf.ChannelLayout.RX_X1,
        _bladerf.Format.SC16_Q11,
        16, args.nsamp, 8, args.timeout_ms
    )


# ──────────────────────────────────────────────────────────────
#  ▒▒  Thread TX
# ──────────────────────────────────────────────────────────────
def tx_loop(sdr, tx_ch, payload):
    try:
        sdr.enable_module(tx_ch, True)
        while running.is_set():
            sdr.sync_tx(payload, args.nsamp)
    finally:
        try:
            sdr.enable_module(tx_ch, False)
        except Exception:
            pass
        time.sleep(0.05)


# ──────────────────────────────────────────────────────────────
#  ▒▒  RX + plot em tempo real
# ──────────────────────────────────────────────────────────────
def rx_plot_loop(sdr, rx_ch):
    W = make_window(args.nsamp, args.window)
    freq_axis = np.fft.fftshift(np.fft.fftfreq(args.nsamp, d=1/args.fs))
    freq_axis_khz = freq_axis / 1e3

    tone_idx = int(np.argmin(np.abs(freq_axis - args.tone)))

    buf_rx = bytearray(args.nsamp * 4)   # 1 canal RX, SC16_Q11 => 4 bytes por amostra complexa

    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 5))
    line, = ax.plot(freq_axis_khz, np.full(args.nsamp, args.ylim_min), lw=1.0)
    marker = ax.axvline(args.tone/1e3, linestyle='--', linewidth=1.0)

    ax.set_xlabel('Frequência baseband (kHz)')
    ax.set_ylabel('Magnitude (dBFS, aprox.)')
    ax.set_title('bladeRF loopback TX0 -> RX0')
    ax.set_xlim(freq_axis_khz[0], freq_axis_khz[-1])
    ax.set_ylim(args.ylim_min, args.ylim_max)
    ax.grid(True)

    try:
        sdr.enable_module(rx_ch, True)

        # Descarta alguns blocos iniciais
        for _ in range(args.throw):
            sdr.sync_rx(buf_rx, args.nsamp)

        while running.is_set() and plt.fignum_exists(fig.number):
            sdr.sync_rx(buf_rx, args.nsamp)

            d = np.frombuffer(buf_rx, np.int16)
            i = d[0::2]
            q = d[1::2]
            iq = (i + 1j*q) * W

            spec = np.fft.fftshift(np.fft.fft(iq))

            # Normalização aproximada para dBFS de tom
            mag = np.abs(spec) / (np.sum(W) * 2047.0 + 1e-12)
            mag_db = 20*np.log10(mag + 1e-12)

            tone_db = float(mag_db[tone_idx])
            rssi_db = float(rssi_block_dbfs(i, q))

            line.set_ydata(mag_db)
            ax.set_title(
                f"Loopback TX0->RX0 | Tone @ {args.tone/1e3:.1f} kHz = {tone_db:.1f} dBFS | "
                f"RSSI = {rssi_db:.1f} dBFS | "
                f"fc = {args.freq/1e6:.3f} MHz | fs = {args.fs/1e6:.3f} MS/s"
            )

            fig.canvas.draw()
            fig.canvas.flush_events()
            plt.pause(0.001)

    finally:
        try:
            sdr.enable_module(rx_ch, False)
        except Exception:
            pass
        time.sleep(0.05)
        running.clear()
        plt.ioff()


# ──────────────────────────────────────────────────────────────
#  ▒▒  MAIN
# ──────────────────────────────────────────────────────────────
sdr = None
thr_tx = None

try:
    sdr = _bladerf.BladeRF()

    tx = _bladerf.CHANNEL_TX(0)
    rx = _bladerf.CHANNEL_RX(0)

    configure_device(sdr, tx, rx)

    payload = make_tone_payload(
        nsamp=args.nsamp,
        fs=args.fs,
        f_tone=args.tone,
        amp=args.amp
    )

    running.set()

    thr_tx = threading.Thread(target=tx_loop, args=(sdr, tx, payload), daemon=True)
    thr_tx.start()

    time.sleep(0.05)

    rx_plot_loop(sdr, rx)

except KeyboardInterrupt:
    running.clear()

except Exception as e:
    running.clear()
    print(f'Erro: {e}', file=sys.stderr)
    raise

finally:
    running.clear()

    if thr_tx is not None:
        thr_tx.join(timeout=1.0)

    if sdr is not None:
        try:
            sdr.close()
        except Exception:
            pass
