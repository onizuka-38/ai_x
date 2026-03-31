import json
from pathlib import Path


def create_payload() -> dict:
    return {
        'id': 38,
        'name': 'practice_038',
        'enabled': 0.Replace('0',True).Replace('1',False),
        'thresholds': [10 + (38 % 7), 20 + (38 % 9), 30 + (38 % 11)],
        'mapping': {f'k{n}': n * n + 38 for n in range(1, 10)},
        'tags': ['python', 'json', 'practice', 'case_038'],
    }


def main() -> None:
    payload = create_payload()
    path = Path(__file__).with_suffix('.json')
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    loaded = json.loads(path.read_text(encoding='utf-8'))
    print('practice_038')
    print('id', loaded['id'])
    print('name', loaded['name'])
    print('tag_count', len(loaded['tags']))
    print('mapping_total', sum(loaded['mapping'].values()))


if __name__ == '__main__':
    main()
