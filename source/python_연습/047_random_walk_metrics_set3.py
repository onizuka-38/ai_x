import random


def random_walk(steps: int) -> list[int]:
    random.seed(47)
    pos = 0
    trace = [pos]
    for _ in range(steps):
        pos += random.choice([-2, -1, 1, 2])
        trace.append(pos)
    return trace


def metrics(trace: list[int]) -> dict[str, int]:
    return {
        'min': min(trace),
        'max': max(trace),
        'final': trace[-1],
        'cross_zero': sum(1 for i2 in range(1, len(trace)) if trace[i2-1] * trace[i2] < 0),
    }


def main() -> None:
    t = random_walk(180)
    m = metrics(t)
    print('practice_047')
    print('len', len(t))
    print('min', m['min'])
    print('max', m['max'])
    print('final', m['final'])
    print('cross_zero', m['cross_zero'])
    print('tail', t[-15:])


if __name__ == '__main__':
    main()
