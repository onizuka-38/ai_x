from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.conf import global_settings as settings
from django.contrib.auth.views import LoginView, LogoutView
from .forms import SignupForm
from .models import Profile
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
# Create your views here.
def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        form = SignupForm()
    return render(request, "accounts/signup_form.html", {"form": form})

login = LoginView.as_view(template_name="accounts/login_form.html") 

@login_required
def profile(request): # 로그인 후에만 접근 가능
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={
            "phone_number": "",
            "address": "",
        }   
    )
    return render(request, 
                "accounts/profile.html", 
                {"profile": profile, "user": request.user, "is_new_profile": created})

logout = LogoutView.as_view(next_page=settings.LOGIN_URL)