import itertools


def build_menu() -> list[tuple[str, int]]:
    return [
        ('ramen', 6500 + 85 % 50),
        ('kimbap', 4200 + 85 % 30),
        ('tteokbokki', 5000 + 85 % 40),
        ('dumpling', 4800 + 85 % 20),
        ('cola', 2000),
        ('tea', 2500),
    ]


def combos(menu: list[tuple[str, int]], budget: int) -> list[tuple[list[str], int]]:
    items = []
    for r in range(2, 5):
        for c in itertools.combinations(menu, r):
            names = [x[0] for x in c]
            price = sum(x[1] for x in c)
            if price <= budget:
                items.append((names, price))
    return sorted(items, key=lambda x: (x[1], len(x[0])))


def main() -> None:
    menu = build_menu()
    budget = 16000 + (85 % 500)
    selected = combos(menu, budget)
    print('practice_085')
    print('budget', budget)
    print('valid_count', len(selected))
    for names, price in selected[:20]:
        print(','.join(names), price)


if __name__ == '__main__':
    main()
