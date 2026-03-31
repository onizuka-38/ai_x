from pathlib import Path


def fizzbuzz_map(limit: int) -> list[str]:
    out = []
    for n in range(1, limit + 1):
        s = ''
        if n % 3 == 0:
            s += 'Fizz'
        if n % 5 == 0:
            s += 'Buzz'
        if n % 7 == 0:
            s += 'Bazz'
        out.append(s if s else str(n))
    return out


def main() -> None:
    limit = 180 + (100 % 40)
    seq = fizzbuzz_map(limit)
    p = Path(__file__).with_suffix('.out')
    p.write_text('\n'.join(seq), encoding='utf-8')
    print('practice_100')
    print('limit', limit)
    print('first30', seq[:30])
    print('last20', seq[-20:])
    print('special_count', sum(1 for x in seq if not x.isdigit()))


if __name__ == '__main__':
    main()
