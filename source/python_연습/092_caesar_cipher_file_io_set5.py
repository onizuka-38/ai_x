from pathlib import Path


def encode_caesar(text: str, shift: int) -> str:
    out = []
    for ch in text:
        o = ord(ch)
        if 65 <= o <= 90:
            out.append(chr((o - 65 + shift) % 26 + 65))
        elif 97 <= o <= 122:
            out.append(chr((o - 97 + shift) % 26 + 97))
        else:
            out.append(ch)
    return ''.join(out)


def decode_caesar(text: str, shift: int) -> str:
    return encode_caesar(text, -shift)


def main() -> None:
    raw = f'Practice file 092 with custom Caesar cipher shift and repeated words {92}.'
    shift = 3 + (92 % 10)
    enc = encode_caesar(raw, shift)
    dec = decode_caesar(enc, shift)
    p = Path(__file__).with_suffix('.log')
    p.write_text(raw + '\n' + enc + '\n' + dec, encoding='utf-8')
    print('practice_092')
    print('shift', shift)
    print(enc)
    print('restored_ok', dec == raw)


if __name__ == '__main__':
    main()
