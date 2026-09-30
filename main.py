# -*- coding: utf-8 -*-
# =============================================================================
# Projeto: AcousticNet - Software de Camada Física para Comunicação Acústica
# Arquivo: main.py
# Descrição: Interface principal do sistema - Menu de controle e interação
# Licença: MIT License - Veja o arquivo LICENSE para detalhes
# =============================================================================

"""
Interface principal do sistema AcousticNet.

Apresenta um menu interativo que permite ao usuário:
- Transmitir mensagens via Método 1 (Batidas) ou Método 2 (FSK)
- Receber mensagens via Método 1 (Batidas) ou Método 2 (FSK)
- Testar a detecção de erros (simulação de corrupção)
- Visualizar informações sobre os métodos implementados

Este é o ponto de entrada principal do software.
"""

import sys
import os
import time
import random

from config import (
    SAMPLE_RATE, FSK_FREQ_0, FSK_FREQ_1, FSK_BIT_DURATION,
    BEAT_FREQUENCY, BIT_INTERVAL, METHOD1_FRAME_SIZE,
    Colors
)
from transmitter import AcousticTransmitter
from receiver import AcousticReceiver
from error_detection import (
    char_to_bits, build_parity_frame, verify_parity_frame,
    calculate_crc8, verify_crc_frame, bits_to_char, byte_to_bits
)


def clear_screen():
    """Limpa a tela do terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    """Exibe o banner principal do software."""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║      █████╗  ██████╗ ██████╗ ██╗   ██╗███████╗████████╗██╗ ██████╗║
    ║     ██╔══██╗██╔════╝██╔═══██╗██║   ██║██╔════╝╚══██╔══╝██║██╔════╝║
    ║     ███████║██║     ██║   ██║██║   ██║███████╗   ██║   ██║██║     ║
    ║     ██╔══██║██║     ██║   ██║██║   ██║╚════██║   ██║   ██║██║     ║
    ║     ██║  ██║╚██████╗╚██████╔╝╚██████╔╝███████║   ██║   ██║╚██████╗║
    ║     ╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝   ╚═╝   ╚═╝ ╚═════╝║
    ║                        N E T W O R K                             ║
    ║                                                                  ║
    ║        Software de Camada Física - Comunicação Acústica          ║
    ║               Redes de Computadores - UTFPR                      ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
{Colors.RESET}"""
    print(banner)


def print_menu():
    """Exibe o menu principal."""
    print(f"""
{Colors.BOLD}{Colors.WHITE}═══════════════════════ MENU PRINCIPAL ═══════════════════════{Colors.RESET}

  {Colors.GREEN}[TRANSMISSÃO]{Colors.RESET}
    {Colors.YELLOW}1{Colors.RESET} │ Transmitir mensagem - Método 1 (Batidas)
    {Colors.YELLOW}2{Colors.RESET} │ Transmitir mensagem - Método 2 (FSK)

  {Colors.BLUE}[RECEPÇÃO]{Colors.RESET}
    {Colors.YELLOW}3{Colors.RESET} │ Receber mensagem - Método 1 (Batidas)
    {Colors.YELLOW}4{Colors.RESET} │ Receber mensagem - Método 2 (FSK)

  {Colors.MAGENTA}[TESTES & INFORMAÇÕES]{Colors.RESET}
    {Colors.YELLOW}5{Colors.RESET} │ Demonstrar detecção de erros (Paridade Par)
    {Colors.YELLOW}6{Colors.RESET} │ Demonstrar detecção de erros (CRC-8)
    {Colors.YELLOW}7{Colors.RESET} │ Informações sobre os métodos

  {Colors.RED}[SISTEMA]{Colors.RESET}
    {Colors.YELLOW}0{Colors.RESET} │ Sair

{Colors.BOLD}{Colors.WHITE}═════════════════════════════════════════════════════════════{Colors.RESET}
""")


def get_message_input() -> str:
    """Solicita uma mensagem ao usuário."""
    print(f"{Colors.CYAN}Digite a mensagem para transmitir "
          f"(max 256 caracteres):{Colors.RESET}")
    message = input(f"{Colors.WHITE}>>> {Colors.RESET}").strip()

    if not message:
        print(f"{Colors.RED}Mensagem vazia. Operação cancelada.{Colors.RESET}")
        return ""

    if len(message) > 256:
        message = message[:256]
        print(f"{Colors.YELLOW}Mensagem truncada para 256 caracteres.{Colors.RESET}")

    return message


def demo_parity_error():
    """
    Demonstra o mecanismo de detecção de erros por Paridade Par.

    Mostra como a paridade funciona com dados íntegros e simula
    uma corrupção de bit para demonstrar a detecção de falha.
    """
    print(f"\n{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}"
          f" ═══ DEMONSTRAÇÃO: DETECÇÃO DE ERROS - PARIDADE PAR ═══ "
          f"{Colors.RESET}\n")

    test_chars = ['A', 'B', 'Z', '1', '!']

    # Parte 1: Transmissão sem erro
    print(f"{Colors.GREEN}{Colors.BOLD}━━━ Parte 1: Quadros ÍNTEGROS "
          f"(sem erro) ━━━{Colors.RESET}\n")

    for char in test_chars:
        data_bits = char_to_bits(char)
        frame = build_parity_frame(data_bits)
        data_recovered, ok = verify_parity_frame(frame)

        bits_str = ''.join(str(b) for b in data_bits)
        ones_count = sum(data_bits)

        print(f"  Caractere '{char}' (ASCII {ord(char):3d})")
        print(f"    Dados:     [{Colors.YELLOW}{bits_str}{Colors.RESET}]  "
              f"(nº de 1s = {ones_count}, {'par' if ones_count % 2 == 0 else 'ímpar'})")
        print(f"    Paridade:  {Colors.MAGENTA}{frame[8]}{Colors.RESET}")
        print(f"    Quadro:    [{Colors.YELLOW}"
              f"{''.join(str(b) for b in frame)}{Colors.RESET}]")
        status = (f"{Colors.GREEN}✓ SUCESSO{Colors.RESET}" if ok
                  else f"{Colors.RED}✗ FALHA{Colors.RESET}")
        print(f"    Verificação: {status}\n")

    # Parte 2: Simulação de erro
    print(f"\n{Colors.RED}{Colors.BOLD}━━━ Parte 2: Quadros CORROMPIDOS "
          f"(com erro simulado) ━━━{Colors.RESET}\n")

    for char in test_chars:
        data_bits = char_to_bits(char)
        frame = build_parity_frame(data_bits)

        # Corrompe um bit aleatório dos dados
        corrupted_frame = frame.copy()
        corrupt_pos = random.randint(0, 7)
        corrupted_frame[corrupt_pos] = 1 - corrupted_frame[corrupt_pos]

        data_recovered, ok = verify_parity_frame(corrupted_frame)
        bits_str_orig = ''.join(str(b) for b in frame[:8])
        bits_str_corr = ''.join(
            f"{Colors.RED}{b}{Colors.RESET}" if i == corrupt_pos
            else str(b)
            for i, b in enumerate(corrupted_frame[:8])
        )

        print(f"  Caractere '{char}' (corrompido no bit {corrupt_pos})")
        print(f"    Original:    [{Colors.YELLOW}{bits_str_orig}{Colors.RESET}] "
              f"paridade={frame[8]}")
        print(f"    Corrompido:  [{bits_str_corr}] "
              f"paridade={corrupted_frame[8]}")
        status = (f"{Colors.GREEN}✓ SUCESSO{Colors.RESET}" if ok
                  else f"{Colors.BG_RED}{Colors.WHITE} ✗ FALHA DE TRANSMISSÃO "
                  f"{Colors.RESET}")
        print(f"    Verificação: {status}\n")

    input(f"\n{Colors.CYAN}Pressione Enter para voltar ao menu...{Colors.RESET}")


def demo_crc_error():
    """
    Demonstra o mecanismo de detecção de erros por CRC-8.

    Mostra o cálculo do CRC para dados íntegros e demonstra a
    detecção de corrupção quando os dados são alterados.
    """
    print(f"\n{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}"
          f" ═══ DEMONSTRAÇÃO: DETECÇÃO DE ERROS - CRC-8 ═══ "
          f"{Colors.RESET}\n")

    test_messages = ["Hi", "UTFPR", "Redes", "ABC", "OK"]

    # Parte 1: Dados íntegros
    print(f"{Colors.GREEN}{Colors.BOLD}━━━ Parte 1: Dados ÍNTEGROS "
          f"(sem erro) ━━━{Colors.RESET}\n")

    for msg in test_messages:
        data = msg.encode('utf-8')
        crc = calculate_crc8(data)
        ok = verify_crc_frame(data, crc)

        hex_str = ' '.join(f'{b:02X}' for b in data)
        crc_bits = ''.join(str(b) for b in byte_to_bits(crc))

        print(f"  Mensagem: \"{msg}\"")
        print(f"    Hex:     [{Colors.YELLOW}{hex_str}{Colors.RESET}]")
        print(f"    CRC-8:   {Colors.MAGENTA}0x{crc:02X}{Colors.RESET} "
              f"({crc_bits})")
        status = (f"{Colors.GREEN}✓ SUCESSO{Colors.RESET}" if ok
                  else f"{Colors.RED}✗ FALHA{Colors.RESET}")
        print(f"    Verificação: {status}\n")

    # Parte 2: Dados corrompidos
    print(f"\n{Colors.RED}{Colors.BOLD}━━━ Parte 2: Dados CORROMPIDOS "
          f"(com erro simulado) ━━━{Colors.RESET}\n")

    for msg in test_messages:
        data = msg.encode('utf-8')
        crc_original = calculate_crc8(data)

        # Corrompe um byte aleatório
        corrupted = bytearray(data)
        corrupt_pos = random.randint(0, len(corrupted) - 1)
        corrupted[corrupt_pos] ^= random.randint(1, 255)

        ok = verify_crc_frame(bytes(corrupted), crc_original)
        crc_corrupted = calculate_crc8(bytes(corrupted))

        hex_orig = ' '.join(f'{b:02X}' for b in data)
        hex_corr = ' '.join(
            f'{Colors.RED}{b:02X}{Colors.RESET}' if i == corrupt_pos
            else f'{b:02X}'
            for i, b in enumerate(corrupted)
        )

        print(f"  Mensagem: \"{msg}\" (corrompida no byte {corrupt_pos})")
        print(f"    Original:    [{Colors.YELLOW}{hex_orig}{Colors.RESET}]")
        print(f"    Corrompido:  [{hex_corr}]")
        print(f"    CRC original:  {Colors.MAGENTA}0x{crc_original:02X}{Colors.RESET}")
        print(f"    CRC calculado: {Colors.RED}0x{crc_corrupted:02X}{Colors.RESET}")
        status = (f"{Colors.GREEN}✓ SUCESSO{Colors.RESET}" if ok
                  else f"{Colors.BG_RED}{Colors.WHITE} ✗ FALHA DE TRANSMISSÃO "
                  f"- CRC NÃO CONFERE {Colors.RESET}")
        print(f"    Verificação: {status}\n")

    input(f"\n{Colors.CYAN}Pressione Enter para voltar ao menu...{Colors.RESET}")


def show_info():
    """Exibe informações detalhadas sobre os métodos implementados."""
    clear_screen()
    print(f"""
{Colors.BOLD}{Colors.CYAN}
╔══════════════════════════════════════════════════════════════════╗
║              INFORMAÇÕES DOS MÉTODOS DE TRANSMISSÃO              ║
╚══════════════════════════════════════════════════════════════════╝
{Colors.RESET}

{Colors.GREEN}{Colors.BOLD}━━━ MÉTODO 1: BATIDAS (Impacto Sonoro) ━━━{Colors.RESET}

  {Colors.WHITE}Tipo:{Colors.RESET}        Modulação OOK (On-Off Keying) por impacto
  {Colors.WHITE}Bit 0:{Colors.RESET}       Silêncio + 1 batida + silêncio
  {Colors.WHITE}Bit 1:{Colors.RESET}       Silêncio + 2 batidas consecutivas + silêncio
  {Colors.WHITE}Frequência:{Colors.RESET}  {BEAT_FREQUENCY} Hz (pulso com harmônicas)
  {Colors.WHITE}Intervalo:{Colors.RESET}   {BIT_INTERVAL}s por bit
  {Colors.WHITE}Taxa:{Colors.RESET}        ~{1.0/BIT_INTERVAL:.1f} bps brutos
  {Colors.WHITE}Quadro:{Colors.RESET}      9 bits (8 dados + 1 paridade par)
  {Colors.WHITE}Detecção:{Colors.RESET}    Bit de Paridade Par
  {Colors.WHITE}Padrão:{Colors.RESET}      Interoperável entre equipes

{Colors.BLUE}{Colors.BOLD}━━━ MÉTODO 2: FSK (Frequency-Shift Keying) ━━━{Colors.RESET}

  {Colors.WHITE}Tipo:{Colors.RESET}        Modulação por chaveamento de frequência
  {Colors.WHITE}Bit 0:{Colors.RESET}       Tom de {FSK_FREQ_0} Hz
  {Colors.WHITE}Bit 1:{Colors.RESET}       Tom de {FSK_FREQ_1} Hz
  {Colors.WHITE}Duração:{Colors.RESET}     {FSK_BIT_DURATION}s por bit
  {Colors.WHITE}Taxa bruta:{Colors.RESET}  {1.0/FSK_BIT_DURATION:.0f} bps
  {Colors.WHITE}Preâmbulo:{Colors.RESET}   Tom de 1800 Hz (sincronização)
  {Colors.WHITE}Fim:{Colors.RESET}         Tom de 3000 Hz
  {Colors.WHITE}Detecção:{Colors.RESET}    CRC-8 (polinômio 0x07)
  {Colors.WHITE}Algoritmo:{Colors.RESET}   Goertzel (detecção de frequência)

{Colors.MAGENTA}{Colors.BOLD}━━━ DETECÇÃO DE ERROS ━━━{Colors.RESET}

  {Colors.WHITE}Método 1 - Paridade Par:{Colors.RESET}
    • Detecta todos os erros de 1 bit (e erros ímpares)
    • Não detecta erros de 2 bits (erros pares)
    • Overhead: 1 bit por quadro (11,1%)

  {Colors.WHITE}Método 2 - CRC-8:{Colors.RESET}
    • Detecta todos os erros de 1 bit
    • Detecta todos os erros de burst até 8 bits
    • Detecta 99,6% dos erros aleatórios
    • Overhead: 8 bits por mensagem

{Colors.YELLOW}{Colors.BOLD}━━━ PARÂMETROS DE ÁUDIO ━━━{Colors.RESET}

  {Colors.WHITE}Taxa de amostragem:{Colors.RESET}  {SAMPLE_RATE} Hz
  {Colors.WHITE}Canais:{Colors.RESET}              Mono (1 canal)
  {Colors.WHITE}Resolução:{Colors.RESET}           16 bits (int16)
  {Colors.WHITE}Nyquist:{Colors.RESET}             {SAMPLE_RATE//2} Hz (freq. máx)
""")
    input(f"\n{Colors.CYAN}Pressione Enter para voltar ao menu...{Colors.RESET}")


def main():
    """Função principal do programa - loop do menu interativo."""
    transmitter = AcousticTransmitter()
    receiver = AcousticReceiver()

    try:
        while True:
            clear_screen()
            print_banner()
            print_menu()

            choice = input(f"{Colors.WHITE}Escolha uma opção: {Colors.RESET}").strip()

            if choice == '1':
                # Transmitir - Método 1 (Batidas)
                message = get_message_input()
                if message:
                    transmitter.transmit_method1(message)
                    input(f"\n{Colors.CYAN}Pressione Enter para "
                          f"voltar ao menu...{Colors.RESET}")

            elif choice == '2':
                # Transmitir - Método 2 (FSK)
                message = get_message_input()
                if message:
                    transmitter.transmit_method2(message)
                    input(f"\n{Colors.CYAN}Pressione Enter para "
                          f"voltar ao menu...{Colors.RESET}")

            elif choice == '3':
                # Receber - Método 1 (Batidas)
                print(f"\n{Colors.YELLOW}Preparando recepção "
                      f"(Método 1 - Batidas)...{Colors.RESET}")
                print(f"{Colors.CYAN}Dica: O transmissor deve iniciar "
                      f"com 3 batidas rápidas.{Colors.RESET}")
                receiver.receive_method1(timeout=60.0)
                input(f"\n{Colors.CYAN}Pressione Enter para "
                      f"voltar ao menu...{Colors.RESET}")

            elif choice == '4':
                # Receber - Método 2 (FSK)
                print(f"\n{Colors.YELLOW}Preparando recepção "
                      f"(Método 2 - FSK)...{Colors.RESET}")
                receiver.receive_method2(timeout=30.0)
                input(f"\n{Colors.CYAN}Pressione Enter para "
                      f"voltar ao menu...{Colors.RESET}")

            elif choice == '5':
                # Demo - Paridade Par
                demo_parity_error()

            elif choice == '6':
                # Demo - CRC-8
                demo_crc_error()

            elif choice == '7':
                # Informações
                show_info()

            elif choice == '0':
                print(f"\n{Colors.GREEN}Encerrando AcousticNet... "
                      f"Até logo!{Colors.RESET}\n")
                break

            else:
                print(f"{Colors.RED}Opção inválida. Tente novamente.{Colors.RESET}")
                time.sleep(1)

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Programa interrompido pelo "
              f"usuário.{Colors.RESET}\n")

    finally:
        transmitter.close()
        receiver.close()


if __name__ == '__main__':
    main()
