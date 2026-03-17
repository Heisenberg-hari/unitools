from django.contrib import messages
from django.http import FileResponse, HttpResponse
from django.shortcuts import render, redirect
from core.utils import handle_tool_errors, record_operation
from .services import (
    compress_image,
    convert_image_format,
    images_to_pdf,
    resize_image,
    watermark_image,
    remove_background,
    batch_rename,
)


def index(request):
    tools = [
        {"name": "Compress Image", "desc": "Shrink JPG/PNG/WebP files.", "icon": "bi-file-earmark-zip", "url": "image_tools:compress", "live": True},
        {"name": "Convert Format", "desc": "PNG, JPG, WEBP conversion.", "icon": "bi-arrow-left-right", "url": "image_tools:convert", "live": True},
        {"name": "Resize Image", "desc": "Set exact width and height.", "icon": "bi-bounding-box", "url": "image_tools:resize", "live": True},
        {"name": "Watermark Image", "desc": "Brand your visuals.", "icon": "bi-brush", "url": "image_tools:watermark", "live": True},
        {"name": "Remove Background", "desc": "AI cutout workflow.", "icon": "bi-magic", "url": "image_tools:remove_bg", "live": True},
        {"name": "Batch Rename", "desc": "Rename many files fast.", "icon": "bi-input-cursor-text", "url": "image_tools:batch_rename", "live": True},
    ]
    return render(request, "image_tools/index.html", {"tools": tools})


@handle_tool_errors
def compress(request):
    if request.method == "POST":
        file_obj = request.FILES.get("file")
        quality = int(request.POST.get("quality", 70))
        target_value = request.POST.get("target_size_value", "").strip()
        target_unit = request.POST.get("target_size_unit", "kb")
        target_bytes = None
        if target_value:
            factor = 1024 if target_unit == "kb" else 1024 * 1024
            target_bytes = int(float(target_value) * factor)
        result = compress_image(file_obj, quality=quality, target_bytes=target_bytes)
        record_operation(request.user, "compress_image", [file_obj])
        return FileResponse(result, as_attachment=True, filename=result.name)
    return render(request, "image_tools/compress.html")


@handle_tool_errors
def convert(request):
    if request.method == "POST":
        files = request.FILES.getlist("files")
        if not files:
            messages.error(request, "Upload at least one image.")
            return redirect("image_tools:convert")
        target_format = request.POST.get("target_format", "png")
        if target_format == "pdf":
            result = images_to_pdf(files)
            record_operation(request.user, "images_to_pdf", files)
            return FileResponse(result, as_attachment=True, filename=result.name)
        file_obj = files[0] if files else None
        result = convert_image_format(file_obj, target_format=target_format)
        record_operation(request.user, "convert_image", [file_obj] if file_obj else [])
        return FileResponse(result, as_attachment=True, filename=result.name)
    return render(request, "image_tools/convert.html")


@handle_tool_errors
def resize(request):
    if request.method == "POST":
        file_obj = request.FILES.get("file")
        width = int(request.POST.get("width", 1200))
        height = int(request.POST.get("height", 800))
        result = resize_image(file_obj, width=width, height=height)
        record_operation(request.user, "resize_image", [file_obj])
        return FileResponse(result, as_attachment=True, filename=result.name)
    return render(request, "image_tools/resize.html")


@handle_tool_errors
def watermark(request):
    if request.method == "POST":
        file_obj = request.FILES.get("file")
        text = request.POST.get("text", "UniTools")
        result = watermark_image(file_obj, watermark_text=text)
        record_operation(request.user, "watermark_image", [file_obj])
        return FileResponse(result, as_attachment=True, filename=result.name)
    return render(request, "image_tools/watermark.html")


@handle_tool_errors
def remove_bg(request):
    if request.method == "POST":
        file_obj = request.FILES.get("file")
        try:
            result = remove_background(file_obj)
        except RuntimeError as exc:
            messages.error(request, str(exc))
            return redirect("image_tools:remove_bg")
        record_operation(request.user, "remove_background", [file_obj])
        return FileResponse(result, as_attachment=True, filename=result.name)
    return render(request, "image_tools/remove_bg.html")


@handle_tool_errors
def batch_rename(request):
    if request.method == "POST":
        files = request.FILES.getlist("files")
        prefix = request.POST.get("prefix", "image")
        bundle = batch_rename(files, prefix=prefix)
        record_operation(request.user, "batch_rename", files)
        response = HttpResponse(bundle.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = 'attachment; filename="renamed_images.zip"'
        return response
    return render(request, "image_tools/batch_rename.html")
