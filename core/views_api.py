import json
import logging
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from .models import Operation, UploadedFile
from .utils import detect_file_type
from .firebase_audit import log_operation_event

logger = logging.getLogger("unitools")


@require_POST
@csrf_protect
@login_required
def log_operation(request):
    try:
        data = json.loads(request.body or "{}")
        filename = data.get("file_name", "unknown")
        UploadedFile.objects.create(
            user=request.user,
            original_name=filename,
            file_type=detect_file_type(filename),
            file_size=int(data.get("file_size", 0) or 0),
            is_temp=True,
        )
        operation = Operation.objects.create(
            user=request.user,
            tool_name=data.get("tool_name", "unknown"),
            file_names=filename,
            total_file_size=int(data.get("file_size", 0) or 0),
            status="completed",
        )
        log_operation_event(operation, request.user)
        return JsonResponse({"status": "logged"})
    except Exception as exc:
        logger.exception("log_operation failed: %s", exc)
        return JsonResponse({"error": "Failed to log operation"}, status=500)
