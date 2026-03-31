from functools import lru_cache


@lru_cache(maxsize=None)
def ways(n: int) -> int:
    if n < 0:
        return 0
    if n == 0:
        return 1
    return ways(n-1) + ways(n-2) + ways(n-3)


def table(limit: int) -> list[tuple[int, int]]:
    return [(x, ways(x)) for x in range(limit + 1)]


def main() -> None:
    limit = 20 + (8 % 10)
    rows = table(limit)
    print('practice_008')
    print('limit', limit)
    for n, value in rows:
        print(n, value)


if __name__ == '__main__':
    main()
