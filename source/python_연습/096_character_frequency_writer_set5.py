from pathlib import Path


def count_chars(text: str) -> dict[str, int]:
    d: dict[str, int] = {}
    for ch in text:
        d[ch] = d.get(ch, 0) + 1
    return d


def build_text() -> str:
    base = ['alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta']
    words = [base[(k + 96) % len(base)] for k in range(200)]
    return ' '.join(words)


def main() -> None:
    text = build_text()
    counts = count_chars(text)
    path = Path(__file__).with_suffix('.md')
    lines = [f'practice_096', f'length={len(text)}', f'unique_chars={len(counts)}']
    for k in sorted(counts)[:25]:
        lines.append(f'{repr(k)}={counts[k]}')
    path.write_text('\n'.join(lines), encoding='utf-8')
    print('\n'.join(lines[:10]))


if __name__ == '__main__':
    main()
