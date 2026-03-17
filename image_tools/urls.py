from django.urls import path
from . import views

app_name = "image_tools"

urlpatterns = [
    path("", views.index, name="index"),
    path("compress/", views.compress, name="compress"),
    path("convert/", views.convert, name="convert"),
    path("resize/", views.resize, name="resize"),
    path("watermark/", views.watermark, name="watermark"),
    path("remove-bg/", views.remove_bg, name="remove_bg"),
    path("batch-rename/", views.batch_rename, name="batch_rename"),
]
