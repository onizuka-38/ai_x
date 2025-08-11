from django.contrib import admin
from blog.models import Post
# Register your models here.
admin.site.register(Post) # admin 페이지에서 Post 테이블 액세스 가능
