from typing import Iterable


def moving_average(values: Iterable[float], window: int) -> list[float]:
    vals = list(values)
    if window <= 0 or window > len(vals):
        return []
    out: list[float] = []
    s = sum(vals[:window])
    out.append(round(s / window, 4))
    for n in range(window, len(vals)):
        s += vals[n] - vals[n - window]
        out.append(round(s / window, 4))
    return out


def series() -> list[float]:
    return [round((n * 1.7 + (16 % 9)) % 23 + n / 5, 3) for n in range(1, 70)]


def main() -> None:
    values = series()
    m3 = moving_average(values, 3)
    m5 = moving_average(values, 5)
    m7 = moving_average(values, 7)
    print('practice_016')
    print('count', len(values))
    print('m3_last', m3[-5:])
    print('m5_last', m5[-5:])
    print('m7_last', m7[-5:])


if __name__ == '__main__':
    main()
