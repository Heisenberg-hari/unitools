from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Operation


def home(request):
    return render(request, "core/home.html")


@login_required
def dashboard(request):
    operations = Operation.objects.filter(user=request.user).order_by("-created_at")[:20]
    return render(request, "core/dashboard.html", {"operations": operations})
