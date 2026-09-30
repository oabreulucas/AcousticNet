# -*- coding: utf-8 -*-
# =============================================================================
# Projeto: AcousticNet - Software de Camada Física para Comunicação Acústica
# Arquivo: error_detection.py
# Descrição: Módulo de detecção e verificação de erros (Paridade Par + CRC-8)
# Licença: MIT License - Veja o arquivo LICENSE para detalhes
# =============================================================================

"""
Módulo de detecção de erros para o sistema de comunicação acústica.

Implementa dois mecanismos de verificação de integridade:
- Paridade Par (Método 1): bit extra para garantir número par de 1s no quadro.
- CRC-8 (Método 2): verificação cíclica de redundância para detecção robusta.

A detecção de erros é essencial na camada física pois o meio de transmissão
acústico está sujeito a ruído ambiente, atenuação e interferências que podem
corromper os bits transmitidos.
"""

from config import CRC8_POLYNOMIAL


# =============================================================================
# PARIDADE PAR (Método 1 - Obrigatório)
# =============================================================================

def calculate_even_parity(data_bits: list[int]) -> int:
    """
    Calcula o bit de paridade par para um conjunto de bits de dados.

    Na paridade par, o bit de paridade é definido de forma que o número total
    de bits '1' (dados + paridade) seja sempre par.

    Parâmetros:
        data_bits (list[int]): Lista de 8 bits de dados (0 ou 1).

    Retorna:
        int: Bit de paridade (0 se nº de 1s for par, 1 se for ímpar).

    Exemplos:
        >>> calculate_even_parity([1, 1, 0, 0, 0, 0, 0, 0])
        0
        >>> calculate_even_parity([1, 1, 1, 0, 0, 0, 0, 0])
        1
    """
    count_ones = sum(data_bits)
    return 0 if count_ones % 2 == 0 else 1


def build_parity_frame(data_bits: list[int]) -> list[int]:
    """
    Constrói um quadro de 9 bits: 8 bits de dados + 1 bit de paridade par.

    Parâmetros:
        data_bits (list[int]): Lista de 8 bits de dados.

    Retorna:
        list[int]: Lista de 9 bits (dados + paridade).

    Exemplo:
        >>> build_parity_frame([0, 1, 0, 0, 0, 0, 0, 1])  # 'A' = 0x41
        [0, 1, 0, 0, 0, 0, 0, 1, 0]  # 2 bits '1' -> paridade = 0
    """
    if len(data_bits) != 8:
        raise ValueError(f"Esperados 8 bits de dados, recebidos {len(data_bits)}")

    parity = calculate_even_parity(data_bits)
    return data_bits + [parity]


def verify_parity_frame(frame_bits: list[int]) -> tuple[list[int], bool]:
    """
    Verifica a integridade de um quadro de 9 bits usando paridade par.

    Extrai os 8 bits de dados, recalcula a paridade esperada e compara
    com o 9º bit recebido.

    Parâmetros:
        frame_bits (list[int]): Lista de 9 bits recebidos (dados + paridade).

    Retorna:
        tuple: (dados: list[int], integridade_ok: bool)
            - dados: os 8 bits de dados extraídos
            - integridade_ok: True se a paridade bater, False caso contrário

    Exemplo:
        >>> verify_parity_frame([0, 1, 0, 0, 0, 0, 0, 1, 0])
        ([0, 1, 0, 0, 0, 0, 0, 1], True)
    """
    if len(frame_bits) != 9:
        raise ValueError(f"Esperados 9 bits no quadro, recebidos {len(frame_bits)}")

    data_bits = frame_bits[:8]
    received_parity = frame_bits[8]
    expected_parity = calculate_even_parity(data_bits)

    integrity_ok = (received_parity == expected_parity)
    return data_bits, integrity_ok


# =============================================================================
# CRC-8 (Método 2 - Verificação Cíclica de Redundância)
# =============================================================================

def calculate_crc8(data_bytes: bytes) -> int:
    """
    Calcula o CRC-8 de uma sequência de bytes.

    O CRC (Cyclic Redundancy Check) é um algoritmo de detecção de erros que
    trata os dados como um polinômio e calcula o resto da divisão por um
    polinômio gerador. O CRC-8 utiliza o polinômio x^8 + x^2 + x + 1
    (0x07), capaz de detectar todos os erros de 1 bit, todos os erros de
    burst até 8 bits e a maioria dos erros de múltiplos bits.

    Parâmetros:
        data_bytes (bytes): Dados para calcular o CRC.

    Retorna:
        int: Valor CRC-8 (0 a 255).

    Exemplo:
        >>> calculate_crc8(b'A')
        211
    """
    crc = 0x00  # Valor inicial

    for byte in data_bytes:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ CRC8_POLYNOMIAL) & 0xFF
            else:
                crc = (crc << 1) & 0xFF

    return crc


def build_crc_frame(data_bytes: bytes) -> tuple[bytes, int]:
    """
    Constrói um quadro com dados + CRC-8 para o Método 2.

    Parâmetros:
        data_bytes (bytes): Dados originais a serem protegidos.

    Retorna:
        tuple: (dados_originais, crc_calculado)
    """
    crc = calculate_crc8(data_bytes)
    return data_bytes, crc


def verify_crc_frame(data_bytes: bytes, received_crc: int) -> bool:
    """
    Verifica a integridade dos dados recebidos comparando o CRC recebido
    com o CRC recalculado.

    Parâmetros:
        data_bytes (bytes): Dados recebidos.
        received_crc (int): CRC-8 recebido junto com os dados.

    Retorna:
        bool: True se os dados estão íntegros, False se houve corrupção.
    """
    expected_crc = calculate_crc8(data_bytes)
    return expected_crc == received_crc


# =============================================================================
# FUNÇÕES UTILITÁRIAS DE CONVERSÃO
# =============================================================================

def char_to_bits(char: str) -> list[int]:
    """
    Converte um caractere para uma lista de 8 bits (MSB primeiro).

    Parâmetros:
        char (str): Um único caractere.

    Retorna:
        list[int]: Lista de 8 bits representando o valor ASCII/UTF-8.

    Exemplo:
        >>> char_to_bits('A')  # ASCII 65 = 01000001
        [0, 1, 0, 0, 0, 0, 0, 1]
    """
    byte_val = ord(char) & 0xFF
    return [(byte_val >> (7 - i)) & 1 for i in range(8)]


def bits_to_char(bits: list[int]) -> str:
    """
    Converte uma lista de 8 bits para um caractere.

    Parâmetros:
        bits (list[int]): Lista de 8 bits (MSB primeiro).

    Retorna:
        str: O caractere correspondente.

    Exemplo:
        >>> bits_to_char([0, 1, 0, 0, 0, 0, 0, 1])
        'A'
    """
    byte_val = 0
    for bit in bits:
        byte_val = (byte_val << 1) | bit
    return chr(byte_val)


def byte_to_bits(byte_val: int) -> list[int]:
    """
    Converte um valor de byte (0-255) para lista de 8 bits.

    Parâmetros:
        byte_val (int): Valor do byte (0 a 255).

    Retorna:
        list[int]: Lista de 8 bits (MSB primeiro).
    """
    return [(byte_val >> (7 - i)) & 1 for i in range(8)]


def bits_to_byte(bits: list[int]) -> int:
    """
    Converte uma lista de 8 bits para valor inteiro (byte).

    Parâmetros:
        bits (list[int]): Lista de 8 bits (MSB primeiro).

    Retorna:
        int: Valor do byte (0 a 255).
    """
    value = 0
    for bit in bits:
        value = (value << 1) | bit
    return value
