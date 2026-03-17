import logging
from functools import wraps
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect

logger = logging.getLogger("unitools")


def handle_tool_errors(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as exc:
            logger.exception("Unhandled tool error in %s: %s", view_func.__name__, exc)
            if request.headers.get("content-type", "").startswith("application/json"):
                return JsonResponse({"error": "Processing failed. Check errors.log."}, status=500)
            messages.error(request, "Something went wrong while processing your request.")
            return redirect("core:home")

    return wrapper


def detect_file_type(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "pdf":
        return "pdf"
    if ext in ("png", "jpg", "jpeg", "webp", "bmp", "gif"):
        return "image"
    return "document"


def record_operation(user, tool_name, files=None, status="completed"):
    if not getattr(user, "is_authenticated", False):
        return
    from .models import Operation, UploadedFile
    from .firebase_audit import log_operation_event

    files = files or []
    file_names = []
    total_size = 0
    for file_obj in files:
        if not file_obj:
            continue
        file_name = getattr(file_obj, "name", "unknown")
        size = int(getattr(file_obj, "size", 0) or 0)
        file_names.append(file_name)
        total_size += size
        UploadedFile.objects.create(
            user=user,
            original_name=file_name,
            file_type=detect_file_type(file_name),
            file_size=size,
            is_temp=True,
        )
    operation = Operation.objects.create(
        user=user,
        tool_name=tool_name,
        file_names=", ".join(file_names),
        total_file_size=total_size,
        status=status,
    )
    log_operation_event(operation, user)
