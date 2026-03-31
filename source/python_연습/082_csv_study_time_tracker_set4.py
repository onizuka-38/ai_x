import csv
from pathlib import Path


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for day in range(1, 21):
        study = 30 + (day * 7 + 82) % 90
        coding = 20 + (day * 5 + 82) % 80
        rows.append({'day': str(day), 'study': str(study), 'coding': str(coding)})
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['day', 'study', 'coding'])
        w.writeheader()
        w.writerows(rows)


def read_totals(path: Path) -> tuple[int, int]:
    a = 0
    b = 0
    with path.open('r', newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            a += int(r['study'])
            b += int(r['coding'])
    return a, b


def main() -> None:
    path = Path(__file__).with_suffix('.csv')
    rows = build_rows()
    write_csv(path, rows)
    study_total, coding_total = read_totals(path)
    print('practice_082')
    print('rows', len(rows))
    print('study_total', study_total)
    print('coding_total', coding_total)
    print('combined', study_total + coding_total)


if __name__ == '__main__':
    main()
