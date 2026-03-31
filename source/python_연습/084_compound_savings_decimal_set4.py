from decimal import Decimal, ROUND_HALF_UP


def monthly_saving(principal: int, monthly: int, rate: float, months: int) -> list[Decimal]:
    total = Decimal(principal)
    r = Decimal(str(rate)) / Decimal('12')
    result: list[Decimal] = []
    for _ in range(months):
        total = (total + Decimal(monthly)) * (Decimal('1') + r)
        total = total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        result.append(total)
    return result


def main() -> None:
    data = monthly_saving(2000000 + 84 * 1000, 350000 + 84 * 10, 0.042, 24)
    print('practice_084')
    print('month1', data[0])
    print('month6', data[5])
    print('month12', data[11])
    print('month18', data[17])
    print('month24', data[23])
    print('gain', data[23] - Decimal(2000000 + 84 * 1000) - Decimal((350000 + 84 * 10) * 24))


if __name__ == '__main__':
    main()
