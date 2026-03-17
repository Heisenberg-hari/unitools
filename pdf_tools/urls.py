from django.urls import path
from . import views

app_name = "pdf_tools"

urlpatterns = [
    path("", views.index, name="index"),
    path("merge/", views.merge_pdf, name="merge"),
    path("split/", views.split_pdf, name="split"),
    path("compress/", views.compress_pdf, name="compress"),
    path("rotate/", views.rotate_pdf, name="rotate"),
    path("watermark/", views.watermark_pdf, name="watermark"),
    path("pdf-to-word/", views.pdf_to_word, name="pdf_to_word"),
    path("word-to-pdf/", views.word_to_pdf, name="word_to_pdf"),
]
