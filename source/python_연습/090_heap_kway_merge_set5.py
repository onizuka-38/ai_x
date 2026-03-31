from heapq import heappush, heappop


def merge_k_sorted(lists: list[list[int]]) -> list[int]:
    heap: list[tuple[int, int, int]] = []
    for i2, arr in enumerate(lists):
        if arr:
            heappush(heap, (arr[0], i2, 0))
    out: list[int] = []
    while heap:
        value, i2, j2 = heappop(heap)
        out.append(value)
        nj = j2 + 1
        if nj < len(lists[i2]):
            heappush(heap, (lists[i2][nj], i2, nj))
    return out


def build_lists() -> list[list[int]]:
    base = []
    for g in range(5):
        row = sorted([(g + 1) * n + (90 % 13) for n in range(1, 16)])
        base.append(row)
    return base


def main() -> None:
    lists = build_lists()
    merged = merge_k_sorted(lists)
    print('practice_090')
    print('input_groups', len(lists))
    print('merged_count', len(merged))
    print('first20', merged[:20])
    print('last20', merged[-20:])


if __name__ == '__main__':
    main()
