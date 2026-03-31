import re


def extract_emails(text: str) -> list[str]:
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}'
    return re.findall(pattern, text)


def mask(email: str) -> str:
    user, domain = email.split('@', 1)
    if len(user) <= 2:
        hidden = '*' * len(user)
    else:
        hidden = user[:2] + '*' * (len(user) - 2)
    return hidden + '@' + domain


def main() -> None:
    text = 'team61@example.com alpha.beta61@sample.org support61@domain.net no-email text'
    emails = extract_emails(text)
    print('practice_061')
    for e in emails:
        print(e, '=>', mask(e))
    print('count', len(emails))


if __name__ == '__main__':
    main()
