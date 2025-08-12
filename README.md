# Tutorial: Instalando e Configurando o bladeRF no Windows Subsystem for Linux (WSL)

Este tutorial orienta no processo de instalação e configuração do **bladeRF** no Windows Subsystem for Linux (WSL2), integrando também dicas adicionais obtidas na prática e ajustes para compatibilidade com as versões mais recentes do `usbipd-win`. O **bladeRF** é um transceptor SDR (Software Defined Radio) versátil para desenvolvimento e teste de sistemas de rádio flexíveis. Com o WSL2, é possível executar um ambiente Linux diretamente no Windows, integrando ferramentas Linux ao seu fluxo de trabalho.

## Índice
1. [Pré-requisitos](#pré-requisitos)
2. [Configurando o Ambiente no WSL](#configurando-o-ambiente-no-wsl)
3. [Conectando a bladeRF ao WSL](#conectando-a-bladerf-ao-wsl)
4. [Instalando o bladeRF](#instalando-o-bladerf)
   - 4.1 [Instalando as Dependências](#41-instalando-as-dependências)
   - 4.2 [Compilando e Instalando o libbladeRF](#42-compilando-e-instalando-o-libbladerf)
5. [Preparação do bladeRF](#preparação-do-bladerf)
   - 5.1 [Baixando os Arquivos de Firmware e FPGA](#51-baixando-os-arquivos-de-firmware-e-fpga)
   - 5.2 [Atualizando o Firmware](#52-atualizando-o-firmware)
   - 5.3 [Carregando e Configurando o Bitstream da FPGA](#53-carregando-e-configurando-o-bitstream-da-fpga)
6. [Testando o bladeRF](#testando-o-bladerf)
7. [Usando o bladeRF com Python](#usando-o-bladerf-com-python)
   - 7.1 [Criando Ambiente Virtual](#71-criando-ambiente-virtual)
   - 7.2 [Instalando Bindings Python](#72-instalando-bindings-python)
   - 7.3 [Teste de Acesso via Python](#73-teste-de-acesso-via-python)
8. [Problemas Comuns e Soluções](#problemas-comuns-e-soluções)
9. [Conclusão](#conclusão)
10. [Referências](#referências)

---

## Pré-requisitos
- **Windows 10 (2004+)** ou **Windows 11** com WSL2 configurado.
- **Ubuntu 22.04 ou 24.04** instalado no WSL.
- **Acesso de administrador** no Windows para instalar drivers e usar o `usbipd`.
- **Cabo USB 3.0** de dados e porta USB 3.0 para máximo throughput.
- **Placa bladeRF** (1.x ou 2.x).
- **Opcional:** Servidor X no Windows (VcXsrv/Xming) para aplicações gráficas.

---

## Configurando o Ambiente no WSL
No Ubuntu (WSL):
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y build-essential cmake git pkg-config libusb-1.0-0-dev libcurl4-openssl-dev libtecla-dev libglib2.0-dev
```

---

## Conectando a bladeRF ao WSL
1. Instale o `usbipd-win` no Windows:
```powershell
winget install usbipd
```

2. Conecte a bladeRF na porta USB 3.0.

3. No PowerShell (Admin):
```powershell
usbipd list                  # Anote o BUSID da bladeRF
usbipd bind --busid <BUSID>
usbipd attach --wsl --busid <BUSID>
```

4. No Ubuntu (WSL), confirme:
```bash
lsusb
# Deve listar algo como: ID 2cf0:5250 Nuand bladeRF 2.0 micro
```

---

## Instalando o bladeRF

### 4.1 Instalando as Dependências
```bash
sudo apt install -y libusb-1.0-0-dev libcurl4-openssl-dev libtecla-dev libglib2.0-dev
```

### 4.2 Compilando e Instalando o libbladeRF
```bash
cd ~
git clone https://github.com/Nuand/bladeRF.git
cd bladeRF/host
git submodule update --init --recursive
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release -DINSTALL_UDEV_RULES=OFF ..
cmake --build . -- -j"$(nproc)"
sudo make install
sudo ldconfig
```
> No Linux o executável se chama **`bladeRF-cli`** (R e F maiúsculos).

---

## Preparação do bladeRF

### 5.1 Baixando os Arquivos de Firmware e FPGA
- Firmware: [https://www.nuand.com/fx3_images/](https://www.nuand.com/fx3_images/)
- FPGA: [https://www.nuand.com/fpga_images/](https://www.nuand.com/fpga_images/)

Ex.:  
- `bladeRF_fw_v2.5.0.img` (ou mais recente)  
- `hostedxA4_v0.16.0.rbf` (ajuste xA4 conforme modelo)

### 5.2 Atualizando o Firmware
```bash
bladeRF-cli -L ./bladeRF_fw_v2.5.0.img
```
Depois desconecte e reconecte a placa.

### 5.3 Carregando e Configurando o Bitstream da FPGA
```bash
bladeRF-cli -l ./hostedxA4_v0.16.0.rbf
```
Para carregar automaticamente na inicialização:
```bash
bladeRF-cli -L ./hostedxA4_v0.16.0.rbf
```

---

## Testando o bladeRF
```bash
bladeRF-cli -p        # Lista dispositivos
bladeRF-cli -i        # Modo interativo
```
No modo interativo:
```bladeRF
version
info
set frequency rx 100M
set samplerate rx 10M
rx config file=/tmp/samples.sc16 format=bin n=1000000
rx start
rx wait
quit
```
Depois verifique:
```bash
ls -lh /tmp/samples.sc16
```

---

## Usando o bladeRF com Python

### 7.1 Criando Ambiente Virtual
```bash
sudo apt install -y python3-venv
python3 -m venv bladerf_env
source bladerf_env/bin/activate
```

### 7.2 Instalando Bindings Python
```bash
pip install --upgrade pip cython numpy matplotlib
cd ~/bladeRF/host/libraries/libbladeRF_bindings/python
python3 setup.py install
```

### 7.3 Teste de Acesso via Python
```python
from bladerf import BladeRF
dev = BladeRF()
print("bladeRF conectado com sucesso!")
dev.close()
```

---

## Problemas Comuns e Soluções
- **`Using legacy message size`** → Atualize firmware ≥ v2.5.0 e FPGA ≥ v0.16.0 para melhor performance e compatibilidade.
- **`Device Speed: High`** → Está em USB 2.0; use porta/cabo USB 3.0.
- **`command not found`** → Use `bladeRF-cli` (case sensitive).
- **`Could NOT find CURL`** → Instale `libcurl4-openssl-dev`.
- **`No rule to make target 'bladerf-cli'`** → Compile com `cmake --build . --target bladeRF-cli`.

---

## Conclusão
Seguindo este guia, você terá:
- Ambiente WSL2 configurado.
- `libbladeRF` e `bladeRF-cli` instalados.
- Firmware e FPGA atualizados.
- Teste funcional no CLI e via Python.

Mantenha seu firmware/FPGA atualizados para maximizar throughput, estabilidade e compatibilidade com bibliotecas mais recentes.

---

## Referências
- [PySDR - Using the bladeRF](https://pysdr.org/content/bladerf.html)
- [bladeRF GitHub Repository](https://github.com/Nuand/bladeRF)
- [Nuand Firmware & FPGA Images](https://www.nuand.com/)
- [usbipd-win GitHub](https://github.com/dorssel/usbipd-win)
