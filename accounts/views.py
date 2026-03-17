import logging
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from .forms import RegisterForm

logger = logging.getLogger("unitools")


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully.")
            return redirect("core:home")
        logger.error("Registration errors: %s", form.errors)
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("core:home")
        messages.error(request, "Invalid credentials.")
        logger.error("Failed login attempt for username=%s", username)
    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    return redirect("core:home")

