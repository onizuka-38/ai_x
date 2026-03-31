from dataclasses import dataclass


@dataclass(order=True)
class Score:
    total: int
    name: str
    math: int
    eng: int
    py: int



def make_scores() -> list[Score]:
    raw = [
        ('mina', 70 + (87 % 20), 85, 90),
        ('jisu', 88, 77 + (87 % 10), 91),
        ('hoon', 92, 81, 80 + (87 % 15)),
        ('sora', 84, 94, 87),
        ('dani', 76, 89, 93),
    ]
    result: list[Score] = []
    for n, m, e, p in raw:
        result.append(Score(m+e+p, n, m, e, p))
    return result


def ranking(scores: list[Score]) -> list[Score]:
    return sorted(scores, reverse=True)


def main() -> None:
    rows = ranking(make_scores())
    print('practice_087')
    for idx2, s in enumerate(rows, 1):
        print(idx2, s.name, s.math, s.eng, s.py, s.total)


if __name__ == '__main__':
    main()
