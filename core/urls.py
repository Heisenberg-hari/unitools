from django.urls import path
from . import views
from .views_api import log_operation

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("api/log-operation/", log_operation, name="log_operation"),
]
