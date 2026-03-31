from collections import deque


def bfs_graph(start: str, graph: dict[str, list[str]]) -> list[str]:
    q = deque([start])
    seen = {start}
    order: list[str] = []
    while q:
        cur = q.popleft()
        order.append(cur)
        for nxt in graph.get(cur, []):
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return order


def sample_graph() -> dict[str, list[str]]:
    nodes = [chr(ord('A') + n) for n in range(10)]
    g: dict[str, list[str]] = {n: [] for n in nodes}
    for n in range(len(nodes)):
        g[nodes[n]].append(nodes[(n + 1) % len(nodes)])
        g[nodes[n]].append(nodes[(n + 2 + (31 % 3)) % len(nodes)])
    return g


def main() -> None:
    g = sample_graph()
    order = bfs_graph('A', g)
    print('practice_031')
    for k in sorted(g):
        print(k, '->', ','.join(g[k]))
    print('bfs', ' '.join(order))


if __name__ == '__main__':
    main()
