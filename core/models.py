from django.conf import settings
from django.db import models


class UploadedFile(models.Model):
    FILE_TYPES = (
        ("pdf", "PDF"),
        ("image", "Image"),
        ("document", "Document"),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    original_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES, default="document")
    file_size = models.BigIntegerField(default=0)
    is_temp = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_name


class Operation(models.Model):
    STATUS_CHOICES = (
        ("completed", "Completed"),
        ("failed", "Failed"),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tool_name = models.CharField(max_length=100)
    file_names = models.TextField(blank=True, default="")
    total_file_size = models.BigIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="completed")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tool_name} ({self.status})"
