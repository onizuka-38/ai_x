from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def home(request):
    # return HttpResponse("<h1>Hello, Django!</h1><p>Welcome to the home page.</p>")
    return render(request,
                  template_name="home.html",
                  context={"message": "장고하이ㅋㅋ"})
