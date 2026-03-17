from django.urls import path
from . import views

app_name = "document_tools"

urlpatterns = [
    path("", views.index, name="index"),
    path("summarize/", views.summarize_page, name="summarize_page"),
    path("compare/", views.compare_page, name="compare"),
    path("translate/", views.translate_page, name="translate"),
    path("analyze/", views.analyze_page, name="analyze"),
    path("docx-to-pdf/", views.docx_to_pdf_page, name="docx_to_pdf"),
    path("api/summarize/", views.summarize_text_api, name="summarize"),
]
