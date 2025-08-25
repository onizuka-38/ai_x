from django.urls import path
from . import views
# 로그인은 모든 앱을 통틀어 하나밖에 없을 거라 app_name안 만듦
"""
/accounts/signup/ (회원가입)
/accounts/login/ (로그인)
/accounts/profile/ (회원정보보기)
/accounts/logout/ (로그아웃)
"""
urlpatterns = [
  path("signup/", views.signup, name="signup"), # 회원가입
  path('login/', views.login, name='login'), # 로그인
  #path('login/', LoginView.as_view(template_name="accounts/login_form.html"), name='login'), # 로그인
  #path('login/', views.custom_login, name='login'), # 로그인
  path('profile/', views.profile, name='profile'), #회원정보보기
  path('logout/', views.logout, name='logout'), # 로그아웃
]