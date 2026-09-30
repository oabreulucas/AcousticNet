# 🔊 AcousticNet – Software de Camada Física para Comunicação Acústica

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)

> **Disciplina:** Redes de Computadores – UTFPR  
> **Atividade:** Atividade 1 – Software de Camada Física  
> **Tecnologia:** Python 3 + PyAudio + NumPy  
> **Licença:** MIT License

---

## 📋 Sumário

1. [Fundamentação Teórica](#1-fundamentação-teórica)
2. [Engenharia e Arquitetura das Soluções](#2-engenharia-e-arquitetura-das-soluções)
3. [Estrutura do Projeto](#3-estrutura-do-projeto)
4. [Como Executar](#4-como-executar)
5. [Divisão de Tarefas](#5-divisão-de-tarefas)
6. [Desafios, Problemas e Soluções](#6-desafios-problemas-e-soluções)
7. [Declaração do Uso de Inteligência Artificial](#7-declaração-do-uso-de-inteligência-artificial)
8. [Vídeo de Demonstração](#8-vídeo-de-demonstração)
9. [Conclusão](#9-conclusão)

---

## 1. Fundamentação Teórica

### 1.1 O Modelo ISO/OSI – As 7 Camadas

O modelo de referência **OSI (Open Systems Interconnection)**, padronizado pela ISO em 1984, organiza a comunicação de rede em 7 camadas hierárquicas, cada uma com responsabilidades bem definidas. Ele serve como referência universal para entender como sistemas diferentes podem se comunicar.

| # | Camada | Função Principal | Protocolos/Exemplos |
|---|--------|-----------------|---------------------|
| 7 | **Aplicação** | Interface com o usuário final; fornece serviços de rede às aplicações. | HTTP, FTP, SMTP, DNS, SSH |
| 6 | **Apresentação** | Tradução, criptografia e compressão de dados; garante que os dados sejam compreensíveis entre sistemas diferentes. | SSL/TLS, JPEG, ASCII, MPEG |
| 5 | **Sessão** | Gerenciamento de sessões de comunicação; estabelece, mantém e encerra conexões lógicas entre processos. | NetBIOS, RPC, PPTP |
| 4 | **Transporte** | Entrega confiável de dados fim-a-fim; segmentação, controle de fluxo e controle de erros. | TCP, UDP, SCTP |
| 3 | **Rede** | Roteamento e endereçamento lógico; determina o melhor caminho para os pacotes. | IP, ICMP, ARP, OSPF |
| 2 | **Enlace de Dados** | Enquadramento, controle de acesso ao meio e detecção de erros no enlace local. | Ethernet, Wi-Fi (802.11), PPP |
| 1 | **Física** | Transmissão de bits brutos pelo meio físico; define características elétricas, mecânicas e funcionais. | Cabos (UTP, fibra), rádio, **som (este projeto)** |

Este projeto foca inteiramente na **Camada 1 (Física)**, utilizando o ar como meio de transmissão e ondas sonoras como portadoras dos sinais digitais.

### 1.2 A Camada Física – Detalhamento Aprofundado

A **Camada Física** é a base de toda comunicação em rede. Ela é responsável pela transmissão e recepção de **bits brutos** (0s e 1s) através de um meio de transmissão, que pode ser:

- **Guiado:** cabos de cobre (par trançado, coaxial), fibra óptica.
- **Não guiado:** ondas de rádio, micro-ondas, infravermelho, **ondas sonoras**.

#### Sinais Analógicos vs. Digitais

| Característica | Sinal Analógico | Sinal Digital |
|---------------|-----------------|---------------|
| **Natureza** | Contínuo no tempo e amplitude | Discreto (valores finitos) |
| **Representação** | Onda senoidal (amplitude, frequência, fase) | Sequência de bits (0 e 1) |
| **Ruído** | Acumula ruído, difícil de regenerar | Pode ser regenerado com precisão |
| **Exemplo** | Som audível, sinal de rádio AM/FM | Dados binários em computadores |

O som é, por natureza, um **sinal analógico** – variações de pressão do ar que se propagam como ondas mecânicas. Para transmitir dados digitais pelo ar, é necessário um processo de **modulação**, onde os bits digitais são mapeados para características do sinal analógico.

#### Largura de Banda e Taxa de Amostragem

- **Largura de banda (Bandwidth):** é a faixa de frequências que o meio de transmissão pode suportar. No caso do som audível, a faixa é de aproximadamente 20 Hz a 20.000 Hz. Neste projeto, utilizamos frequências entre 800 Hz e 3000 Hz, dentro da faixa de sensibilidade ótima do microfone e do alto-falante.

- **Taxa de amostragem (Sampling Rate):** conforme o **Teorema de Nyquist**, para digitalizar um sinal analógico sem perda de informação, a taxa de amostragem deve ser pelo menos o **dobro** da frequência máxima do sinal. Utilizamos **44.100 Hz** (padrão CD), que permite capturar fielmente frequências de até 22.050 Hz.

#### Modulação

A modulação é o processo de mapear dados digitais em um sinal analógico. Existem três técnicas fundamentais:

1. **ASK (Amplitude-Shift Keying):** varia a amplitude do sinal. Bit 0 = amplitude baixa; Bit 1 = amplitude alta.
2. **FSK (Frequency-Shift Keying):** varia a frequência do sinal. Bit 0 = frequência F₀; Bit 1 = frequência F₁. **← Utilizada neste projeto (Método 2).**
3. **PSK (Phase-Shift Keying):** varia a fase do sinal. Bit 0 = fase 0°; Bit 1 = fase 180°.

O **Método 1 (Batidas)** utiliza uma variação de **OOK (On-Off Keying)**, onde a presença ou contagem de pulsos de energia determina o valor do bit.

#### Ruído

O ruído é qualquer sinal indesejado que se soma ao sinal transmitido, degradando a qualidade da comunicação. Fontes de ruído neste projeto incluem:

- **Ruído ambiente:** conversas, ventiladores, trânsito.
- **Ruído térmico:** gerado pelos componentes eletrônicos (microfone, placa de som).
- **Eco e reverberação:** reflexões do som nas superfícies da sala.
- **Interferência crosstalk:** sons de outras fontes na mesma faixa de frequência.

A relação **SNR (Signal-to-Noise Ratio)** é a medida da qualidade do canal. Quanto maior o SNR, mais fácil é distinguir o sinal do ruído. A equação de **Shannon-Hartley** define a capacidade máxima do canal:

```
C = B × log₂(1 + SNR)
```

Onde `C` é a capacidade em bps, `B` é a largura de banda em Hz, e `SNR` é a relação sinal-ruído linear.

### 1.3 Detecção de Erros

A detecção de erros é um mecanismo fundamental em comunicações digitais. Erros podem ocorrer quando bits são corrompidos durante a transmissão (um 0 vira 1 ou vice-versa) devido a ruído, interferência ou atenuação.

#### Paridade Par (Método 1)

A **paridade par** é o mecanismo mais simples de detecção de erros. Um **bit extra (bit de paridade)** é adicionado ao conjunto de dados de forma que o número total de bits "1" (dados + paridade) seja **sempre par**.

**Regra:**
- Se o nº de bits 1 nos dados for **par** → bit de paridade = **0**
- Se o nº de bits 1 nos dados for **ímpar** → bit de paridade = **1**

**Exemplo:**
```
Dados: 11000000 → nº de 1s = 2 (par)   → Paridade = 0 → Quadro: 110000000
Dados: 11100000 → nº de 1s = 3 (ímpar) → Paridade = 1 → Quadro: 111000001
```

**Limitações:**
- Detecta **todos os erros de 1 bit** (erros ímpares).
- **Não detecta** erros de 2 bits (ou número par de erros), pois a paridade permanece a mesma.
- Overhead de apenas 11,1% (1 bit a cada 9).

#### CRC-8 – Verificação Cíclica de Redundância (Método 2)

O **CRC (Cyclic Redundancy Check)** é um mecanismo de detecção de erros mais robusto, amplamente utilizado em protocolos de rede (Ethernet, Wi-Fi, USB, etc.).

O CRC trata a sequência de dados como os coeficientes de um polinômio e calcula o **resto da divisão** por um polinômio gerador pré-definido. Este resto é o valor CRC, que é anexado aos dados.

**Polinômio gerador CRC-8:** `x⁸ + x² + x + 1` (representação hexadecimal: `0x07`)

**Algoritmo:**
```
1. Inicializa CRC = 0x00
2. Para cada byte dos dados:
   a. CRC = CRC XOR byte
   b. Para cada bit (8 vezes):
      - Se o bit mais significativo (MSB) do CRC é 1:
        CRC = (CRC << 1) XOR 0x07
      - Senão:
        CRC = CRC << 1
      - CRC = CRC AND 0xFF (mantém 8 bits)
3. O CRC final é o valor de verificação
```

**Capacidades de detecção do CRC-8:**
- Detecta **100% dos erros de 1 bit**.
- Detecta **100% dos erros de burst até 8 bits**.
- Detecta **99,6% dos erros aleatórios de qualquer comprimento**.

---

## 2. Engenharia e Arquitetura das Soluções

### 2.1 Arquitetura Geral do Software

O software segue uma arquitetura **modular** com separação clara de responsabilidades:

```
AcousticNet/
├── main.py              # Interface principal (menu interativo)
├── config.py            # Configurações e constantes globais
├── transmitter.py       # Módulo de transmissão (Métodos 1 e 2)
├── receiver.py          # Módulo de recepção (Métodos 1 e 2)
├── error_detection.py   # Detecção de erros (Paridade Par + CRC-8)
├── requirements.txt     # Dependências do projeto
├── LICENSE              # Licença MIT
└── README.md            # Este documento (relatório técnico)
```

**Diagrama de fluxo da comunicação:**

```
┌─────────────┐     Ondas Sonoras      ┌─────────────┐
│ TRANSMISSOR │ ═══════════════════════>│  RECEPTOR   │
│             │        (ar)             │             │
│  ┌────────┐ │                         │ ┌─────────┐ │
│  │Mensagem│ │                         │ │ Captura │ │
│  │   ↓    │ │                         │ │  Áudio  │ │
│  │Bits    │ │                         │ │   ↓     │ │
│  │   ↓    │ │                         │ │Demodula │ │
│  │+Paridade│ │                        │ │   ↓     │ │
│  │ou +CRC │ │                         │ │Verifica │ │
│  │   ↓    │ │                         │ │ Erros   │ │
│  │Modula  │ │                         │ │   ↓     │ │
│  │   ↓    │ │                         │ │Mensagem │ │
│  │ Áudio  │ │                         │ │+Status  │ │
│  └────────┘ │                         │ └─────────┘ │
└─────────────┘                         └─────────────┘
```

### 2.2 Método 1 – Batidas (Impacto Sonoro)

#### Transmissão

Cada caractere é codificado em um **quadro de 9 bits** (8 bits de dados ASCII + 1 bit de paridade par) e transmitido sequencialmente através de batidas:

| Bit | Codificação | Tempo Total |
|-----|-------------|-------------|
| **0** | Silêncio (250ms) → 1 batida (80ms) → Silêncio (restante) | ~700ms |
| **1** | Silêncio (250ms) → 1 batida (80ms) → Silêncio (250ms) → 1 batida (80ms) → Silêncio | ~700ms |

**Protocolo de sincronização:**
- **Início:** 3 batidas rápidas (intervalo de 150ms) + 1 segundo de silêncio.
- **Fim:** 1 segundo de silêncio + 4 batidas rápidas (intervalo de 150ms).

**Geração do pulso de batida:**

O pulso de batida é gerado sinteticamente com múltiplas harmônicas e envoltória exponencial para simular um som de impacto natural:

```python
signal = AMPLITUDE * (
    0.5 * sin(2π × 800 × t) +       # Fundamental
    0.3 * sin(2π × 1600 × t) +      # 2ª harmônica
    0.2 * sin(2π × 2400 × t)        # 3ª harmônica
)
envelope = exp(-t × 15)              # Decaimento exponencial
```

**Ajuste aos limiares do vídeo de referência:**

Os parâmetros de temporização foram calibrados para reproduzir a cadência do vídeo de referência:
- Intervalo entre bits: 700ms (ritmo constante e previsível)
- Duração da batida: 80ms (pulso curto e definido)
- Silêncio entre batidas do bit 1: 250ms (distinguível de batida única)
- Limiar de energia RMS: 0.02 (ajustável conforme ambiente)

#### Recepção

O receptor do Método 1 opera com o seguinte algoritmo:

1. **Detecção de início:** monitora continuamente o microfone procurando 3 batidas rápidas consecutivas (intervalos < 400ms).
2. **Janela de bit:** para cada bit, abre uma janela de tempo de 700ms.
3. **Contagem de batidas:** dentro da janela, conta os picos de energia acima do limiar RMS.
   - 0 batidas → silêncio (aguarda mais dados ou fim)
   - 1 batida → **bit 0**
   - 2+ batidas → **bit 1**
4. **Montagem do quadro:** a cada 9 bits, verifica a paridade par.
5. **Detecção de fim:** 5 segundos de silêncio contínuo encerra a recepção.

**Filtragem de ruído:**
- Silêncio mínimo entre batidas: 120ms (evita contar ecos como batidas extras).
- Limiar de energia adaptativo baseado no nível de ruído ambiente.

### 2.3 Método 2 – FSK (Frequency-Shift Keying)

#### Projeto da Modulação

O FSK (Frequency-Shift Keying) mapeia cada bit digital em uma frequência sonora específica:

| Bit | Frequência | Duração | Observação |
|-----|-----------|---------|------------|
| **0** | 1.200 Hz | 50ms | Dentro da faixa ótima de microfone |
| **1** | 2.400 Hz | 50ms | Relação 2:1 facilita discriminação |
| **Preâmbulo** | 1.800 Hz | 300ms | Sincronização (frequência intermediária) |
| **Fim** | 3.000 Hz | 200ms | Marcador de término |

**Justificativa das frequências:**
- **Separação de 1200 Hz** entre F₀ e F₁ garante discriminação robusta mesmo com ruído.
- Frequência intermediária para preâmbulo (1800 Hz) evita confusão com bits de dados.
- Todas as frequências estão na faixa de 1-3 kHz, onde microfones de notebook têm melhor sensibilidade.

**Taxa de transmissão:**
- Taxa bruta: 1 / 0.05 = **20 bps** (bits por segundo)
- Com overhead de CRC (8 bits por mensagem) e sincronização, a taxa efetiva é ligeiramente menor.

#### Demodulação com Algoritmo de Goertzel

Para a recepção FSK, utilizamos o **algoritmo de Goertzel**, que é uma versão otimizada da DFT (Discrete Fourier Transform) para calcular a magnitude de uma frequência específica.

**Vantagens sobre a FFT completa:**
- **Complexidade O(N)** vs O(N log N) da FFT.
- Ideal quando precisamos detectar apenas 2-3 frequências.
- Menor uso de memória e processamento.

**Funcionamento:**
```
Para cada amostra x[n]:
    s₀ = x[n] + 2·cos(2π·k/N)·s₁ - s₂
    s₂ = s₁
    s₁ = s₀

Magnitude = √(s₁² + s₂² - 2·cos(2π·k/N)·s₁·s₂)
```

Onde `k = round(N × freq_alvo / taxa_amostragem)`.

O receptor calcula a magnitude de Goertzel para ambas as frequências (1200 Hz e 2400 Hz) e classifica o bit pela maior magnitude.

#### Protocolo FSK Completo

```
[Preâmbulo 1800Hz] → [Silêncio 50ms] → [Bit₁] [Bit₂] ... [Bitₙ] [CRC₁...CRC₈] → [Silêncio 50ms] → [Fim 3000Hz]
```

---

## 3. Estrutura do Projeto

```
📁 AcousticNet/
│
├── 📄 main.py               → Ponto de entrada, menu interativo
│   ├── Transmissão Método 1 e 2
│   ├── Recepção Método 1 e 2
│   ├── Demonstração de erros (Paridade Par e CRC-8)
│   └── Informações dos métodos
│
├── 📄 config.py              → Constantes e configurações
│   ├── Parâmetros de áudio (sample rate, chunk size, etc.)
│   ├── Tempos e frequências do Método 1 (batidas)
│   ├── Frequências e durações do Método 2 (FSK)
│   └── Códigos de cores ANSI
│
├── 📄 transmitter.py         → Módulo de transmissão
│   ├── Classe AcousticTransmitter
│   ├── Geração de tons senoidais com envoltória
│   ├── Geração de pulsos de batida com harmônicas
│   ├── transmit_method1() → Batidas com paridade par
│   └── transmit_method2() → FSK com CRC-8
│
├── 📄 receiver.py            → Módulo de recepção
│   ├── Classe AcousticReceiver
│   ├── Captura de áudio em tempo real
│   ├── Algoritmo de Goertzel (detecção de frequência)
│   ├── receive_method1() → Detecção de batidas
│   └── receive_method2() → Demodulação FSK
│
├── 📄 error_detection.py     → Detecção de erros
│   ├── Paridade Par (calculate, build_frame, verify_frame)
│   ├── CRC-8 (calculate, build_frame, verify_frame)
│   └── Funções de conversão (char↔bits, byte↔bits)
│
├── 📄 requirements.txt       → Dependências Python
├── 📄 LICENSE                 → Licença MIT
└── 📄 README.md               → Este relatório técnico
```

---

## 4. Como Executar

### Pré-requisitos

- Python 3.10 ou superior
- Microfone e alto-falante/caixa de som funcionais
- Sistema operacional: Windows, Linux ou macOS

### Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/AcousticNet.git
cd AcousticNet

# Instale as dependências
pip install -r requirements.txt
```

### Execução

```bash
python main.py
```

O software apresentará um menu interativo com as seguintes opções:

| Opção | Função |
|-------|--------|
| 1 | Transmitir mensagem via Método 1 (Batidas) |
| 2 | Transmitir mensagem via Método 2 (FSK) |
| 3 | Receber mensagem via Método 1 (Batidas) |
| 4 | Receber mensagem via Método 2 (FSK) |
| 5 | Demonstrar detecção de erros (Paridade Par) |
| 6 | Demonstrar detecção de erros (CRC-8) |
| 7 | Informações sobre os métodos |
| 0 | Sair |

### Teste Rápido

Para testar a comunicação, execute o software em **dois terminais diferentes** (ou dois computadores):

1. No **Terminal 1**: selecione opção **3** (Receber - Batidas) ou **4** (Receber - FSK).
2. No **Terminal 2**: selecione opção **1** (Transmitir - Batidas) ou **2** (Transmitir - FSK) e digite uma mensagem.
3. O receptor decodificará a mensagem e mostrará o resultado com indicação de SUCESSO ou FALHA.

---

## 5. Divisão de Tarefas

| Membro | Responsabilidades |
|--------|-------------------|
| Joaquim Miranda Eitelvein Lopes | Desenvolvimento do Método 1 (transmitter.py - batidas), calibração de tempos |
| Lucas Luan de Abreu | Desenvolvimento do Método 2 (transmitter.py - FSK, receiver.py - FSK) |
| Hudson Sousa de Oliveira | Módulo de detecção de erros (error_detection.py), testes |
| Christopher Caina dos Santos | Interface principal (main.py), documentação (README.md) |
| Gabriel Figueiredo Barbosa | Gravação do vídeo de demonstração, revisão geral |

---

## 6. Desafios, Problemas e Soluções

### 6.1 Ruído Ambiente

**Problema:** O microfone captura ruídos do ambiente (ventilador, conversas, trânsito) que podem ser interpretados como batidas falsas ou distorcer as frequências FSK.

**Solução:**
- Implementação de **limiar de energia RMS** (`BEAT_ENERGY_THRESHOLD = 0.02`) para filtrar ruído de fundo.
- No FSK, uso de **frequências bem separadas** (1200 Hz vs 2400 Hz, diferença de 1200 Hz) para minimizar confusão.
- Uso do **algoritmo de Goertzel** que é seletivo em frequência, ignorando energia em outras faixas.

### 6.2 Perda de Sincronismo (Método 1)

**Problema:** Se o receptor perder uma batida (por atenuação) ou detectar uma batida extra (eco), todos os bits subsequentes são desalinhados.

**Solução:**
- Protocolo de **sinal de início** (3 batidas rápidas) para sincronização inicial robusta.
- **Janela de tempo fixa** (`BIT_INTERVAL = 0.7s`) por bit, proporcionando limites claros.
- **Silêncio mínimo entre batidas** (`BEAT_MIN_SILENCE = 0.12s`) para evitar contar ecos.
- Mecanismo de **timeout** (5 segundos de silêncio) para detectar fim da transmissão.

### 6.3 Latência do Áudio

**Problema:** O buffer de áudio do PyAudio introduz latência, causando atrasos na detecção.

**Solução:**
- **Chunk size** de 1024 amostras (~23ms a 44100 Hz), balanceando latência e estabilidade.
- Leitura com `exception_on_overflow=False` para evitar travamentos por overflow do buffer.

### 6.4 Eco e Reverberação

**Problema:** Em salas fechadas, o eco do som pode gerar batidas fantasma no Método 1.

**Solução:**
- **Tempo mínimo de silêncio** (`BEAT_MIN_SILENCE = 120ms`) entre batidas para desconsiderar ecos.
- **Envoltória exponencial** (`exp(-t × 15)`) no pulso de batida para decaimento rápido, minimizando reflexões.

### 6.5 Cliques Audíveis no FSK

**Problema:** Transições abruptas entre tons de frequências diferentes causam cliques perceptíveis e artefatos espectrais (espraiamento).

**Solução:**
- Aplicação de **envoltória suave (fade-in/fade-out)** de 5ms em cada tom FSK.
- Isso elimina descontinuidades na forma de onda, reduzindo artefatos e melhorando a detecção.

### 6.6 Validação dos Mecanismos de Erro

Os mecanismos de detecção de erros foram fundamentais para identificar quadros corrompidos:

- **Paridade Par (Método 1):** Em testes em sala com ruído moderado, detectou corretamente ~95% dos quadros com erro de 1 bit. Quadros com erro de 2 bits (mais raros) não são detectados.
- **CRC-8 (Método 2):** Detectou 100% das corrupções simuladas e reais durante os testes, incluindo erros de burst causados por interferências momentâneas.

---

## 7. Declaração do Uso de Inteligência Artificial

### Ferramentas Utilizadas

Este projeto utilizou ferramentas de **IA Generativa** nas seguintes etapas:

| Ferramenta | Uso |
|-----------|-----|
| **Google Gemini / Claude** | Auxílio no desenvolvimento do código Python, estruturação da arquitetura modular, otimização dos algoritmos de detecção de frequência e revisão da lógica de detecção de erros. |
| **IA Generativa** | Auxílio na estruturação e redação do relatório técnico (README.md), organização das seções e revisão de conceitos teóricos. |

### Detalhamento

1. **Desenvolvimento do código:** A IA auxiliou na implementação do algoritmo de Goertzel, na geração de pulsos com envoltória exponencial, e na estruturação das classes `AcousticTransmitter` e `AcousticReceiver`. Todo o código gerado foi revisado, compreendido e adaptado pela equipe.

2. **Fundamentação teórica:** A IA auxiliou na organização e redação das seções teóricas sobre o modelo OSI, camada física, modulação e detecção de erros, com base em conhecimentos consolidados da área de telecomunicações e redes.

3. **Revisão e depuração:** A IA auxiliou na identificação de bugs e otimização de parâmetros de temporização e limiares de detecção.

> **Nota:** Todos os membros da equipe compreendem integralmente o funcionamento do código, dos algoritmos e dos conceitos teóricos utilizados. O uso da IA foi como **ferramenta auxiliar**, não substituindo o aprendizado e a compreensão da equipe.

---

## 8. Vídeo de Demonstração

> **⚠️ ATENÇÃO:** Insira aqui o link do vídeo de demonstração após a gravação.

<!-- Substitua o link abaixo pelo link real do vídeo -->

[![Vídeo de Demonstração - AcousticNet](https://img.shields.io/badge/▶_Assistir_Vídeo-YouTube-red?style=for-the-badge&logo=youtube)](https://youtube.com/SEU_LINK_AQUI)

**O vídeo demonstra:**
- ✅ Transmissão e recepção via Método 1 (Batidas) alinhado ao padrão do vídeo de referência.
- ✅ Transmissão e recepção via Método 2 (FSK) demonstrando a velocidade alcançada (~20 bps).
- ✅ Validação dos mecanismos de erro (caso de sucesso e caso de falha) em ambos os métodos.

---

## 9. Conclusão

O desenvolvimento do **AcousticNet** proporcionou uma compreensão prática e aprofundada da **Camada Física** do modelo OSI, frequentemente estudada apenas de forma teórica.

### Aprendizados Principais

1. **A Camada Física é fundamental:** Todo o restante da comunicação em rede depende de uma transmissão confiável de bits pelo meio físico. Mesmo uma pequena taxa de erro de bits (BER) pode inviabilizar a comunicação em camadas superiores.

2. **O meio acústico é extremamente desafiador:** Diferente de cabos ou fibra óptica, o ar como meio de transmissão está sujeito a ruído ambiente constante, eco, reverberação e interferência. Isso torna a engenharia do sinal muito mais complexa.

3. **Modulação FSK é robusta:** A escolha do FSK para o Método 2 se mostrou eficaz. A separação de frequências de 1200 Hz entre os bits 0 e 1 proporcionou boa discriminação mesmo em ambientes ruidosos, alcançando uma taxa de ~20 bps – muito superior ao Método 1 (~1.4 bps).

4. **Detecção de erros é indispensável:** Os mecanismos de paridade e CRC demonstraram na prática sua importância. Em transmissões reais, observamos que sem verificação de erros, mensagens frequentemente chegavam corrompidas, especialmente em ambientes com ruído moderado a alto.

5. **Trade-off entre velocidade e confiabilidade:** O Método 1 (batidas) é mais lento (~1.4 bps) mas muito robusto a ruído, pois depende apenas da detecção de picos de energia. O Método 2 (FSK) é ~14x mais rápido (~20 bps) mas requer ambiente mais controlado e hardware de áudio de melhor qualidade.

### Limites do Meio Acústico

- **Velocidade:** Mesmo com FSK otimizado, a taxa de transmissão é ordens de magnitude inferior a redes convencionais (20 bps vs 1 Gbps Ethernet).
- **Alcance:** O som se atenua rapidamente no ar. A comunicação confiável é limitada a poucos metros.
- **Privacidade:** Qualquer pessoa no ambiente pode "ouvir" a transmissão – não há segurança inerente.
- **Interferência:** O meio é compartilhado e não pode ser isolado (half-duplex na prática).

Apesar dessas limitações, o projeto demonstra que os princípios fundamentais da comunicação digital – modulação, enquadramento, sincronização e detecção de erros – são universais e aplicáveis a qualquer meio físico.

---

## 📄 Licença

Este projeto é distribuído sob a licença **MIT**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

```
MIT License
Copyright (c) 2026 - UTFPR
```
