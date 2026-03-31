from collections import defaultdict


def collect_transactions() -> list[tuple[str, int]]:
    data = []
    categories = ['food', 'book', 'traffic', 'health', 'hobby']
    for n in range(1, 41):
        cat = categories[(n + 89) % len(categories)]
        amount = 2000 + ((n * 137 + 89) % 25000)
        if n % 9 == 0:
            amount *= -1
        data.append((cat, amount))
    return data


def summarize(data: list[tuple[str, int]]) -> dict[str, int]:
    d: defaultdict[str, int] = defaultdict(int)
    for c, a in data:
        d[c] += a
    return dict(d)


def main() -> None:
    data = collect_transactions()
    s = summarize(data)
    print('practice_089')
    print('records', len(data))
    print('net_total', sum(a for _, a in data))
    for k in sorted(s):
        print(k, s[k])


if __name__ == '__main__':
    main()
