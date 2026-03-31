from fractions import Fraction


def parse_ratio(s: str) -> Fraction:
    a, b = s.split('/')
    return Fraction(int(a), int(b))


def chain(values: list[str]) -> Fraction:
    result = Fraction(0, 1)
    for i2, v in enumerate(values, 1):
        f = parse_ratio(v)
        if i2 % 2 == 0:
            result -= f
        else:
            result += f
    return result


def main() -> None:
    vals = [f'{n + (94 % 3)}/{n + 2}' for n in range(1, 18)]
    result = chain(vals)
    print('practice_094')
    print('terms', len(vals))
    print('result', result)
    print('float', round(float(result), 8))


if __name__ == '__main__':
    main()
