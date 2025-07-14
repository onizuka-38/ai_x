def mask_password(password):
    return '*' * len(password)

if __name__ == "__main__":
    password = input("비밀번호를 입력하세요: ")
    print(mask_password(password))