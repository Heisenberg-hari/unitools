from django.http import FileResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from core.utils import handle_tool_errors, record_operation
from . import services


def index(request):
    tools = [
        {"name": "Merge PDF", "desc": "Combine PDFs in seconds.", "icon": "bi-files", "url": "pdf_tools:merge", "live": True},
        {"name": "Split PDF", "desc": "Extract a custom page range.", "icon": "bi-scissors", "url": "pdf_tools:split", "live": True},
        {"name": "Compress PDF", "desc": "Reduce file size quickly.", "icon": "bi-file-zip", "url": "pdf_tools:compress", "live": True},
        {"name": "Rotate PDF", "desc": "Rotate all pages together.", "icon": "bi-arrow-clockwise", "url": "pdf_tools:rotate", "live": True},
        {"name": "Watermark PDF", "desc": "Add text mark to each page.", "icon": "bi-droplet-half", "url": "pdf_tools:watermark", "live": True},
        {"name": "PDF to Word", "desc": "Convert for editing.", "icon": "bi-filetype-docx", "url": "pdf_tools:pdf_to_word", "live": True},
        {"name": "Word to PDF", "desc": "Export docs as PDF.", "icon": "bi-filetype-pdf", "url": "pdf_tools:word_to_pdf", "live": True},
    ]
    return render(request, "pdf_tools/index.html", {"tools": tools})


@handle_tool_errors
def merge_pdf(request):
    if request.method == "POST":
        files = request.FILES.getlist("files")
        if len(files) < 2:
            messages.error(request, "Upload at least two PDF files.")
            return redirect("pdf_tools:merge")
        try:
            result = services.merge_pdfs(files)
        except RuntimeError as exc:
            messages.error(request, str(exc))
            return redirect("pdf_tools:merge")
        record_operation(request.user, "merge_pdf", files)
        return FileResponse(result, as_attachment=True, filename="merged.pdf")
    return render(request, "pdf_tools/merge.html")


@handle_tool_errors
def compress_pdf(request):
    if request.method == "POST":
        file_obj = request.FILES.get("file")
        target_value = request.POST.get("target_size_value", "").strip()
        target_unit = request.POST.get("target_size_unit", "kb")
        target_bytes = None
        if target_value:
            factor = 1024 if target_unit == "kb" else 1024 * 1024
            target_bytes = int(float(target_value) * factor)
        try:
            result = services.compress_pdf(file_obj, target_bytes=target_bytes)
        except RuntimeError as exc:
            messages.error(request, str(exc))
            return redirect("pdf_tools:compress")
        record_operation(request.user, "compress_pdf", [file_obj])
        return FileResponse(result, as_attachment=True, filename=result.name)
    return render(request, "pdf_tools/compress.html")


@handle_tool_errors
def split_pdf(request):
    if request.method == "POST":
        file_obj = request.FILES.get("file")
        start_page = int(request.POST.get("start_page", 1))
        end_page = int(request.POST.get("end_page", start_page))
        try:
            result = services.split_pdf(file_obj, start_page=start_page, end_page=end_page)
        except RuntimeError as exc:
            messages.error(request, str(exc))
            return redirect("pdf_tools:split")
        record_operation(request.user, "split_pdf", [file_obj])
        return FileResponse(result, as_attachment=True, filename=result.name)
    return render(request, "pdf_tools/split.html")


@handle_tool_errors
def rotate_pdf(request):
    if request.method == "POST":
        file_obj = request.FILES.get("file")
        degrees = int(request.POST.get("degrees", 90))
        try:
            result = services.rotate_pdf(file_obj, degrees=degrees)
        except RuntimeError as exc:
            messages.error(request, str(exc))
            return redirect("pdf_tools:rotate")
        record_operation(request.user, "rotate_pdf", [file_obj])
        return FileResponse(result, as_attachment=True, filename=result.name)
    return render(request, "pdf_tools/rotate.html")


@handle_tool_errors
def watermark_pdf(request):
    if request.method == "POST":
        file_obj = request.FILES.get("file")
        watermark_text = request.POST.get("watermark_text", "CONFIDENTIAL")
        try:
            result = services.add_watermark(file_obj, watermark_text=watermark_text)
        except RuntimeError as exc:
            messages.error(request, str(exc))
            return redirect("pdf_tools:watermark")
        record_operation(request.user, "watermark_pdf", [file_obj])
        return FileResponse(result, as_attachment=True, filename="watermarked.pdf")
    return render(request, "pdf_tools/watermark.html")


@handle_tool_errors
def pdf_to_word(request):
    if request.method == "POST":
        file_obj = request.FILES.get("file")
        try:
            result = services.pdf_to_word(file_obj)
        except RuntimeError as exc:
            messages.error(request, str(exc))
            return redirect("pdf_tools:pdf_to_word")
        record_operation(request.user, "pdf_to_word", [file_obj])
        return FileResponse(result, as_attachment=True, filename="converted.docx")
    return render(request, "pdf_tools/pdf_to_word.html")


@handle_tool_errors
def word_to_pdf(request):
    if request.method == "POST":
        file_obj = request.FILES.get("file")
        try:
            result = services.word_to_pdf(file_obj)
        except RuntimeError as exc:
            messages.error(request, str(exc))
            return redirect("pdf_tools:word_to_pdf")
        record_operation(request.user, "word_to_pdf", [file_obj])
        return FileResponse(result, as_attachment=True, filename="converted.pdf")
    return render(request, "pdf_tools/word_to_pdf.html")
