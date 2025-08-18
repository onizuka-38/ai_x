from django.urls import path
from . import views
app_name='book'
urlpatterns = [
    path('', views.book_list, name="list"), # /book/
    path('new/', views.book_new, name="new"), # /book/new/
    path('<int:pk>/edit/', views.book_edit, name='edit'),  # /book/1/edit
    path('<int:pk>/delete/', views.book_delete, name='delete') # /book/1/delete
]
