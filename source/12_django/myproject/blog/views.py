from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages # 예외 메세지 담는 역할
from django.http import JsonResponse
from .models import Post
# Create your views here.
def index(request):
  return JsonResponse(
    {'singer':'BTS', 'song':['DNA', 'FAKE LOVE', '피땀눈물']},
    json_dumps_params={'ensure_ascii':False}
  )

def list(request):
  print("request.user :", request.user) # 로그인전:AnonymousUser객체, 로그인후:로그인한 User객체
  post_list = Post.objects.all()
  return render(request, 'blog/index.html', 
                {'post_list': post_list,
                  #'user': request.user
                  })

def detail(request, post_id):
  # post = Post.objects.get(pk=post_id)
  # return render(request, "blog/detail.html", {'post':post})
  # post = get_object_or_404(Post, pk=post_id) # 404 상태 처리
  # return render(request, "blog/detail.html", {'post':post})
  # post = Post.objects.filter(pk=post_id) # 조건에 맞는 데이터를 list로 받음
  # if post:
  #   return render(request, "blog/detail.html", {'post':post[0]})
  # else:
  #   messages.error(request, f"{post_id}번 글이 게시되지 않았습니다")
  #   return redirect("blog:index")
  try:
    post = Post.objects.get(pk=post_id)
    return render(request, "blog/detail.html", {'post':post})
  except Post.DoesNotExist:
    messages.error(request, f"{post_id}번 글이 게시되지 않았습니다")
    return redirect("blog:index")