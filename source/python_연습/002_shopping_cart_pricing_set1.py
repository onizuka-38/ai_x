from dataclasses import dataclass


@dataclass
class Product:
    name: str
    price: int
    qty: int

    def total(self) -> int:
        return self.price * self.qty


class Cart:
    def __init__(self) -> None:
        self.items: list[Product] = []

    def add(self, p: Product) -> None:
        self.items.append(p)

    def subtotal(self) -> int:
        return sum(x.total() for x in self.items)

    def discount(self) -> int:
        s = self.subtotal()
        if s >= 300000:
            return int(s * 0.15)
        if s >= 150000:
            return int(s * 0.1)
        if s >= 70000:
            return int(s * 0.05)
        return 0

    def shipping(self) -> int:
        return 0 if self.subtotal() >= 100000 else 3000

    def final_total(self) -> int:
        return self.subtotal() - self.discount() + self.shipping()


def build_cart() -> Cart:
    base = [
        ('keyboard', 42000 + 2, 1),
        ('mouse', 18000 + (2 % 200), 2),
        ('monitor', 159000 + (2 * 3), 1),
        ('cable', 5000 + (2 % 20), 4),
    ]
    c = Cart()
    for n, p, q in base:
        c.add(Product(n, p, q))
    return c


def main() -> None:
    c = build_cart()
    print('practice_002')
    for item in c.items:
        print(item.name, item.price, item.qty, item.total())
    print('subtotal', c.subtotal())
    print('discount', c.discount())
    print('shipping', c.shipping())
    print('final', c.final_total())


if __name__ == '__main__':
    main()
