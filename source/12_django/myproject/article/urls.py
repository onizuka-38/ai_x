from django.urls import path
from . import views
'''
/article/ => article_list
/article/new => article추가(article_new)
/article/1/detail => 1번 article 상세보기(article_detail)
/article/1/edit => 1번 article 수정(article_edit)
/article/1/delete => 1번 article 삭제(article_delete)
'''
app_name = "article"
urlpatterns = [
    path("", views.article_list, name="list"),
    path("new/", views.article_new, name="new"),
    path("<int:pk>/detail/", views.article_detail, name='detail'),
    path("<int:pk>/edit/", views.article_edit, name='edit'),
    path("<int:pk>/delete/", views.article_delete, name='delete'),
]
