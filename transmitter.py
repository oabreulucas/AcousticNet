# -*- coding: utf-8 -*-
# =============================================================================
# Projeto: AcousticNet - Software de Camada Física para Comunicação Acústica
# Arquivo: transmitter.py
# Descrição: Módulo de transmissão acústica (Método 1: Batidas, Método 2: FSK)
# Licença: MIT License - Veja o arquivo LICENSE para detalhes
# =============================================================================

"""
Módulo de transmissão acústica para o sistema AcousticNet.

Implementa dois métodos de modulação para envio de dados via áudio:

Método 1 (Batidas):
    - Cada bit é representado por batidas sonoras (impulsos de energia).
    - Bit 0: silêncio + 1 batida + silêncio
    - Bit 1: silêncio + 2 batidas consecutivas + silêncio
    - Cadência padronizada conforme vídeo de referência.

Método 2 (FSK - Frequency-Shift Keying):
    - Modulação por chaveamento de frequência.
    - Bit 0: tom de 1200 Hz
    - Bit 1: tom de 2400 Hz
    - Inclui preâmbulo de sincronização e marcador de fim.
    - Taxa de transmissão: ~20 bps (ajustável).
"""

import numpy as np
import pyaudio
import time

from config import (
    SAMPLE_RATE, CHANNELS, AUDIO_FORMAT_WIDTH,
    BEAT_DURATION, BEAT_SILENCE, BIT_INTERVAL,
    BEAT_FREQUENCY, BEAT_AMPLITUDE,
    FSK_FREQ_0, FSK_FREQ_1, FSK_BIT_DURATION, FSK_AMPLITUDE,
    FSK_PREAMBLE_FREQ, FSK_PREAMBLE_DURATION,
    FSK_END_FREQ, FSK_END_DURATION,
    Colors
)
from error_detection import (
    char_to_bits, build_parity_frame,
    calculate_crc8, byte_to_bits
)


class AcousticTransmitter:
    """
    Transmissor acústico que converte dados digitais em sinais sonoros.

    Suporta dois métodos de modulação:
    - Método 1: Batidas (impacto sonoro) com paridade par
    - Método 2: FSK (Frequency-Shift Keying) com CRC-8
    """

    def __init__(self):
        """Inicializa o transmissor acústico com a interface de áudio."""
        self.audio = pyaudio.PyAudio()
        self.stream = None

    def _open_stream(self):
        """Abre o stream de saída de áudio."""
        self.stream = self.audio.open(
            format=self.audio.get_format_from_width(AUDIO_FORMAT_WIDTH),
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            output=True
        )

    def _close_stream(self):
        """Fecha o stream de áudio."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def _generate_tone(self, frequency: float, duration: float,
                       amplitude: float = 0.8) -> np.ndarray:
        """
        Gera um tom senoidal com envoltória suave (fade-in/fade-out).

        A envoltória evita cliques audíveis no início e fim do sinal,
        que seriam causados por descontinuidades na forma de onda.

        Parâmetros:
            frequency (float): Frequência do tom em Hz.
            duration (float): Duração do tom em segundos.
            amplitude (float): Amplitude do sinal (0.0 a 1.0).

        Retorna:
            np.ndarray: Amostras do tom em formato int16.
        """
        n_samples = int(SAMPLE_RATE * duration)
        t = np.linspace(0, duration, n_samples, endpoint=False)

        # Gera a onda senoidal
        signal = amplitude * np.sin(2 * np.pi * frequency * t)

        # Aplica envoltória suave (fade-in e fade-out de 5ms)
        fade_samples = min(int(SAMPLE_RATE * 0.005), n_samples // 4)
        if fade_samples > 0:
            fade_in = np.linspace(0, 1, fade_samples)
            fade_out = np.linspace(1, 0, fade_samples)
            signal[:fade_samples] *= fade_in
            signal[-fade_samples:] *= fade_out

        return (signal * 32767).astype(np.int16)

    def _generate_silence(self, duration: float) -> np.ndarray:
        """
        Gera um período de silêncio.

        Parâmetros:
            duration (float): Duração do silêncio em segundos.

        Retorna:
            np.ndarray: Amostras de silêncio (zeros) em formato int16.
        """
        n_samples = int(SAMPLE_RATE * duration)
        return np.zeros(n_samples, dtype=np.int16)

    def _generate_beat(self) -> np.ndarray:
        """
        Gera um pulso de batida (impulso sonoro curto e intenso).

        O pulso simula o som de uma batida em superfície, com ataque
        rápido e decaimento natural (envoltória exponencial).

        Retorna:
            np.ndarray: Amostras do pulso de batida em formato int16.
        """
        n_samples = int(SAMPLE_RATE * BEAT_DURATION)
        t = np.linspace(0, BEAT_DURATION, n_samples, endpoint=False)

        # Gera o impulso com múltiplas harmônicas para simular batida
        signal = BEAT_AMPLITUDE * (
            0.5 * np.sin(2 * np.pi * BEAT_FREQUENCY * t) +
            0.3 * np.sin(2 * np.pi * BEAT_FREQUENCY * 2 * t) +
            0.2 * np.sin(2 * np.pi * BEAT_FREQUENCY * 3 * t)
        )

        # Envoltória exponencial decrescente (ataque rápido, decaimento natural)
        envelope = np.exp(-t * 15)
        signal *= envelope

        return (signal * 32767).astype(np.int16)

    def _play_audio(self, samples: np.ndarray):
        """
        Reproduz amostras de áudio pelo stream de saída.

        Parâmetros:
            samples (np.ndarray): Amostras de áudio em formato int16.
        """
        self.stream.write(samples.tobytes())

    # =========================================================================
    # MÉTODO 1 - TRANSMISSÃO POR BATIDAS
    # =========================================================================

    def _transmit_bit_beats(self, bit: int):
        """
        Transmite um único bit usando o método de batidas.

        - Bit 0: silêncio + 1 batida + silêncio
        - Bit 1: silêncio + 2 batidas consecutivas + silêncio

        Parâmetros:
            bit (int): O bit a ser transmitido (0 ou 1).
        """
        beat = self._generate_beat()
        pre_silence = self._generate_silence(BEAT_SILENCE)

        if bit == 0:
            # Bit 0: silêncio + 1 batida + silêncio
            self._play_audio(pre_silence)
            self._play_audio(beat)
            post_silence_duration = BIT_INTERVAL - BEAT_SILENCE - BEAT_DURATION
            if post_silence_duration > 0:
                self._play_audio(self._generate_silence(post_silence_duration))
        else:
            # Bit 1: silêncio + 2 batidas + silêncio
            self._play_audio(pre_silence)
            self._play_audio(beat)
            inter_beat_silence = self._generate_silence(BEAT_SILENCE)
            self._play_audio(inter_beat_silence)
            self._play_audio(beat)
            post_silence_duration = (BIT_INTERVAL - BEAT_SILENCE -
                                     BEAT_DURATION - BEAT_SILENCE - BEAT_DURATION)
            if post_silence_duration > 0:
                self._play_audio(self._generate_silence(post_silence_duration))

    def transmit_method1(self, message: str):
        """
        Transmite uma mensagem usando o Método 1 (Batidas) com paridade par.

        Cada caractere é convertido em um quadro de 9 bits (8 dados + 1 paridade)
        e transmitido sequencialmente via batidas sonoras.

        Parâmetros:
            message (str): Mensagem a ser transmitida.
        """
        print(f"\n{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}"
              f" ═══ TRANSMISSÃO - MÉTODO 1 (BATIDAS) ═══ "
              f"{Colors.RESET}")
        print(f"{Colors.CYAN}Mensagem: {Colors.WHITE}\"{message}\"{Colors.RESET}")
        print(f"{Colors.CYAN}Caracteres: {Colors.WHITE}{len(message)}{Colors.RESET}")
        print(f"{Colors.CYAN}Bits por quadro: {Colors.WHITE}9 (8 dados + 1 paridade par)"
              f"{Colors.RESET}")
        print(f"{Colors.CYAN}Total de bits: {Colors.WHITE}"
              f"{len(message) * 9}{Colors.RESET}")
        print()

        self._open_stream()

        try:
            # Sinal de início: 3 batidas rápidas para sincronização
            print(f"{Colors.YELLOW}▶ Enviando sinal de início...{Colors.RESET}")
            for _ in range(3):
                self._play_audio(self._generate_beat())
                self._play_audio(self._generate_silence(0.15))
            self._play_audio(self._generate_silence(1.0))

            for i, char in enumerate(message):
                data_bits = char_to_bits(char)
                frame = build_parity_frame(data_bits)

                bits_str = ''.join(str(b) for b in data_bits)
                print(f"  {Colors.GREEN}Char '{char}'{Colors.RESET} "
                      f"(ASCII {ord(char):3d}) → "
                      f"Dados: [{Colors.YELLOW}{bits_str}{Colors.RESET}] "
                      f"Paridade: {Colors.MAGENTA}{frame[8]}{Colors.RESET}")

                # Transmite cada bit do quadro (9 bits)
                for bit in frame:
                    self._transmit_bit_beats(bit)

                # Pausa entre caracteres
                self._play_audio(self._generate_silence(0.5))

            # Sinal de fim: 4 batidas rápidas
            print(f"\n{Colors.YELLOW}▶ Enviando sinal de fim...{Colors.RESET}")
            self._play_audio(self._generate_silence(1.0))
            for _ in range(4):
                self._play_audio(self._generate_beat())
                self._play_audio(self._generate_silence(0.15))

            print(f"\n{Colors.BG_GREEN}{Colors.WHITE}{Colors.BOLD}"
                  f" ✓ TRANSMISSÃO MÉTODO 1 CONCLUÍDA COM SUCESSO "
                  f"{Colors.RESET}\n")

        finally:
            self._close_stream()

    # =========================================================================
    # MÉTODO 2 - TRANSMISSÃO FSK (Frequency-Shift Keying)
    # =========================================================================

    def _transmit_bit_fsk(self, bit: int):
        """
        Transmite um único bit usando modulação FSK.

        - Bit 0: tom de 1200 Hz durante FSK_BIT_DURATION
        - Bit 1: tom de 2400 Hz durante FSK_BIT_DURATION

        Parâmetros:
            bit (int): O bit a ser transmitido (0 ou 1).
        """
        freq = FSK_FREQ_0 if bit == 0 else FSK_FREQ_1
        tone = self._generate_tone(freq, FSK_BIT_DURATION, FSK_AMPLITUDE)
        self._play_audio(tone)

    def transmit_method2(self, message: str):
        """
        Transmite uma mensagem usando o Método 2 (FSK) com CRC-8.

        Estrutura da transmissão:
        1. Preâmbulo de sincronização (tom de 1800 Hz)
        2. Para cada byte: 8 bits FSK + 8 bits CRC-8
        3. Marcador de fim (tom de 3000 Hz)

        A taxa teórica de transmissão é de 1/FSK_BIT_DURATION bps para os
        bits brutos, mas a taxa efetiva é menor devido ao overhead do CRC
        e da sincronização.

        Parâmetros:
            message (str): Mensagem a ser transmitida.
        """
        data_bytes = message.encode('utf-8')
        crc = calculate_crc8(data_bytes)
        crc_bits = byte_to_bits(crc)

        # Calcula taxas de transmissão
        total_bits = len(data_bytes) * 8 + 8  # dados + CRC
        raw_bps = 1.0 / FSK_BIT_DURATION
        total_time = (FSK_PREAMBLE_DURATION + total_bits * FSK_BIT_DURATION +
                      FSK_END_DURATION)
        effective_bps = (len(data_bytes) * 8) / total_time

        print(f"\n{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}"
              f" ═══ TRANSMISSÃO - MÉTODO 2 (FSK) ═══ "
              f"{Colors.RESET}")
        print(f"{Colors.CYAN}Mensagem: {Colors.WHITE}\"{message}\"{Colors.RESET}")
        print(f"{Colors.CYAN}Bytes de dados: {Colors.WHITE}{len(data_bytes)}{Colors.RESET}")
        print(f"{Colors.CYAN}CRC-8: {Colors.WHITE}0x{crc:02X} "
              f"({''.join(str(b) for b in crc_bits)}){Colors.RESET}")
        print(f"{Colors.CYAN}Frequências: {Colors.WHITE}"
              f"Bit 0 = {FSK_FREQ_0} Hz | Bit 1 = {FSK_FREQ_1} Hz{Colors.RESET}")
        print(f"{Colors.CYAN}Taxa bruta: {Colors.WHITE}{raw_bps:.1f} bps{Colors.RESET}")
        print(f"{Colors.CYAN}Taxa efetiva: {Colors.WHITE}"
              f"{effective_bps:.1f} bps{Colors.RESET}")
        print(f"{Colors.CYAN}Tempo estimado: {Colors.WHITE}"
              f"{total_time:.2f}s{Colors.RESET}")
        print()

        self._open_stream()

        try:
            # 1. Preâmbulo de sincronização
            print(f"  {Colors.YELLOW}▶ Preâmbulo de sincronização "
                  f"({FSK_PREAMBLE_FREQ} Hz, {FSK_PREAMBLE_DURATION}s)..."
                  f"{Colors.RESET}")
            preamble = self._generate_tone(FSK_PREAMBLE_FREQ,
                                           FSK_PREAMBLE_DURATION, FSK_AMPLITUDE)
            self._play_audio(preamble)
            self._play_audio(self._generate_silence(0.05))

            # 2. Transmite dados byte a byte
            for i, byte_val in enumerate(data_bytes):
                bits = byte_to_bits(byte_val)
                char_repr = chr(byte_val) if 32 <= byte_val < 127 else '?'
                bits_str = ''.join(str(b) for b in bits)

                print(f"  {Colors.GREEN}Byte {i+1}/{len(data_bytes)}: "
                      f"'{char_repr}'{Colors.RESET} "
                      f"(0x{byte_val:02X}) → "
                      f"[{Colors.YELLOW}{bits_str}{Colors.RESET}]")

                for bit in bits:
                    self._transmit_bit_fsk(bit)

            # 3. Transmite CRC-8
            print(f"  {Colors.MAGENTA}▶ CRC-8: "
                  f"{''.join(str(b) for b in crc_bits)} "
                  f"(0x{crc:02X}){Colors.RESET}")
            for bit in crc_bits:
                self._transmit_bit_fsk(bit)

            # 4. Marcador de fim
            self._play_audio(self._generate_silence(0.05))
            end_marker = self._generate_tone(FSK_END_FREQ,
                                             FSK_END_DURATION, FSK_AMPLITUDE)
            self._play_audio(end_marker)

            print(f"\n{Colors.BG_GREEN}{Colors.WHITE}{Colors.BOLD}"
                  f" ✓ TRANSMISSÃO MÉTODO 2 (FSK) CONCLUÍDA COM SUCESSO "
                  f"{Colors.RESET}")
            print(f"  {Colors.CYAN}Tempo total: {Colors.WHITE}"
                  f"{total_time:.2f}s{Colors.RESET}\n")

        finally:
            self._close_stream()

    def close(self):
        """Libera os recursos de áudio."""
        self._close_stream()
        self.audio.terminate()
