from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("pdf/", include("pdf_tools.urls")),
    path("image/", include("image_tools.urls")),
    path("document/", include("document_tools.urls")),
]

