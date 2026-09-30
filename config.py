# -*- coding: utf-8 -*-
# =============================================================================
# Projeto: AcousticNet - Software de Camada Física para Comunicação Acústica
# Arquivo: config.py
# Descrição: Configurações globais e constantes do sistema
# Licença: MIT License - Veja o arquivo LICENSE para detalhes
# =============================================================================

"""
Módulo de configurações globais para o sistema de comunicação acústica.
Define constantes de áudio, temporização e parâmetros para ambos os métodos
de transmissão (Método 1: Batidas e Método 2: FSK).
"""

# =============================================================================
# CONFIGURAÇÕES DE ÁUDIO (PyAudio)
# =============================================================================
SAMPLE_RATE = 44100          # Taxa de amostragem em Hz (padrão CD)
CHUNK_SIZE = 1024            # Tamanho do buffer de áudio (amostras por frame)
AUDIO_FORMAT_WIDTH = 2       # Largura do formato (2 bytes = 16 bits)
CHANNELS = 1                 # Número de canais (mono)

# =============================================================================
# MÉTODO 1 - BATIDAS (Transmissão por Impacto Sonoro)
# =============================================================================
# Tempos baseados no vídeo de referência (https://youtube.com/shorts/iheMxCTJW6A)
BEAT_DURATION = 0.08         # Duração de cada batida (pulso) em segundos
BEAT_SILENCE = 0.25          # Silêncio entre batidas consecutivas (bit 1)
BIT_INTERVAL = 0.7           # Intervalo total entre o início de cada bit
BEAT_FREQUENCY = 800         # Frequência do pulso de batida simulada (Hz)
BEAT_AMPLITUDE = 0.9         # Amplitude do pulso de batida (0.0 a 1.0)

# Limiares de detecção para o receptor (Método 1)
BEAT_ENERGY_THRESHOLD = 0.02  # Limiar de energia RMS para detectar uma batida
BEAT_MIN_SILENCE = 0.12      # Silêncio mínimo entre batidas (segundos)
BEAT_WINDOW_SIZE = 0.6       # Janela de tempo para agrupar batidas de um bit

# Quadro do Método 1
METHOD1_DATA_BITS = 8        # Bits de dados por quadro
METHOD1_PARITY_BITS = 1      # Bits de paridade (paridade par)
METHOD1_FRAME_SIZE = METHOD1_DATA_BITS + METHOD1_PARITY_BITS  # Total: 9 bits

# =============================================================================
# MÉTODO 2 - FSK (Frequency-Shift Keying)
# =============================================================================
FSK_FREQ_0 = 1200            # Frequência para bit 0 (Hz)
FSK_FREQ_1 = 2400            # Frequência para bit 1 (Hz)
FSK_BIT_DURATION = 0.05      # Duração de cada bit FSK (segundos) - 20 bps
FSK_AMPLITUDE = 0.8          # Amplitude do sinal FSK (0.0 a 1.0)

# Sinais de sincronização FSK
FSK_PREAMBLE_FREQ = 1800     # Frequência do preâmbulo de sincronização (Hz)
FSK_PREAMBLE_DURATION = 0.3  # Duração do preâmbulo (segundos)
FSK_END_FREQ = 3000          # Frequência do marcador de fim (Hz)
FSK_END_DURATION = 0.2       # Duração do marcador de fim (segundos)

# Limiares de detecção FSK
FSK_ENERGY_THRESHOLD = 0.01  # Limiar de energia para detecção de sinal
FSK_FREQ_TOLERANCE = 100     # Tolerância de frequência (Hz)

# Quadro do Método 2 - usa CRC-8
METHOD2_DATA_BITS = 8        # Bits de dados por byte
CRC8_POLYNOMIAL = 0x07       # Polinômio CRC-8 (x^8 + x^2 + x + 1)

# =============================================================================
# CONFIGURAÇÕES DE INTERFACE
# =============================================================================
ENCODING = 'utf-8'           # Codificação de caracteres para mensagens
MAX_MESSAGE_LENGTH = 256     # Comprimento máximo da mensagem em caracteres

# Cores ANSI para terminal
class Colors:
    """Códigos de cores ANSI para formatação do terminal."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BG_GREEN = '\033[42m'
    BG_RED = '\033[41m'
    BG_BLUE = '\033[44m'
    BG_YELLOW = '\033[43m'