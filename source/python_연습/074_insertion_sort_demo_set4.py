import random


def insertion_sort(a: list[int]) -> list[int]:
    arr = a[:]
    for i2 in range(1, len(arr)):
        key = arr[i2]
        j2 = i2 - 1
        while j2 >= 0 and arr[j2] > key:
            arr[j2 + 1] = arr[j2]
            j2 -= 1
        arr[j2 + 1] = key
    return arr


def main() -> None:
    random.seed(74)
    arr = [random.randint(1, 500) for _ in range(60)]
    sorted_arr = insertion_sort(arr)
    print('practice_074')
    print('input_first20', arr[:20])
    print('sorted_first20', sorted_arr[:20])
    print('sorted_last20', sorted_arr[-20:])
    print('is_sorted', sorted_arr == sorted(arr))


if __name__ == '__main__':
    main()
