# -*- coding: utf-8 -*-
# =============================================================================
# Projeto: AcousticNet - Software de Camada Física para Comunicação Acústica
# Arquivo: receiver.py
# Descrição: Módulo de recepção acústica (Método 1: Batidas, Método 2: FSK)
# Licença: MIT License - Veja o arquivo LICENSE para detalhes
# =============================================================================

"""
Módulo de recepção acústica para o sistema AcousticNet.

Implementa a demodulação e decodificação de dados para ambos os métodos:

Método 1 (Batidas):
    - Detecta impulsos de energia (batidas) no sinal capturado.
    - Classifica cada bit contando batidas em janelas de tempo.
    - Verifica integridade usando bit de paridade par.

Método 2 (FSK - Frequency-Shift Keying):
    - Detecta o preâmbulo de sincronização para início da recepção.
    - Demodula usando análise de frequência (Goertzel/FFT).
    - Verifica integridade usando CRC-8.

A captura de áudio é feita em tempo real pelo microfone do computador.
"""

import numpy as np
import pyaudio
import time
import struct

from config import (
    SAMPLE_RATE, CHUNK_SIZE, CHANNELS, AUDIO_FORMAT_WIDTH,
    BEAT_ENERGY_THRESHOLD, BEAT_MIN_SILENCE, BEAT_WINDOW_SIZE,
    BIT_INTERVAL, METHOD1_FRAME_SIZE, METHOD1_DATA_BITS,
    FSK_FREQ_0, FSK_FREQ_1, FSK_BIT_DURATION, FSK_AMPLITUDE,
    FSK_PREAMBLE_FREQ, FSK_PREAMBLE_DURATION,
    FSK_END_FREQ, FSK_ENERGY_THRESHOLD, FSK_FREQ_TOLERANCE,
    Colors
)
from error_detection import (
    verify_parity_frame, bits_to_char, bits_to_byte,
    calculate_crc8, verify_crc_frame
)


class AcousticReceiver:
    """
    Receptor acústico que decodifica sinais sonoros em dados digitais.

    Captura áudio do microfone em tempo real e aplica algoritmos de
    detecção para extrair os dados transmitidos.
    """

    def __init__(self):
        """Inicializa o receptor acústico com a interface de áudio."""
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_listening = False

    def _open_stream(self):
        """Abre o stream de entrada de áudio (microfone)."""
        self.stream = self.audio.open(
            format=self.audio.get_format_from_width(AUDIO_FORMAT_WIDTH),
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )

    def _close_stream(self):
        """Fecha o stream de áudio."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def _read_audio_chunk(self) -> np.ndarray:
        """
        Lê um chunk de amostras de áudio do microfone.

        Retorna:
            np.ndarray: Amostras normalizadas de áudio (float64, -1.0 a 1.0).
        """
        try:
            raw_data = self.stream.read(CHUNK_SIZE, exception_on_overflow=False)
            samples = np.frombuffer(raw_data, dtype=np.int16)
            return samples.astype(np.float64) / 32768.0
        except Exception:
            return np.zeros(CHUNK_SIZE, dtype=np.float64)

    def _calculate_rms(self, samples: np.ndarray) -> float:
        """
        Calcula o valor RMS (Root Mean Square) de um sinal.

        O RMS é uma medida da energia do sinal e é utilizado para
        determinar se há uma batida presente no áudio.

        Parâmetros:
            samples (np.ndarray): Amostras de áudio.

        Retorna:
            float: Valor RMS do sinal.
        """
        return np.sqrt(np.mean(samples ** 2))

    def _goertzel(self, samples: np.ndarray, target_freq: float) -> float:
        """
        Algoritmo de Goertzel para detecção eficiente de frequência específica.

        O algoritmo de Goertzel é mais eficiente que a FFT completa quando
        se deseja detectar apenas uma ou poucas frequências específicas.
        Ele calcula a magnitude da componente de Fourier em uma frequência
        alvo usando O(N) operações.

        Parâmetros:
            samples (np.ndarray): Amostras de áudio.
            target_freq (float): Frequência alvo em Hz.

        Retorna:
            float: Magnitude da componente na frequência alvo.
        """
        n = len(samples)
        k = int(0.5 + (n * target_freq) / SAMPLE_RATE)
        omega = (2.0 * np.pi * k) / n
        coeff = 2.0 * np.cos(omega)

        s0, s1, s2 = 0.0, 0.0, 0.0
        for sample in samples:
            s0 = sample + coeff * s1 - s2
            s2 = s1
            s1 = s0

        magnitude = np.sqrt(s1 * s1 + s2 * s2 - coeff * s1 * s2)
        return magnitude / n

    def _detect_frequency(self, samples: np.ndarray) -> float:
        """
        Detecta a frequência dominante em um segmento de áudio usando FFT.

        Parâmetros:
            samples (np.ndarray): Amostras de áudio.

        Retorna:
            float: Frequência dominante em Hz.
        """
        # Aplica janela de Hanning para reduzir vazamento espectral
        windowed = samples * np.hanning(len(samples))

        # Calcula FFT
        fft_result = np.fft.rfft(windowed)
        magnitudes = np.abs(fft_result)

        # Encontra o pico (ignora DC - componente 0)
        peak_index = np.argmax(magnitudes[1:]) + 1
        peak_freq = peak_index * SAMPLE_RATE / len(samples)

        return peak_freq

    # =========================================================================
    # MÉTODO 1 - RECEPÇÃO POR BATIDAS
    # =========================================================================

    def receive_method1(self, timeout: float = 60.0) -> str:
        """
        Recebe uma mensagem usando o Método 1 (detecção de batidas).

        Algoritmo de recepção:
        1. Aguarda sinal de início (3 batidas rápidas).
        2. Para cada bit, abre uma janela de tempo e conta batidas:
           - 1 batida = bit 0
           - 2 batidas = bit 1
        3. A cada 9 bits, verifica a paridade par.
        4. Aguarda sinal de fim (4 batidas rápidas) ou timeout.

        Parâmetros:
            timeout (float): Tempo máximo de espera em segundos.

        Retorna:
            str: Mensagem decodificada.
        """
        print(f"\n{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}"
              f" ═══ RECEPÇÃO - MÉTODO 1 (BATIDAS) ═══ "
              f"{Colors.RESET}")
        print(f"{Colors.YELLOW}Aguardando sinal de início "
              f"(3 batidas rápidas)...{Colors.RESET}")
        print(f"{Colors.CYAN}Timeout: {Colors.WHITE}{timeout}s{Colors.RESET}")
        print(f"{Colors.CYAN}Limiar de energia: {Colors.WHITE}"
              f"{BEAT_ENERGY_THRESHOLD}{Colors.RESET}")
        print()

        self._open_stream()
        message = ""
        frame_bits = []
        char_count = 0

        try:
            # Fase 1: Aguarda sinal de início
            if not self._wait_for_start_signal(timeout):
                print(f"{Colors.RED}✗ Timeout: nenhum sinal de início "
                      f"detectado.{Colors.RESET}")
                return ""

            print(f"{Colors.GREEN}✓ Sinal de início detectado! "
                  f"Recebendo dados...{Colors.RESET}\n")

            # Fase 2: Recepção de bits
            silence_counter = 0
            max_silence = int(5.0 * SAMPLE_RATE / CHUNK_SIZE)  # 5s de silêncio = fim

            while silence_counter < max_silence:
                # Lê janela de tempo para um bit
                bit, is_silence = self._read_bit_beats()

                if is_silence:
                    silence_counter += 1
                    continue
                else:
                    silence_counter = 0

                frame_bits.append(bit)

                # Quando completar 9 bits, processa o quadro
                if len(frame_bits) == METHOD1_FRAME_SIZE:
                    data_bits, integrity_ok = verify_parity_frame(frame_bits)
                    char = bits_to_char(data_bits)
                    char_count += 1

                    bits_str = ''.join(str(b) for b in data_bits)
                    parity_bit = frame_bits[8]

                    if integrity_ok:
                        message += char
                        print(f"  {Colors.GREEN}[SUCESSO]{Colors.RESET} "
                              f"Char #{char_count}: '{char}' "
                              f"(ASCII {ord(char):3d}) "
                              f"Dados: [{Colors.YELLOW}{bits_str}{Colors.RESET}] "
                              f"Paridade: {Colors.MAGENTA}{parity_bit}"
                              f"{Colors.RESET} ✓")
                    else:
                        message += '?'
                        print(f"  {Colors.BG_RED}{Colors.WHITE}"
                              f"[FALHA DE TRANSMISSÃO]{Colors.RESET} "
                              f"Char #{char_count}: "
                              f"Dados: [{Colors.RED}{bits_str}{Colors.RESET}] "
                              f"Paridade: {Colors.RED}{parity_bit}"
                              f"{Colors.RESET} ✗ "
                              f"{Colors.RED}(Erro de paridade detectado!)"
                              f"{Colors.RESET}")

                    frame_bits = []

            # Resultado final
            print(f"\n{Colors.BG_GREEN}{Colors.WHITE}{Colors.BOLD}"
                  f" ═══ RESULTADO DA RECEPÇÃO (MÉTODO 1) ═══ "
                  f"{Colors.RESET}")
            print(f"  {Colors.CYAN}Mensagem recebida: {Colors.WHITE}"
                  f"\"{message}\"{Colors.RESET}")
            print(f"  {Colors.CYAN}Caracteres recebidos: {Colors.WHITE}"
                  f"{char_count}{Colors.RESET}\n")

            return message

        finally:
            self._close_stream()

    def _wait_for_start_signal(self, timeout: float) -> bool:
        """
        Aguarda o sinal de início (3 batidas rápidas em sequência).

        Parâmetros:
            timeout (float): Tempo máximo de espera em segundos.

        Retorna:
            bool: True se o sinal foi detectado, False se timeout.
        """
        start_time = time.time()
        beat_count = 0
        last_beat_time = 0
        in_beat = False

        while time.time() - start_time < timeout:
            chunk = self._read_audio_chunk()
            rms = self._calculate_rms(chunk)
            current_time = time.time()

            if rms > BEAT_ENERGY_THRESHOLD * 2:
                if not in_beat:
                    in_beat = True
                    if last_beat_time > 0:
                        interval = current_time - last_beat_time
                        if interval < 0.4:  # Batidas rápidas (< 400ms)
                            beat_count += 1
                        else:
                            beat_count = 1
                    else:
                        beat_count = 1
                    last_beat_time = current_time
            else:
                in_beat = False

            if beat_count >= 3:
                time.sleep(1.0)  # Espera o silêncio pós-sinal de início
                return True

        return False

    def _read_bit_beats(self) -> tuple[int, bool]:
        """
        Lê e decodifica um bit do Método 1 (batidas).

        Analisa a janela de tempo para contar o número de batidas:
        - 1 batida → bit 0
        - 2 batidas → bit 1
        - 0 batidas → silêncio (nenhum dado)

        Retorna:
            tuple: (bit_value, is_silence)
                - bit_value: 0 ou 1
                - is_silence: True se não foram detectadas batidas
        """
        window_samples = int(BIT_INTERVAL * SAMPLE_RATE)
        chunks_needed = window_samples // CHUNK_SIZE + 1

        beat_count = 0
        in_beat = False
        samples_since_beat = 0
        min_silence_samples = int(BEAT_MIN_SILENCE * SAMPLE_RATE)

        for _ in range(chunks_needed):
            chunk = self._read_audio_chunk()
            rms = self._calculate_rms(chunk)

            if rms > BEAT_ENERGY_THRESHOLD:
                if not in_beat:
                    if samples_since_beat >= min_silence_samples or beat_count == 0:
                        beat_count += 1
                    in_beat = True
                    samples_since_beat = 0
            else:
                in_beat = False
                samples_since_beat += CHUNK_SIZE

        if beat_count == 0:
            return 0, True   # Silêncio
        elif beat_count == 1:
            return 0, False  # Bit 0
        else:
            return 1, False  # Bit 1

    # =========================================================================
    # MÉTODO 2 - RECEPÇÃO FSK (Frequency-Shift Keying)
    # =========================================================================

    def receive_method2(self, expected_bytes: int = 0,
                        timeout: float = 30.0) -> str:
        """
        Recebe uma mensagem usando o Método 2 (demodulação FSK).

        Algoritmo de recepção:
        1. Aguarda detecção do preâmbulo de sincronização (1800 Hz).
        2. Lê segmentos de FSK_BIT_DURATION e classifica pela frequência:
           - Freq ~1200 Hz → bit 0
           - Freq ~2400 Hz → bit 1
        3. Detecta marcador de fim (3000 Hz) ou coleta expected_bytes + CRC.
        4. Verifica integridade com CRC-8.

        Parâmetros:
            expected_bytes (int): Número de bytes esperados (0 = auto-detectar).
            timeout (float): Tempo máximo de espera em segundos.

        Retorna:
            str: Mensagem decodificada.
        """
        print(f"\n{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}"
              f" ═══ RECEPÇÃO - MÉTODO 2 (FSK) ═══ "
              f"{Colors.RESET}")
        print(f"{Colors.YELLOW}Aguardando preâmbulo de sincronização "
              f"({FSK_PREAMBLE_FREQ} Hz)...{Colors.RESET}")
        print(f"{Colors.CYAN}Frequências: {Colors.WHITE}"
              f"Bit 0 = {FSK_FREQ_0} Hz | Bit 1 = {FSK_FREQ_1} Hz{Colors.RESET}")
        print(f"{Colors.CYAN}Timeout: {Colors.WHITE}{timeout}s{Colors.RESET}")
        print()

        self._open_stream()

        try:
            # Fase 1: Detecta preâmbulo
            if not self._wait_for_preamble(timeout):
                print(f"{Colors.RED}✗ Timeout: preâmbulo não detectado."
                      f"{Colors.RESET}")
                return ""

            print(f"{Colors.GREEN}✓ Preâmbulo detectado! "
                  f"Demodulando FSK...{Colors.RESET}\n")

            # Pequena pausa para transição preâmbulo → dados
            time.sleep(0.05)

            # Fase 2: Demodulação FSK
            all_bits = []
            bit_samples = int(FSK_BIT_DURATION * SAMPLE_RATE)
            consecutive_end = 0

            while True:
                # Lê amostras para um bit
                raw_data = self.stream.read(bit_samples,
                                            exception_on_overflow=False)
                samples = np.frombuffer(raw_data, dtype=np.int16)
                samples_float = samples.astype(np.float64) / 32768.0

                rms = self._calculate_rms(samples_float)

                if rms < FSK_ENERGY_THRESHOLD:
                    consecutive_end += 1
                    if consecutive_end > 3:
                        break
                    continue

                # Detecta frequência usando Goertzel
                mag_0 = self._goertzel(samples_float, FSK_FREQ_0)
                mag_1 = self._goertzel(samples_float, FSK_FREQ_1)
                mag_end = self._goertzel(samples_float, FSK_END_FREQ)

                # Verifica marcador de fim
                if mag_end > mag_0 and mag_end > mag_1:
                    consecutive_end += 1
                    if consecutive_end > 2:
                        break
                    continue
                else:
                    consecutive_end = 0

                # Classifica bit
                bit = 0 if mag_0 > mag_1 else 1
                all_bits.append(bit)

            # Fase 3: Decodificação
            if len(all_bits) < 16:  # Mínimo: 8 dados + 8 CRC
                print(f"{Colors.RED}✗ Dados insuficientes: "
                      f"apenas {len(all_bits)} bits recebidos.{Colors.RESET}")
                return ""

            # Separa dados e CRC (últimos 8 bits = CRC)
            data_bits = all_bits[:-8]
            crc_bits = all_bits[-8:]

            # Converte bits em bytes
            data_bytes = bytearray()
            for i in range(0, len(data_bits), 8):
                if i + 8 <= len(data_bits):
                    byte_val = bits_to_byte(data_bits[i:i+8])
                    data_bytes.append(byte_val)

            received_crc = bits_to_byte(crc_bits)

            # Verifica CRC
            integrity_ok = verify_crc_frame(bytes(data_bytes), received_crc)

            # Decodifica mensagem
            try:
                message = data_bytes.decode('utf-8')
            except UnicodeDecodeError:
                message = data_bytes.decode('latin-1')

            expected_crc = calculate_crc8(bytes(data_bytes))

            # Exibe resultado byte a byte
            for i, byte_val in enumerate(data_bytes):
                char_repr = chr(byte_val) if 32 <= byte_val < 127 else '?'
                byte_bits = data_bits[i*8:(i+1)*8]
                bits_str = ''.join(str(b) for b in byte_bits)
                print(f"  {Colors.GREEN}Byte {i+1}/{len(data_bytes)}: "
                      f"'{char_repr}'{Colors.RESET} "
                      f"(0x{byte_val:02X}) ← "
                      f"[{Colors.YELLOW}{bits_str}{Colors.RESET}]")

            crc_str = ''.join(str(b) for b in crc_bits)
            print(f"\n  {Colors.MAGENTA}CRC-8 recebido:  0x{received_crc:02X} "
                  f"({crc_str}){Colors.RESET}")
            print(f"  {Colors.MAGENTA}CRC-8 calculado: 0x{expected_crc:02X}"
                  f"{Colors.RESET}")

            # Resultado final
            if integrity_ok:
                print(f"\n{Colors.BG_GREEN}{Colors.WHITE}{Colors.BOLD}"
                      f" ✓ SUCESSO - DADOS ÍNTEGROS (CRC-8 VÁLIDO) "
                      f"{Colors.RESET}")
            else:
                print(f"\n{Colors.BG_RED}{Colors.WHITE}{Colors.BOLD}"
                      f" ✗ FALHA DE TRANSMISSÃO - CRC-8 INVÁLIDO "
                      f"{Colors.RESET}")
                print(f"  {Colors.RED}Erro detectado: dados podem estar "
                      f"corrompidos!{Colors.RESET}")

            print(f"  {Colors.CYAN}Mensagem: {Colors.WHITE}\"{message}\""
                  f"{Colors.RESET}")
            print(f"  {Colors.CYAN}Total de bits: {Colors.WHITE}"
                  f"{len(all_bits)}{Colors.RESET}")
            print(f"  {Colors.CYAN}Bytes de dados: {Colors.WHITE}"
                  f"{len(data_bytes)}{Colors.RESET}\n")

            return message

        finally:
            self._close_stream()

    def _wait_for_preamble(self, timeout: float) -> bool:
        """
        Aguarda a detecção do preâmbulo de sincronização FSK.

        Usa o algoritmo de Goertzel para detectar a frequência do preâmbulo
        (1800 Hz) no áudio capturado.

        Parâmetros:
            timeout (float): Tempo máximo de espera em segundos.

        Retorna:
            bool: True se o preâmbulo foi detectado, False se timeout.
        """
        start_time = time.time()
        preamble_detect_count = 0
        required_detections = 3  # Requer múltiplas detecções consecutivas

        while time.time() - start_time < timeout:
            chunk = self._read_audio_chunk()
            rms = self._calculate_rms(chunk)

            if rms > FSK_ENERGY_THRESHOLD:
                mag_preamble = self._goertzel(chunk, FSK_PREAMBLE_FREQ)
                mag_0 = self._goertzel(chunk, FSK_FREQ_0)
                mag_1 = self._goertzel(chunk, FSK_FREQ_1)

                if (mag_preamble > mag_0 and
                    mag_preamble > mag_1 and
                    mag_preamble > FSK_ENERGY_THRESHOLD):
                    preamble_detect_count += 1
                else:
                    preamble_detect_count = 0
            else:
                preamble_detect_count = 0

            if preamble_detect_count >= required_detections:
                return True

        return False

    def close(self):
        """Libera os recursos de áudio."""
        self._close_stream()
        self.audio.terminate()
