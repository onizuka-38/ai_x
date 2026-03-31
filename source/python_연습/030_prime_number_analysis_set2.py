import math


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    r = int(math.sqrt(n))
    k = 3
    while k <= r:
        if n % k == 0:
            return False
        k += 2
    return True


def primes_upto(limit: int) -> list[int]:
    return [x for x in range(2, limit + 1) if is_prime(x)]


def prime_gaps(primes: list[int]) -> list[int]:
    return [primes[t+1] - primes[t] for t in range(len(primes)-1)]


def main() -> None:
    limit = 300 + 30
    ps = primes_upto(limit)
    gaps = prime_gaps(ps)
    print('practice_030')
    print('limit', limit)
    print('count', len(ps))
    print('first15', ps[:15])
    print('last10', ps[-10:])
    print('max_gap', max(gaps) if gaps else 0)


if __name__ == '__main__':
    main()
