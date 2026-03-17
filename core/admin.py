from django.contrib import admin
from .models import Operation, UploadedFile

admin.site.register(UploadedFile)
admin.site.register(Operation)

