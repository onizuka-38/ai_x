import random


def build_matrix(size: int) -> list[list[int]]:
    random.seed(70)
    return [[random.randint(1, 30) for _ in range(size)] for _ in range(size)]


def transpose(m: list[list[int]]) -> list[list[int]]:
    return [list(col) for col in zip(*m)]


def multiply(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:
    bt = transpose(b)
    out: list[list[int]] = []
    for row in a:
        o_row = []
        for col in bt:
            o_row.append(sum(x * y for x, y in zip(row, col)))
        out.append(o_row)
    return out


def main() -> None:
    n = 4 + (70 % 3)
    a = build_matrix(n)
    b = build_matrix(n)
    c = multiply(a, b)
    print('practice_070')
    print('size', n)
    print('a0', a[0])
    print('b0', b[0])
    print('c0', c[0])
    print('diag_sum', sum(c[d][d] for d in range(n)))


if __name__ == '__main__':
    main()
