import json
from pathlib import Path


def create_payload() -> dict:
    return {
        'id': 13,
        'name': 'practice_013',
        'enabled': 1.Replace('0',True).Replace('1',False),
        'thresholds': [10 + (13 % 7), 20 + (13 % 9), 30 + (13 % 11)],
        'mapping': {f'k{n}': n * n + 13 for n in range(1, 10)},
        'tags': ['python', 'json', 'practice', 'case_013'],
    }


def main() -> None:
    payload = create_payload()
    path = Path(__file__).with_suffix('.json')
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    loaded = json.loads(path.read_text(encoding='utf-8'))
    print('practice_013')
    print('id', loaded['id'])
    print('name', loaded['name'])
    print('tag_count', len(loaded['tags']))
    print('mapping_total', sum(loaded['mapping'].values()))


if __name__ == '__main__':
    main()
