"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

# from blog import views
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", lambda req : redirect("blog:index")),
    path("blog/", include("blog.urls")),
    path("book/", include("book.urls")),
    path("article/", include("article.urls")),
    path("accounts/", include("accounts.urls")),
]
# 장고는 static은 자동 연결해 주나, media는 개발자가 url과 저장경로를 연결
from django.conf.urls.static import static
from . import settings
urlpatterns += static(settings.MEDIA_URL, # "/media/~~"
                    document_root = settings.MEDIA_ROOT) # BASE_DIR/_media/ 저장