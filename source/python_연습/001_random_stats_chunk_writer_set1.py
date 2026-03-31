from pathlib import Path
import random


def make_sequence(n: int) -> list[int]:
    random.seed(1)
    return [random.randint(10, 999) for _ in range(n)]


def stats(values: list[int]) -> dict[str, float]:
    total = sum(values)
    avg = total / len(values)
    return {
        'min': min(values),
        'max': max(values),
        'sum': total,
        'avg': round(avg, 3),
        'spread': max(values) - min(values),
    }


def chunk(values: list[int], size: int) -> list[list[int]]:
    return [values[j:j+size] for j in range(0, len(values), size)]


def main() -> None:
    values = make_sequence(48)
    s = stats(values)
    rows = chunk(values, 8)
    out = Path(__file__).with_suffix('.txt')
    lines = [
        f'file=practice_001.py',
        f'count={len(values)}',
        f'min={s["min"]}',
        f'max={s["max"]}',
        f'sum={s["sum"]}',
        f'avg={s["avg"]}',
        f'spread={s["spread"]}',
    ]
    for r in rows:
        lines.append(' '.join(f'{v:03d}' for v in r))
    out.write_text('\n'.join(lines), encoding='utf-8')
    print('\n'.join(lines[:7]))


if __name__ == '__main__':
    main()
