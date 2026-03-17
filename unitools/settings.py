from pathlib import Path
import os
import shutil

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
IS_VERCEL = os.getenv("VERCEL") == "1"
DEBUG = os.getenv("DEBUG", "False" if IS_VERCEL else "True").lower() == "true"
ALLOWED_HOSTS = [h for h in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost,testserver,.vercel.app").split(",") if h]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "accounts",
    "pdf_tools",
    "image_tools",
    "document_tools",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "unitools.urls"
WSGI_APPLICATION = "unitools.wsgi.application"
ASGI_APPLICATION = "unitools.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

if IS_VERCEL:
    writable_db = Path("/tmp/db.sqlite3")
    source_db = BASE_DIR / "db.sqlite3"
    if source_db.exists() and not writable_db.exists():
        try:
            shutil.copy2(source_db, writable_db)
        except OSError:
            pass
    DATABASES["default"]["NAME"] = str(writable_db)
    # Avoid write attempts to DB-backed sessions/messages in ephemeral serverless runtime.
    SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
    MESSAGE_STORAGE = "django.contrib.messages.storage.cookie.CookieStorage"

AUTH_USER_MODEL = "accounts.User"
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "core:home"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {module}:{lineno} -> {message}",
            "style": "{",
        }
    },
    "handlers": {
        "console": {
            "level": "ERROR",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "unitools": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        }
    },
}
