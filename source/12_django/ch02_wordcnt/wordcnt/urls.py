# wordcnt 패키지안의 urls.py
# /wordcnt : text를 입력하는 form (POST/GET)
# /wordcnt/about : 도움말 페이지
# /wordcnt/result : 입력된 text의 글자수, 단어수, 각 단어 갯수 출력
from django.urls import path
from wordcnt import views
app_name = "wordcnt"
urlpatterns = [
  path("", views.wordinput, name="wordinput"), # wordcnt/
  path("about/", views.about, name="about"), # wordcnt/about/
  path("result/", views.result, name="result"), # wordcnt/result/
]