import random


def quickselect(arr: list[int], k: int) -> int:
    if len(arr) == 1:
        return arr[0]
    pivot = random.choice(arr)
    lows = [x for x in arr if x < pivot]
    highs = [x for x in arr if x > pivot]
    pivots = [x for x in arr if x == pivot]
    if k < len(lows):
        return quickselect(lows, k)
    if k < len(lows) + len(pivots):
        return pivots[0]
    return quickselect(highs, k - len(lows) - len(pivots))


def main() -> None:
    random.seed(93)
    arr = [random.randint(1, 10000) for _ in range(101)]
    k = 50
    value = quickselect(arr, k)
    sorted_arr = sorted(arr)
    print('practice_093')
    print('k', k)
    print('value', value)
    print('check', value == sorted_arr[k])
    print('median', sorted_arr[len(sorted_arr)//2])


if __name__ == '__main__':
    main()
