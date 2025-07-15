def mask_password(password):
  return "*" * len(password)

if __name__=="__main__":
  password = input('비밀번호')
  print(mask_password(password))