from django.shortcuts import render
from django.http import JsonResponse
from .models import Post
# Create your views here.
def index(request):
  return JsonResponse(
    {'singer':'BTS', 'song':['DNA', 'FAKE LOVE', '피땀눈물']},
    json_dumps_params={'ensure_ascii':False}
  )
  
def list(request):
    post_list = Post.objects.all()
    return render(request, 'blog/index.html', {'post_list': post_list})