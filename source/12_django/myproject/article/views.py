from django.shortcuts import render
from django.views.generic import ListView, CreateView
from django.views.generic import DetailView, UpdateView,DeleteView
from article.models import Article
from django.urls import reverse_lazy
from django.core.paginator import Paginator
# /article/ : 1페이지 /article/?page=2 : 2페이지
def article_list1(request):
	article_list = Article.objects.all()
	paginator = Paginator(article_list, 3)
	page_number = request.GET.get('page', '1')
	page_object = paginator.get_page(page_number)
	return render(request, 'article/article_list.html',
			{'article_list':page_object,
			'page_obj':page_object})

article_list = ListView.as_view(model=Article, 
								#tamplate_name = 'article/article_list.html',
								paginate_by=3) # 1페이지에 3데이터

article_new = CreateView.as_view(model = Article, fields = '__all__')

article_detail = DetailView.as_view(model=Article)

article_edit = UpdateView.as_view(model=Article, fields = '__all__')

article_delete = DeleteView.as_view(model=Article,
									success_url = reverse_lazy("article:list"))