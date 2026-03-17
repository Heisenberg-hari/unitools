from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
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
    # Fallback static serving for Vercel serverless deployments.
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
