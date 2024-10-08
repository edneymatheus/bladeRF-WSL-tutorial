# Tutorial: Instalando e Configurando o bladeRF no Windows Subsystem for Linux (WSL)

Este tutorial orienta você no processo de instalação e configuração do **bladeRF** no Windows Subsystem for Linux (WSL), seguindo o fluxo do guia disponível em [PySDR - Using the bladeRF](https://pysdr.org/content/bladerf.html). O **bladeRF** é um transceptor SDR (Software Defined Radio) que permite o desenvolvimento e teste de sistemas de rádio flexíveis. Com o WSL, você pode executar um ambiente Linux diretamente no Windows, facilitando a integração de ferramentas Linux no seu fluxo de trabalho.

## Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Configurando o Ambiente no WSL](#configurando-o-ambiente-no-wsl)
3. [Instalando o bladeRF](#instalando-o-bladerf)
   - 3.1 [Instalando as Dependências](#31-instalando-as-dependências)
   - 3.2 [Instalando o libbladeRF](#32-instalando-o-libbladerf)
4. [Preparação do bladeRF](#preparação-do-bladerf)
   - 4.1 [Baixando os Arquivos Necessários](#41-baixando-os-arquivos-necessários)
   - 4.2 [Atualizando o Firmware do bladeRF](#42-atualizando-o-firmware-do-bladerf)
   - 4.3 [Carregando e Configurando o Bitstream da FPGA](#43-carregando-e-configurando-o-bitstream-da-fpga)
5. [Testando o bladeRF](#testando-o-bladerf)
   - 5.1 [Recebendo Amostras](#51-recebendo-amostras)
6. [Instalando as Bibliotecas Python para bladeRF](#instalando-as-bibliotecas-python-para-bladerf)
   - 6.1 [Criando um Ambiente Virtual Python](#61-criando-um-ambiente-virtual-python)
   - 6.2 [Instalando as Dependências Python](#62-instalando-as-dependências-python)
   - 6.3 [Testando o Acesso via Python](#63-testando-o-acesso-via-python)
7. [Problemas Comuns e Soluções](#problemas-comuns-e-soluções)
   - 7.1 [Mensagens "Hit stall for buffer"](#71-mensagens-hit-stall-for-buffer)
8. [Conclusão](#conclusão)
9. [Referências](#referências)

---

## Pré-requisitos

- **Sistema Operacional:** Windows 10 (versão 2004 ou superior) ou Windows 11.
- **Acesso Administrativo:** Permissões para instalar softwares e modificar configurações do sistema.
- **Conexão com a Internet:** Necessária para baixar pacotes e dependências.
- **Dispositivo bladeRF:** Hardware bladeRF conectado ao computador.
- **X Server (opcional):** Para executar aplicações gráficas no WSL, você pode instalar um servidor X, como o Xming ou o VcXsrv.

---

## Configurando o Ambiente no WSL

Antes de instalar o bladeRF, precisamos atualizar os repositórios e instalar algumas dependências.

1. **Atualize os repositórios:**

   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```
2. **Instale algumas ferramentas essenciais:**

   ```bash
   sudo apt install -y build-essential cmake git libusb-1.0-0-dev libtecla-dev libglib2.0-dev
   ```
   
---

## Instalando o bladeRF
### 3.1 Instalando as Dependências
Certifique-se de que as seguintes bibliotecas estão instaladas:

   ```bash
   sudo apt install -y libusb-1.0-0-dev libtecla-dev libglib2.0-dev
   ```

### 3.2 Instalando o libbladeRF

1. Clone o repositório do bladeRF:

   ```bash
   git clone https://github.com/Nuand/bladeRF.git
   ```

2. Compile e instale o libbladeRF:

   ```bash
   cd bladeRF/host
   mkdir build
   cd build
   cmake ..
   make -J8
   sudo make install
   ```

---

## Preparação do bladeRF
### 4.1 Baixando os Arquivos Necessários
Baixe os arquivos mais recentes do firmware e do bitstream da FPGA:
- Firmware: [https://www.nuand.com/fx3_images/](https://www.nuand.com/fx3_images/)
- FPGA Bitstream: [https://www.nuand.com/fpga_images/](https://www.nuand.com/fpga_images/)

Arquivos necessários:
- `bladeRF_fw_latest.img`: Firmware do bladeRF.
- `hostedxA4-latest.rbf`: Bitstream para configurar a FPGA (substitua xA4 pelo modelo específico da sua FPGA, se necessário).

### 4.2 Atualizando o Firmware do bladeRF

1. Navegue até o diretório onde o firmware foi baixado:

   ```bash
   cd /caminho/para/o/diretorio/de/downloads
   ```
2. Atualize o firmware:

   ```bash
   bladeRF-cli -f ./bladeRF_fw_latest.img
   ```

3. Reinicie o dispositivo:
Desconecte e reconecte o bladeRF à porta USB.

4. Verifique a versão do firmware:

   ```bash
   bladeRF-cli -i
   ```
No prompt interativo, digite:

   ```bash
   info
   ```
Verifique se a versão do firmware é v2.4.0 ou superior.

Saia do prompt interativo:

   ```bash
   quit
   ```
### 4.3 Carregando e Configurando o Bitstream da FPGA
1. Carregue o bitstream da FPGA:

   ```bash
   bladeRF-cli -l ./hostedxA4-latest.rbf
   ```
- Interpretação da Saída: Deve aparecer **"Successfully loaded FPGA bitstream!"**.

2. Verifique se a FPGA foi configurada corretamente:

   ```bash
   bladeRF-tool info
   ```
   
3. Configuração Persistente:
Para que o bitstream seja carregado automaticamente na inicialização:

   ```bash
   bladeRF-cli -L ./hostedxA4-latest.rbf
   ```

---

## Testando o bladeRF
### 5.1 Recebendo Amostras
1. Conecte seu dispositivo bladeRF ao computador.

2. Inicie o bladeRF-cli em modo interativo:

   ```bash
   bladeRF-cli -i
   ```

3. No prompt interativo, digite os seguintes comandos:

   ```bash
   set frequency 100M
   set samplerate 10M
   rx config file=/tmp/samples.sc16 format=bin n=1000000
   rx start
   rx wait
   quit
   ```

- Descrição:
  - `set frequency 100M`: Sintoniza em 100 MHz.
  - `set samplerate 10M`: Define a taxa de amostragem para 10 MHz.
  - `rx config`: Configura a recepção para salvar em `/tmp/samples.sc16`.
  - `rx start` e `rx wait`: Inicia a recepção e aguarda a conclusão.

4. Verifique o arquivo gerado:

   ```bash
   ls -lh /tmp/samples.sc16
   ```
O arquivo deve ter aproximadamente 4 MB.

---

## Instalando as Bibliotecas Python para bladeRF
### 6.1 Criando um Ambiente Virtual Python
1. Instale o `python3-venv` se ainda não estiver instalado:

   ```bash
   sudo apt install -y python3-venv
   ```

2. Crie e ative um ambiente virtual:

   ```bash
   python3 -m venv bladerf_env
   source bladerf_env/bin/activate
   ```
### 6.2 Instalando as Dependências Python
1. Atualize o `pip` e instale o `cython`:

   ```bash
   pip install --upgrade pip
   pip install cython
   ```

2. Instale as bindings do bladeRF para Python:

   ```bash
   cd ~/bladeRF/host/libraries/libbladeRF_bindings/python
   python3 setup.py install
   ```

3. Instale outros pacotes necessários:

   ```bash
   pip install numpy matplotlib
   ```

### 6.3 Testando o Acesso via Python
1. Crie um script Python de teste (`teste_bladerf.py`):

   ```bash
   from bladerf import BladeRF

   dev = BladeRF()
   print("bladeRF conectado com sucesso!")
   dev.close()
   ```

2. Execute o script:

   ```bash
   python3 teste_bladerf.py
   ```

Se a mensagem "bladeRF conectado com sucesso!" aparecer, a instalação foi bem-sucedida.

---

## Problemas Comuns e Soluções
### 7.1 Mensagens "Hit stall for buffer"
- Causa: Interrupções temporárias na comunicação USB durante a recepção de amostras.
- Solução: Essas mensagens são comuns e geralmente não afetam a qualidade dos dados coletados.

Dicas para Minimizar as Mensagens:
- Use uma porta USB 3.0 diretamente na máquina.
- Evite hubs USB ou extensões.
- Reduza a taxa de amostragem se necessário.

---

## Conclusão
Parabéns! Você instalou e configurou com sucesso o bladeRF no WSL, atualizou o firmware e o bitstream da FPGA, e testou o dispositivo via linha de comando e Python. Agora, você está pronto para explorar as capacidades do bladeRF em seu ambiente Linux no Windows.

Dicas Adicionais:
- Documentação: Consulte a documentação oficial do [bladeRF](https://github.com/Nuand/bladeRF) e o [PySDR](https://pysdr.org/index.html) para mais informações.
- Ambientes Virtuais: Sempre use ambientes virtuais Python para gerenciar dependências.
- Atualizações: Mantenha seu sistema e pacotes atualizados.
- Comunidade: Participe de fóruns dedicados ao SDR para compartilhar experiências.

---

## Referências
- [PySDR - Using the bladeRF](https://pysdr.org/content/bladerf.html)
- [bladeRF GitHub Repository](https://github.com/Nuand/bladeRF)
- [Python bladeRF Bindings](https://github.com/Nuand/bladeRF/tree/master/host/libraries/libbladeRF_bindings/python)

  
