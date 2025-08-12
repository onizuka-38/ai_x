from django.urls import path
from . import views
app_name='blog'
urlpatterns = [
    path("", views.list, name="index"), # /blog/ (blog:index)
    path("<int:post_id>/", views.detail, name="detail"), # /blog/2 : int컨버터 이용
]
