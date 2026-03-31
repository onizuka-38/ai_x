from collections import Counter
import string


def normalize(text: str) -> str:
    t = text.lower()
    return ''.join(ch if ch in string.ascii_lowercase + ' ' else ' ' for ch in t)


def freq_words(text: str) -> Counter:
    words = [w for w in normalize(text).split() if len(w) >= 2]
    return Counter(words)


def top_n(counter: Counter, n: int) -> list[tuple[str, int]]:
    return sorted(counter.items(), key=lambda x: (-x[1], x[0]))[:n]


def make_text() -> str:
    parts = [
        'python data structures and algorithms',
        'practice makes stable coding habits',
        'functions classes loops and files',
        'readability matters for long projects',
        f'index value {53} creates unique samples',
    ]
    return ' '.join(parts * (2 + (53 % 3)))


def main() -> None:
    text = make_text()
    c = freq_words(text)
    print('practice_053')
    print('token_count', sum(c.values()))
    print('vocab_size', len(c))
    for word, cnt in top_n(c, 12):
        print(word, cnt)


if __name__ == '__main__':
    main()
