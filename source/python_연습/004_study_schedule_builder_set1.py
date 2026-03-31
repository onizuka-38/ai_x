from datetime import datetime, timedelta


def build_schedule(start: str, days: int) -> list[dict[str, str]]:
    dt = datetime.strptime(start, '%Y-%m-%d')
    result: list[dict[str, str]] = []
    subjects = ['math', 'python', 'english', 'history', 'science', 'music']
    for n in range(days):
        day = dt + timedelta(days=n)
        s = subjects[(n + 4) % len(subjects)]
        result.append({
            'date': day.strftime('%Y-%m-%d'),
            'subject': s,
            'start': f'{9 + (n % 3):02d}:00',
            'end': f'{11 + (n % 3):02d}:00',
        })
    return result


def group_by_subject(rows: list[dict[str, str]]) -> dict[str, int]:
    d: dict[str, int] = {}
    for r in rows:
        d[r['subject']] = d.get(r['subject'], 0) + 1
    return d


def main() -> None:
    rows = build_schedule('2026-04-01', 28)
    g = group_by_subject(rows)
    print('practice_004')
    print('total_days', len(rows))
    for r in rows[:10]:
        print(r['date'], r['subject'], r['start'], r['end'])
    print('subject_count')
    for k in sorted(g):
        print(k, g[k])


if __name__ == '__main__':
    main()
