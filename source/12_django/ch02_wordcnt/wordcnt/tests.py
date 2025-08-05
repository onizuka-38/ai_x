from django.test import TestCase
# Create your tests here.
fulltxt = "홍길동 홍길동 아자"
strlength = len(fulltxt) # 글자수10
words = fulltxt.split() # 단어들['홍길동', '홍길동', '아자']
wordcnt = len(words) # 단어수
words_dic = dict() # 빈 딕셔너리 => {'홍길동':2, '아자':1}
for word in words:
  if word in words_dic.keys():
    words_dic[word] += 1
  else:
    words_dic[word] = 1
print('글자수 -',strlength)
print('단어들 -',words)
print('단어수 -',wordcnt)
print('출현 단어(리스트) - ', words_dic.items())#[('홍길동', 2), ('아자', 1)]