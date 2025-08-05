from django.shortcuts import render

# Create your views here.
def wordinput(request):
  return render(request, "wordcnt/wordinput.html")

def about(request):
  return render(request, "wordcnt/about.html")

def result(request):
  'fulltxt 파라미터값 받아 글자수, 단어수, 출현단어등을 templates(result.html) 전송'
  # fulltxt = request.POST['fulltxt']
  # fulltxt = request.POST.get('fulltxt', '')
  fulltxt = request.GET.get('fulltxt')
  strlength = len(fulltxt) # 글자수10
  words = fulltxt.split() # 단어들['홍길동', '홍길동', '아자']
  wordcnt = len(words) # 단어수
  words_dic = dict() # 빈 딕셔너리 => {'홍길동':2, '아자':1}
  for word in words:
    if word in words_dic.keys():
      words_dic[word] += 1
    else:
      words_dic[word] = 1
  context = {
    'fulltxt':fulltxt,
    'strlength':strlength,
    'wordcnt':wordcnt,
    'dict':words_dic.items() #[('홍길동', 2), ('아자', 1)]
  }
  return render(request,
                'wordcnt/result.html',
                context)