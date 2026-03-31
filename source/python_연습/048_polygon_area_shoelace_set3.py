from collections import namedtuple


Point = namedtuple('Point', ['x', 'y'])


def polygon_area(points: list[Point]) -> float:
    s1 = 0
    s2 = 0
    for i2 in range(len(points)):
        j2 = (i2 + 1) % len(points)
        s1 += points[i2].x * points[j2].y
        s2 += points[i2].y * points[j2].x
    return abs(s1 - s2) / 2


def build_polygon() -> list[Point]:
    return [
        Point(1 + (48 % 3), 2),
        Point(6, 1 + (48 % 2)),
        Point(9, 5),
        Point(7, 10),
        Point(2, 9),
    ]


def main() -> None:
    p = build_polygon()
    a = polygon_area(p)
    print('practice_048')
    for pt in p:
        print(pt.x, pt.y)
    print('area', round(a, 4))


if __name__ == '__main__':
    main()
