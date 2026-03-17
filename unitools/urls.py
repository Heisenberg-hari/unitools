from django.contrib import admin
from django.conf import settings
from django.views.static import serve
from django.urls import re_path
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("pdf/", include("pdf_tools.urls")),
    path("image/", include("image_tools.urls")),
    path("document/", include("document_tools.urls")),
]

if settings.IS_VERCEL:
    # Vercel fallback: serve local static assets even when DEBUG=False.
    urlpatterns += [
        re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.BASE_DIR / "static"}),
    ]
