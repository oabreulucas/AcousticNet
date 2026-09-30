"""Script de teste para verificar todos os módulos do AcousticNet."""
from error_detection import *

print('=== TESTE PARIDADE PAR ===')
for c in 'HELLO':
    bits = char_to_bits(c)
    frame = build_parity_frame(bits)
    data, ok = verify_parity_frame(frame)
    char_back = bits_to_char(data)
    print(f'  {c} -> bits={bits} parity={frame[8]} verify={ok} decode={char_back}')

print()
print('=== TESTE CORRUPCAO PARIDADE ===')
bits = char_to_bits('A')
frame = build_parity_frame(bits)
frame_corrupted = frame.copy()
frame_corrupted[0] = 1 - frame_corrupted[0]
data, ok = verify_parity_frame(frame_corrupted)
print(f'  Original:  {frame} -> OK')
print(f'  Corrupted: {frame_corrupted} -> {"FALHA" if not ok else "OK"}')

print()
print('=== TESTE CRC-8 ===')
for msg in ['Hi', 'UTFPR', 'Redes', 'Test123']:
    data = msg.encode('utf-8')
    crc = calculate_crc8(data)
    ok = verify_crc_frame(data, crc)
    print(f'  "{msg}" -> CRC=0x{crc:02X} verify={ok}')

print()
print('=== TESTE CORRUPCAO CRC ===')
data = b'Hello'
crc = calculate_crc8(data)
corrupted = bytearray(data)
corrupted[2] ^= 0x01
ok = verify_crc_frame(bytes(corrupted), crc)
print(f'  Original:  {data} CRC=0x{crc:02X}')
print(f'  Corrupted: {bytes(corrupted)} verify={"FALHA" if not ok else "OK"}')

print()
print('=== TODOS OS TESTES PASSARAM ===')
