# UniTools – AI-Powered File Processing Platform

> A Django-based platform inspired by iLovePDF, extended for **PDF, Image, and Document** processing.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Hybrid Architecture – Online Website, Local Processing](#2-hybrid-architecture--online-website-local-processing)
3. [Tech Stack](#3-tech-stack)
4. [Project Setup](#4-project-setup)
5. [Project Structure](#5-project-structure)
6. [Settings Configuration](#6-settings-configuration)
7. [Database Models](#7-database-models)
8. [URL Routing](#8-url-routing)
9. [Views & Business Logic](#9-views--business-logic)
10. [Templates & Frontend](#10-templates--frontend)
11. [PDF Tools Module](#11-pdf-tools-module)
12. [Image Tools Module](#12-image-tools-module)
13. [Document Tools Module](#13-document-tools-module)
14. [User Authentication](#14-user-authentication)
15. [Error Logging System](#15-error-logging-system)
16. [Deployment](#16-deployment)

---

## 1. Project Overview

**UniTools** is a large-scale Django web application providing file processing tools across three modules:

| Module | Tools |
|--------|-------|
| 📄 PDF | Merge, Split, Compress, Rotate, Watermark, PDF→Word, Word→PDF |
| 🖼 Image | Compress, Format Convert, Resize, Remove BG, Watermark, Batch Rename |
| 📝 Document | Word→PDF, PPT→PDF, OCR, Summarization (AI), Translation, Comparison |

**Extra Features:** User auth, file history dashboard, drag-and-drop upload, batch processing, AI tools.

---

## 2. Hybrid Architecture – Online Website, Local Processing

> **Key Principle:** The website runs online (hosted on a server), but all file conversions and processing run **locally on the client's device** (in the browser). Files never leave the user's machine during processing.

### Why This Architecture?

| Benefit | Description |
|---------|-------------|
| 🔒 **Privacy** | User files are never uploaded to the server for processing |
| ⚡ **Speed** | No upload/download wait — processing is instant on the client |
| 💰 **Cost** | No heavy server-side compute needed for file operations |
| 📈 **Scalability** | Server only handles auth, UI, & metadata — not CPU-heavy conversions |

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    ONLINE SERVER (Django)                    │
│                                                             │
│  ✅ Serve the website (HTML/CSS/JS)                         │
│  ✅ User authentication & sessions                          │
│  ✅ File history & operation logs (metadata only)           │
│  ✅ Serve static assets & JS processing libraries           │
│  ✅ AI features (summarization, translation) via API        │
│  ❌ Does NOT process/convert files                          │
└─────────────────────┬───────────────────────────────────────┘
                      │  HTTPS (UI + metadata only)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│               CLIENT BROWSER (User's Device)                │
│                                                             │
│  ✅ File selection via drag-and-drop or file picker         │
│  ✅ PDF processing     → pdf-lib (WebAssembly)              │
│  ✅ PDF rendering      → pdf.js                             │
│  ✅ Image processing   → browser-image-compression + Canvas │
│  ✅ OCR extraction     → Tesseract.js (WebAssembly)         │
│  ✅ Format conversion  → Canvas API / JS libraries          │
│  ✅ Result downloaded directly from browser memory          │
│  ❌ Files NEVER uploaded to server for conversion           │
└─────────────────────────────────────────────────────────────┘
```

### Client-Side JavaScript Libraries

| Tool Category | Library | Purpose |
|---------------|---------|---------|
| PDF Merge/Split/Rotate | [pdf-lib](https://pdf-lib.js.org/) | Manipulate PDF pages in-browser |
| PDF Rendering | [pdf.js](https://mozilla.github.io/pdf.js/) | Render PDFs for preview |
| PDF Compression | pdf-lib + rewrite streams | Reduce size client-side |
| Image Compress | [browser-image-compression](https://www.npmjs.com/package/browser-image-compression) | Lossy/lossless compress |
| Image Resize/Convert | Canvas API | Native browser image manipulation |
| Image BG Removal | [remove.bg JS SDK](https://www.remove.bg/) or TensorFlow.js | AI background removal |
| OCR | [Tesseract.js](https://tesseract.projectnaptha.com/) | Extract text from images locally |
| Watermark | Canvas API / pdf-lib | Overlay text on images/PDFs |

### Client-Side Processing Engine — `static/js/processing_engine.js`

```javascript
/**
 * UniTools Client-Side Processing Engine
 * All conversions run locally in the user's browser.
 * The server is ONLY used for auth, UI, and logging metadata.
 */

import { PDFDocument, degrees } from 'pdf-lib';
import imageCompression from 'browser-image-compression';

// ─── PDF TOOLS (client-side) ────────────────────────────────

export async function mergePDFs(fileList) {
    const mergedPdf = await PDFDocument.create();
    for (const file of fileList) {
        const bytes = await file.arrayBuffer();
        const pdf = await PDFDocument.load(bytes);
        const pages = await mergedPdf.copyPages(pdf, pdf.getPageIndices());
        pages.forEach(page => mergedPdf.addPage(page));
    }
    const mergedBytes = await mergedPdf.save();
    return new Blob([mergedBytes], { type: 'application/pdf' });
}

export async function splitPDF(file, pageRanges) {
    const bytes = await file.arrayBuffer();
    const srcPdf = await PDFDocument.load(bytes);
    const results = [];
    for (const [start, end] of pageRanges) {
        const newPdf = await PDFDocument.create();
        const indices = Array.from({ length: end - start + 1 }, (_, i) => start - 1 + i);
        const pages = await newPdf.copyPages(srcPdf, indices);
        pages.forEach(p => newPdf.addPage(p));
        const newBytes = await newPdf.save();
        results.push(new Blob([newBytes], { type: 'application/pdf' }));
    }
    return results;
}

export async function rotatePDF(file, rotationDegrees = 90) {
    const bytes = await file.arrayBuffer();
    const pdf = await PDFDocument.load(bytes);
    pdf.getPages().forEach(page => page.setRotation(degrees(rotationDegrees)));
    const rotatedBytes = await pdf.save();
    return new Blob([rotatedBytes], { type: 'application/pdf' });
}

export async function compressPDF(file) {
    // Client-side: reload and re-save (strips unused objects)
    const bytes = await file.arrayBuffer();
    const pdf = await PDFDocument.load(bytes);
    const compressedBytes = await pdf.save({ useObjectStreams: true });
    return new Blob([compressedBytes], { type: 'application/pdf' });
}

// ─── IMAGE TOOLS (client-side) ──────────────────────────────

export async function compressImage(file, quality = 0.7) {
    const options = {
        maxSizeMB: 1,
        maxWidthOrHeight: 1920,
        useWebWorker: true,
        initialQuality: quality,
    };
    return await imageCompression(file, options);
}

export async function resizeImage(file, targetWidth, targetHeight) {
    return new Promise((resolve) => {
        const img = new Image();
        img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = targetWidth;
            canvas.height = targetHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, targetWidth, targetHeight);
            canvas.toBlob(resolve, file.type || 'image/png');
        };
        img.src = URL.createObjectURL(file);
    });
}

export async function convertImageFormat(file, targetFormat = 'image/webp') {
    return new Promise((resolve) => {
        const img = new Image();
        img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth;
            canvas.height = img.naturalHeight;
            canvas.getContext('2d').drawImage(img, 0, 0);
            canvas.toBlob(resolve, targetFormat, 0.92);
        };
        img.src = URL.createObjectURL(file);
    });
}

// ─── OCR (client-side via Tesseract.js) ─────────────────────

export async function extractTextOCR(file) {
    const Tesseract = await import('tesseract.js');
    const { data: { text } } = await Tesseract.recognize(file, 'eng');
    return text;
}

// ─── UTILITY: trigger download from browser memory ──────────

export function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ─── LOG OPERATION TO SERVER (metadata only, no file upload) ─

export async function logOperationToServer(toolName, fileName, fileSize) {
    try {
        await fetch('/api/log-operation/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify({
                tool_name: toolName,
                file_name: fileName,
                file_size: fileSize,
            }),
        });
    } catch (err) {
        console.warn('Failed to log operation to server:', err);
    }
}

function getCSRFToken() {
    return document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
}
```

### Server-Side: Metadata-Only API — `core/views_api.py`

The Django server **only** logs the operation metadata — it never receives the actual file content for conversions.

```python
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from .models import Operation, UploadedFile

logger = logging.getLogger('unitools')

@require_POST
@csrf_protect
@login_required
def log_operation(request):
    """Log metadata about a client-side operation. No file data is received."""
    import json
    try:
        data = json.loads(request.body)
        # Create a lightweight record — file was processed on client
        UploadedFile.objects.create(
            user=request.user,
            original_name=data.get('file_name', 'unknown'),
            file_type=_detect_type(data.get('file_name', '')),
            file_size=data.get('file_size', 0),
            is_temp=True,
        )
        Operation.objects.create(
            user=request.user,
            tool_name=data.get('tool_name', 'unknown'),
            status='completed',
            # No input_file FK needed — processing was client-side
        )
        return JsonResponse({'status': 'logged'})
    except Exception as e:
        logger.error(f"log_operation failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)

def _detect_type(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext == 'pdf': return 'pdf'
    if ext in ('png','jpg','jpeg','webp','bmp','gif'): return 'image'
    return 'document'
```

### URL for Metadata API — add to `core/urls.py`

```python
from .views_api import log_operation

urlpatterns += [
    path('api/log-operation/', log_operation, name='log_operation'),
]
```

### What Runs Where — Summary Table

| Feature | Runs On | Reason |
|---------|---------|--------|
| Website UI & pages | 🌐 Server | Served via Django templates |
| User login/register | 🌐 Server | Auth needs server-side sessions |
| PDF merge/split/rotate/compress | 💻 Client | pdf-lib in browser (WebAssembly) |
| PDF watermark | 💻 Client | pdf-lib text overlay |
| Image compress/resize/convert | 💻 Client | Canvas API + browser-image-compression |
| Image background removal | 💻 Client | TensorFlow.js or remove.bg SDK |
| OCR text extraction | 💻 Client | Tesseract.js (WebAssembly) |
| AI Summarization | 🌐 Server | Needs GPU/large model (transformers) |
| AI Translation | 🌐 Server | googletrans API call |
| Document comparison | 💻 Client | JS diff libraries |
| File history dashboard | 🌐 Server | Reads metadata from database |
| Operation logging | 🌐 Server | Stores metadata only (no file content) |

### Server-Only Tools (AI Features)

Some tools **require server-side processing** because they need large AI models:

```python
# document_tools/views.py — Server-side AI endpoints

@handle_tool_errors
@login_required
def summarize_text_api(request):
    """AI summarization — runs on server (requires transformers model)."""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        text = data.get('text', '')
        from .services import summarize_text
        summary = summarize_text(text)
        return JsonResponse({'summary': summary})
    return JsonResponse({'error': 'POST required'}, status=405)

@handle_tool_errors
@login_required
def translate_text_api(request):
    """Translation — runs on server (uses googletrans)."""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        from .services import translate_text
        result = translate_text(data.get('text', ''), data.get('lang', 'es'))
        return JsonResponse({'translated': result})
    return JsonResponse({'error': 'POST required'}, status=405)
```

### Frontend Integration Example

```html
<!-- pdf_tools/templates/pdf_tools/merge.html -->
{% extends "base.html" %}
{% block content %}
<div class="tool-page">
    <h2>Merge PDF</h2>
    <div class="drop-zone" id="merge-dropzone">
        <p>Drag & drop PDF files here, or click to select</p>
        <input type="file" multiple accept=".pdf" id="merge-files" hidden>
    </div>
    <button class="btn btn-primary mt-3" id="merge-btn" disabled>Merge PDFs</button>
    <div id="progress" class="mt-2" style="display:none;">
        <div class="spinner-border text-primary"></div> Processing locally...
    </div>
</div>
{% endblock %}

{% block scripts %}
<script type="module">
import { mergePDFs, downloadBlob, logOperationToServer } from '/static/js/processing_engine.js';

const input = document.getElementById('merge-files');
const btn = document.getElementById('merge-btn');
const progress = document.getElementById('progress');

input.addEventListener('change', () => {
    btn.disabled = input.files.length < 2;
});

btn.addEventListener('click', async () => {
    progress.style.display = 'block';
    btn.disabled = true;
    try {
        // ✅ Processing happens 100% in the browser
        const merged = await mergePDFs(Array.from(input.files));
        downloadBlob(merged, 'merged.pdf');

        // ✅ Only log metadata to server (no file content sent)
        await logOperationToServer('merge_pdf', 'merged.pdf', merged.size);
    } catch (err) {
        alert('Error: ' + err.message);
        console.error(err);
    } finally {
        progress.style.display = 'none';
        btn.disabled = false;
    }
});
</script>
{% endblock %}
```

---

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.x, Django REST Framework |
| Database | PostgreSQL (prod) / SQLite (dev) |
| PDF Processing | PyPDF2, reportlab, pdf2docx |
| Image Processing | Pillow, rembg (background removal) |
| Document Processing | python-docx, python-pptx, pytesseract (OCR) |
| AI Features | transformers (summarization), googletrans |
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5 |
| Task Queue | Celery + Redis |
| Storage | Django FileSystem (dev) / AWS S3 (prod) |
| Logging | Python `logging` → `errors.log` |

---

## 3. Project Setup

### Step 1: Create Virtual Environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install django djangorestframework psycopg2-binary
pip install PyPDF2 reportlab pdf2docx
pip install Pillow rembg
pip install python-docx python-pptx pytesseract
pip install transformers googletrans==4.0.0-rc1
pip install celery redis django-celery-results
pip install django-allauth django-crispy-forms crispy-bootstrap5
pip install gunicorn whitenoise django-storages boto3
pip install difflib  # built-in, no install needed
```

Save dependencies:

```bash
pip freeze > requirements.txt
```

### Step 3: Create Django Project

```bash
django-admin startproject unitools .
```

### Step 4: Create Apps

```bash
python manage.py startapp accounts
python manage.py startapp core
python manage.py startapp pdf_tools
python manage.py startapp image_tools
python manage.py startapp document_tools
python manage.py startapp dashboard
```

---

## 4. Project Structure

```
unitools/
├── manage.py
├── requirements.txt
├── errors.log                  # Error log file
├── unitools/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py
├── accounts/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   └── templates/accounts/
├── core/
│   ├── models.py               # Shared models (File, Operation)
│   ├── views.py                # Homepage, shared views
│   ├── urls.py
│   ├── utils.py                # Shared utility functions
│   └── templates/core/
├── pdf_tools/
│   ├── views.py
│   ├── urls.py
│   ├── services.py             # PDF processing logic
│   └── templates/pdf_tools/
├── image_tools/
│   ├── views.py
│   ├── urls.py
│   ├── services.py             # Image processing logic
│   └── templates/image_tools/
├── document_tools/
│   ├── views.py
│   ├── urls.py
│   ├── services.py             # Document processing logic
│   └── templates/document_tools/
├── dashboard/
│   ├── views.py
│   ├── urls.py
│   └── templates/dashboard/
├── templates/
│   └── base.html               # Global base template
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   └── img/
└── media/
    ├── uploads/
    └── processed/
```

---

## 5. Settings Configuration

### `unitools/settings.py`

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_celery_results',
    # Local apps
    'accounts',
    'core',
    'pdf_tools',
    'image_tools',
    'document_tools',
    'dashboard',
]

AUTH_USER_MODEL = 'accounts.User'

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# File upload settings
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Celery
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

# ── LOGGING → errors.log ──────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {module}:{lineno} → {message}',
            'style': '{',
        },
    },
    'handlers': {
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'errors.log',
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'unitools': {
            'handlers': ['console', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

### `unitools/celery.py`

```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unitools.settings')
app = Celery('unitools')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

### `unitools/__init__.py`

```python
from .celery import app as celery_app
__all__ = ('celery_app',)
```

---

## 6. Database Models

### `accounts/models.py` – Custom User

```python
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    storage_used = models.BigIntegerField(default=0)  # bytes
    max_storage = models.BigIntegerField(default=1073741824)  # 1GB

    def storage_percent(self):
        return round((self.storage_used / self.max_storage) * 100, 1)

    def __str__(self):
        return self.email or self.username
```

### `core/models.py` – File & Operation

```python
import uuid
import logging
from django.db import models
from django.conf import settings

logger = logging.getLogger('unitools')

class UploadedFile(models.Model):
    FILE_TYPES = [
        ('pdf', 'PDF'), ('image', 'Image'), ('document', 'Document'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='files', null=True, blank=True)
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    original_name = models.CharField(max_length=500)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES)
    file_size = models.BigIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_temp = models.BooleanField(default=True)  # auto-delete after 1 hour

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.original_name

    def save(self, *args, **kwargs):
        try:
            if self.file:
                self.file_size = self.file.size
        except Exception as e:
            logger.error(f"Error saving file {self.original_name}: {e}")
        super().save(*args, **kwargs)


class Operation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'), ('processing', 'Processing'),
        ('completed', 'Completed'), ('failed', 'Failed'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='operations', null=True, blank=True)
    input_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE,
                                   related_name='operations')
    tool_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    output_file = models.FileField(upload_to='processed/%Y/%m/%d/', blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.tool_name} – {self.status}"
```

### Run Migrations

```bash
python manage.py makemigrations accounts core
python manage.py migrate
python manage.py createsuperuser
```

---

## 7. URL Routing

### `unitools/urls.py`

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('pdf/', include('pdf_tools.urls')),
    path('image/', include('image_tools.urls')),
    path('docs/', include('document_tools.urls')),
    path('dashboard/', include('dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### `pdf_tools/urls.py` (example pattern — repeat for other apps)

```python
from django.urls import path
from . import views

app_name = 'pdf_tools'

urlpatterns = [
    path('', views.index, name='index'),
    path('merge/', views.merge_pdf, name='merge'),
    path('split/', views.split_pdf, name='split'),
    path('compress/', views.compress_pdf, name='compress'),
    path('rotate/', views.rotate_pdf, name='rotate'),
    path('watermark/', views.add_watermark, name='watermark'),
    path('pdf-to-word/', views.pdf_to_word, name='pdf_to_word'),
    path('word-to-pdf/', views.word_to_pdf, name='word_to_pdf'),
]
```

---

## 8. Views & Business Logic

### `core/utils.py` – Shared Error-Handling Utility

```python
import logging
import traceback
from functools import wraps
from django.http import JsonResponse

logger = logging.getLogger('unitools')

def handle_tool_errors(view_func):
    """Decorator that catches exceptions, logs to errors.log, and returns error response."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"[{view_func.__name__}] {e}\n{tb}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': str(e)}, status=500)
            from django.shortcuts import render
            return render(request, 'core/error.html', {'error': str(e)}, status=500)
    return wrapper
```

---

## 9. Templates & Frontend

### `templates/base.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}UniTools{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
          rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons/font/bootstrap-icons.css"
          rel="stylesheet">
    {% load static %}
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">🛠 UniTools</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="{% url 'pdf_tools:index' %}">📄 PDF</a>
                <a class="nav-link" href="{% url 'image_tools:index' %}">🖼 Image</a>
                <a class="nav-link" href="{% url 'document_tools:index' %}">📝 Docs</a>
                {% if user.is_authenticated %}
                <a class="nav-link" href="{% url 'dashboard:index' %}">Dashboard</a>
                <a class="nav-link" href="{% url 'accounts:logout' %}">Logout</a>
                {% else %}
                <a class="nav-link" href="{% url 'accounts:login' %}">Login</a>
                {% endif %}
            </div>
        </div>
    </nav>
    <main class="container my-4">
        {% if messages %}
        {% for message in messages %}
        <div class="alert alert-{{ message.tags }} alert-dismissible fade show">
            {{ message }} <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
        {% endfor %}
        {% endif %}
        {% block content %}{% endblock %}
    </main>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js">
    </script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

### Drag & Drop Upload Component — `static/js/main.js`

```javascript
document.addEventListener('DOMContentLoaded', () => {
    const dropZones = document.querySelectorAll('.drop-zone');
    dropZones.forEach(zone => {
        const input = zone.querySelector('input[type="file"]');
        zone.addEventListener('click', () => input.click());
        zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('active'); });
        zone.addEventListener('dragleave', () => zone.classList.remove('active'));
        zone.addEventListener('drop', e => {
            e.preventDefault();
            zone.classList.remove('active');
            input.files = e.dataTransfer.files;
            input.dispatchEvent(new Event('change'));
        });
    });
});
```

---

## 10. PDF Tools Module

### `pdf_tools/services.py`

```python
import io, logging
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.core.files.base import ContentFile

logger = logging.getLogger('unitools')

def merge_pdfs(file_list):
    """Merge multiple PDF files into one."""
    try:
        merger = PdfMerger()
        for f in file_list:
            merger.append(f)
        output = io.BytesIO()
        merger.write(output)
        merger.close()
        output.seek(0)
        return ContentFile(output.read(), name='merged.pdf')
    except Exception as e:
        logger.error(f"merge_pdfs failed: {e}")
        raise

def split_pdf(file_obj, page_ranges):
    """Split PDF by page ranges. page_ranges = [(1,3), (4,6)]"""
    try:
        reader = PdfReader(file_obj)
        results = []
        for start, end in page_ranges:
            writer = PdfWriter()
            for i in range(start - 1, min(end, len(reader.pages))):
                writer.add_page(reader.pages[i])
            buf = io.BytesIO()
            writer.write(buf)
            buf.seek(0)
            results.append(ContentFile(buf.read(), name=f'split_{start}-{end}.pdf'))
        return results
    except Exception as e:
        logger.error(f"split_pdf failed: {e}")
        raise

def compress_pdf(file_obj):
    """Compress PDF by removing duplication."""
    try:
        reader = PdfReader(file_obj)
        writer = PdfWriter()
        for page in reader.pages:
            page.compress_content_streams()
            writer.add_page(page)
        buf = io.BytesIO()
        writer.write(buf)
        buf.seek(0)
        return ContentFile(buf.read(), name='compressed.pdf')
    except Exception as e:
        logger.error(f"compress_pdf failed: {e}")
        raise

def rotate_pdf(file_obj, degrees=90):
    """Rotate all pages by given degrees."""
    try:
        reader = PdfReader(file_obj)
        writer = PdfWriter()
        for page in reader.pages:
            page.rotate(degrees)
            writer.add_page(page)
        buf = io.BytesIO()
        writer.write(buf)
        buf.seek(0)
        return ContentFile(buf.read(), name='rotated.pdf')
    except Exception as e:
        logger.error(f"rotate_pdf failed: {e}")
        raise

def add_watermark_to_pdf(file_obj, watermark_text):
    """Add text watermark to every page."""
    try:
        # Create watermark page
        wm_buf = io.BytesIO()
        c = canvas.Canvas(wm_buf, pagesize=letter)
        c.setFont("Helvetica", 50)
        c.setFillAlpha(0.3)
        c.saveState()
        c.translate(300, 400)
        c.rotate(45)
        c.drawCentredString(0, 0, watermark_text)
        c.restoreState()
        c.save()
        wm_buf.seek(0)
        wm_reader = PdfReader(wm_buf)
        wm_page = wm_reader.pages[0]

        reader = PdfReader(file_obj)
        writer = PdfWriter()
        for page in reader.pages:
            page.merge_page(wm_page)
            writer.add_page(page)
        buf = io.BytesIO()
        writer.write(buf)
        buf.seek(0)
        return ContentFile(buf.read(), name='watermarked.pdf')
    except Exception as e:
        logger.error(f"add_watermark failed: {e}")
        raise
```

### `pdf_tools/views.py`

```python
import logging
from django.shortcuts import render, redirect
from django.http import FileResponse
from django.contrib import messages
from core.utils import handle_tool_errors
from core.models import UploadedFile, Operation
from . import services

logger = logging.getLogger('unitools')

def index(request):
    tools = [
        {'name': 'Merge PDF', 'icon': 'bi-files', 'url': 'pdf_tools:merge', 'desc': 'Combine multiple PDFs'},
        {'name': 'Split PDF', 'icon': 'bi-scissors', 'url': 'pdf_tools:split', 'desc': 'Extract pages'},
        {'name': 'Compress PDF', 'icon': 'bi-file-zip', 'url': 'pdf_tools:compress', 'desc': 'Reduce file size'},
        {'name': 'Rotate PDF', 'icon': 'bi-arrow-repeat', 'url': 'pdf_tools:rotate', 'desc': 'Rotate pages'},
        {'name': 'Watermark', 'icon': 'bi-droplet', 'url': 'pdf_tools:watermark', 'desc': 'Add text watermark'},
        {'name': 'PDF → Word', 'icon': 'bi-filetype-docx', 'url': 'pdf_tools:pdf_to_word', 'desc': 'Convert to DOCX'},
        {'name': 'Word → PDF', 'icon': 'bi-filetype-pdf', 'url': 'pdf_tools:word_to_pdf', 'desc': 'Convert to PDF'},
    ]
    return render(request, 'pdf_tools/index.html', {'tools': tools})

@handle_tool_errors
def merge_pdf(request):
    if request.method == 'POST':
        files = request.FILES.getlist('files')
        if len(files) < 2:
            messages.error(request, 'Upload at least 2 PDF files.')
            return redirect('pdf_tools:merge')
        result = services.merge_pdfs(files)
        return FileResponse(result, as_attachment=True, filename='merged.pdf')
    return render(request, 'pdf_tools/merge.html')

@handle_tool_errors
def compress_pdf(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        result = services.compress_pdf(file)
        return FileResponse(result, as_attachment=True, filename='compressed.pdf')
    return render(request, 'pdf_tools/compress.html')

@handle_tool_errors
def split_pdf(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        ranges = request.POST.get('ranges', '1-1')
        page_ranges = [tuple(map(int, r.strip().split('-'))) for r in ranges.split(',')]
        results = services.split_pdf(file, page_ranges)
        return FileResponse(results[0], as_attachment=True, filename='split.pdf')
    return render(request, 'pdf_tools/split.html')

@handle_tool_errors
def rotate_pdf(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        degrees = int(request.POST.get('degrees', 90))
        result = services.rotate_pdf(file, degrees)
        return FileResponse(result, as_attachment=True, filename='rotated.pdf')
    return render(request, 'pdf_tools/rotate.html')

@handle_tool_errors
def add_watermark(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        text = request.POST.get('watermark_text', 'CONFIDENTIAL')
        result = services.add_watermark_to_pdf(file, text)
        return FileResponse(result, as_attachment=True, filename='watermarked.pdf')
    return render(request, 'pdf_tools/watermark.html')

@handle_tool_errors
def pdf_to_word(request):
    if request.method == 'POST':
        from pdf2docx import Converter
        import tempfile, os
        file = request.FILES.get('file')
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
            for chunk in file.chunks():
                tmp_pdf.write(chunk)
            tmp_pdf_path = tmp_pdf.name
        tmp_docx_path = tmp_pdf_path.replace('.pdf', '.docx')
        try:
            cv = Converter(tmp_pdf_path)
            cv.convert(tmp_docx_path)
            cv.close()
            with open(tmp_docx_path, 'rb') as f:
                from django.core.files.base import ContentFile
                result = ContentFile(f.read(), name='converted.docx')
            return FileResponse(result, as_attachment=True, filename='converted.docx')
        finally:
            os.unlink(tmp_pdf_path)
            if os.path.exists(tmp_docx_path):
                os.unlink(tmp_docx_path)
    return render(request, 'pdf_tools/pdf_to_word.html')

@handle_tool_errors
def word_to_pdf(request):
    if request.method == 'POST':
        messages.info(request, 'Word→PDF requires LibreOffice. Install it for full support.')
    return render(request, 'pdf_tools/word_to_pdf.html')
```

---

## 11. Image Tools Module

### `image_tools/services.py`

```python
import io, logging
from PIL import Image
from django.core.files.base import ContentFile

logger = logging.getLogger('unitools')

FORMAT_MAP = {'jpg': 'JPEG', 'jpeg': 'JPEG', 'png': 'PNG', 'webp': 'WEBP', 'bmp': 'BMP'}

def compress_image(file_obj, quality=70):
    try:
        img = Image.open(file_obj)
        buf = io.BytesIO()
        fmt = img.format or 'JPEG'
        img.save(buf, format=fmt, quality=quality, optimize=True)
        buf.seek(0)
        return ContentFile(buf.read(), name=f'compressed.{fmt.lower()}')
    except Exception as e:
        logger.error(f"compress_image failed: {e}")
        raise

def convert_image_format(file_obj, target_format='png'):
    try:
        img = Image.open(file_obj).convert('RGB')
        buf = io.BytesIO()
        fmt = FORMAT_MAP.get(target_format.lower(), 'PNG')
        img.save(buf, format=fmt)
        buf.seek(0)
        return ContentFile(buf.read(), name=f'converted.{target_format.lower()}')
    except Exception as e:
        logger.error(f"convert_image_format failed: {e}")
        raise

def resize_image(file_obj, width, height):
    try:
        img = Image.open(file_obj)
        img = img.resize((width, height), Image.LANCZOS)
        buf = io.BytesIO()
        fmt = img.format or 'PNG'
        img.save(buf, format=fmt)
        buf.seek(0)
        return ContentFile(buf.read(), name=f'resized.{fmt.lower()}')
    except Exception as e:
        logger.error(f"resize_image failed: {e}")
        raise

def add_watermark_to_image(file_obj, watermark_text):
    try:
        from PIL import ImageDraw, ImageFont
        img = Image.open(file_obj).convert('RGBA')
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        try:
            font = ImageFont.truetype("arial.ttf", size=40)
        except IOError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (img.width - tw) // 2
        y = (img.height - th) // 2
        draw.text((x, y), watermark_text, fill=(255, 255, 255, 80), font=font)
        result = Image.alpha_composite(img, overlay).convert('RGB')
        buf = io.BytesIO()
        result.save(buf, format='PNG')
        buf.seek(0)
        return ContentFile(buf.read(), name='watermarked.png')
    except Exception as e:
        logger.error(f"add_watermark_to_image failed: {e}")
        raise

def remove_background(file_obj):
    try:
        from rembg import remove
        img = Image.open(file_obj)
        result = remove(img)
        buf = io.BytesIO()
        result.save(buf, format='PNG')
        buf.seek(0)
        return ContentFile(buf.read(), name='no_bg.png')
    except Exception as e:
        logger.error(f"remove_background failed: {e}")
        raise
```

---

## 12. Document Tools Module

### `document_tools/services.py`

```python
import io, logging
from django.core.files.base import ContentFile

logger = logging.getLogger('unitools')

def extract_text_ocr(file_obj):
    """Extract text from image using Tesseract OCR."""
    try:
        from PIL import Image
        import pytesseract
        img = Image.open(file_obj)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        raise

def summarize_text(text, max_length=200):
    """Summarize text using HuggingFace transformers."""
    try:
        from transformers import pipeline
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        summary = summarizer(text[:1024], max_length=max_length, min_length=30, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise

def translate_text(text, dest_lang='es'):
    """Translate text using googletrans."""
    try:
        from googletrans import Translator
        translator = Translator()
        result = translator.translate(text, dest=dest_lang)
        return result.text
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise

def compare_documents(file1, file2):
    """Compare two text documents and return differences."""
    try:
        import difflib
        text1 = file1.read().decode('utf-8', errors='replace').splitlines()
        text2 = file2.read().decode('utf-8', errors='replace').splitlines()
        diff = difflib.HtmlDiff().make_file(text1, text2,
                                            fromdesc='Document 1', todesc='Document 2')
        return diff
    except Exception as e:
        logger.error(f"Document comparison failed: {e}")
        raise

def docx_to_pdf(file_obj):
    """Convert DOCX to PDF using python-docx + reportlab."""
    try:
        from docx import Document
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet

        doc = Document(file_obj)
        buf = io.BytesIO()
        pdf = SimpleDocTemplate(buf, pagesize=letter)
        styles = getSampleStyleSheet()
        story = [Paragraph(p.text, styles['Normal']) for p in doc.paragraphs if p.text.strip()]
        pdf.build(story)
        buf.seek(0)
        return ContentFile(buf.read(), name='converted.pdf')
    except Exception as e:
        logger.error(f"DOCX→PDF conversion failed: {e}")
        raise
```

---

## 13. User Authentication

### `accounts/forms.py`

```python
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
```

### `accounts/views.py`

```python
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import RegisterForm

logger = logging.getLogger('unitools')

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('core:home')
        else:
            logger.error(f"Registration errors: {form.errors}")
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('core:home')
        else:
            logger.error(f"Failed login attempt for: {username}")
            messages.error(request, 'Invalid credentials.')
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('core:home')
```

### `accounts/urls.py`

```python
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
```

---

## 14. Error Logging System

All errors are captured and stored in **`errors.log`** at the project root.

### How It Works

1. **Django LOGGING config** (in `settings.py`) sends all `ERROR`+ level logs to `errors.log`
2. **`@handle_tool_errors` decorator** (in `core/utils.py`) wraps every tool view:
   - Catches any unhandled exception
   - Logs the full traceback to `errors.log`
   - Returns a user-friendly error page or JSON response
3. **Every service function** uses `logger.error(...)` in its `except` block

### Log Format

```
[2026-03-16 14:30:00] ERROR unitools services:42 → merge_pdfs failed: invalid PDF header
Traceback (most recent call last):
  File "pdf_tools/services.py", line 10, in merge_pdfs
    merger.append(f)
  ...
```

### Management Command to View Errors

Create `core/management/commands/show_errors.py`:

```python
from django.core.management.base import BaseCommand
from pathlib import Path

class Command(BaseCommand):
    help = 'Display recent entries from errors.log'

    def add_arguments(self, parser):
        parser.add_arguments('-n', '--lines', type=int, default=50)

    def handle(self, *args, **options):
        log_path = Path(__file__).resolve().parents[4] / 'errors.log'
        if not log_path.exists():
            self.stdout.write('No errors.log found.')
            return
        lines = log_path.read_text().splitlines()
        for line in lines[-options['lines']:]:
            self.stdout.write(line)
```

```bash
python manage.py show_errors -n 20
```

---

## 15. Deployment

### Step-by-Step Deployment Checklist

```bash
# 1. Set environment variables
set SECRET_KEY=<random-secret>
set DEBUG=False
set ALLOWED_HOSTS=yourdomain.com
set DATABASE_URL=postgres://user:pass@host:5432/unitools

# 2. Install production server
pip install gunicorn

# 3. Collect static files
python manage.py collectstatic --noinput

# 4. Run migrations
python manage.py migrate

# 5. Start Gunicorn
gunicorn unitools.wsgi:application --bind 0.0.0.0:8000 --workers 3

# 6. Start Celery worker (separate terminal)
celery -A unitools worker --loglevel=info

# 7. For production, use Nginx as reverse proxy + SSL via Let's Encrypt
```

---

## Quick Start Summary

```bash
# Clone & setup
git clone <repo-url> && cd unitools
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt

# Initialize
python manage.py makemigrations accounts core
python manage.py migrate
python manage.py createsuperuser

# Run
python manage.py runserver

# Visit http://127.0.0.1:8000
```

---

> **All errors and debug information are automatically captured in `errors.log`.**
> Use `python manage.py show_errors` to review recent issues.
