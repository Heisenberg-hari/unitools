import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, JsonResponse
from django.shortcuts import render
from core.utils import handle_tool_errors, record_operation
from .services import (
    summarize_text,
    compare_text,
    extract_text_from_upload,
    translate_text,
    analyze_text,
    docx_to_pdf,
)

LANGUAGE_CHOICES = [
    ("ar", "Arabic"), ("bn", "Bengali"), ("zh-cn", "Chinese (Simplified)"), ("zh-tw", "Chinese (Traditional)"),
    ("cs", "Czech"), ("da", "Danish"), ("nl", "Dutch"), ("en", "English"), ("fi", "Finnish"), ("fr", "French"),
    ("de", "German"), ("el", "Greek"), ("gu", "Gujarati"), ("he", "Hebrew"), ("hi", "Hindi"), ("hu", "Hungarian"),
    ("id", "Indonesian"), ("it", "Italian"), ("ja", "Japanese"), ("kn", "Kannada"), ("ko", "Korean"),
    ("ml", "Malayalam"), ("mr", "Marathi"), ("no", "Norwegian"), ("fa", "Persian"), ("pl", "Polish"),
    ("pt", "Portuguese"), ("pa", "Punjabi"), ("ru", "Russian"), ("es", "Spanish"), ("sv", "Swedish"),
    ("ta", "Tamil"), ("te", "Telugu"), ("th", "Thai"), ("tr", "Turkish"), ("uk", "Ukrainian"), ("ur", "Urdu"),
    ("vi", "Vietnamese"),
]


def index(request):
    tools = [
        {"name": "Summarize Text", "desc": "Generate concise summary.", "icon": "bi-text-paragraph", "url": "document_tools:summarize_page", "live": True},
        {"name": "Compare Documents", "desc": "Spot changes quickly.", "icon": "bi-columns-gap", "url": "document_tools:compare", "live": True},
        {"name": "Translate Text", "desc": "Multi-language workflow.", "icon": "bi-translate", "url": "document_tools:translate", "live": True},
        {"name": "Text Analyzer", "desc": "Get readability and word insights.", "icon": "bi-graph-up", "url": "document_tools:analyze", "live": True},
        {"name": "DOCX to PDF", "desc": "Export office docs.", "icon": "bi-filetype-pdf", "url": "document_tools:docx_to_pdf", "live": True},
    ]
    return render(request, "document_tools/index.html", {"tools": tools})


@handle_tool_errors
@login_required
def summarize_text_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    data = json.loads(request.body or "{}")
    text = data.get("text", "")
    return JsonResponse({"summary": summarize_text(text)})


@handle_tool_errors
@login_required
def summarize_page(request):
    output = None
    source_name = None
    if request.method == "POST":
        upload = request.FILES.get("file")
        text = request.POST.get("text", "")
        used_files = []
        if upload:
            text = extract_text_from_upload(upload)
            source_name = upload.name
            used_files = [upload]
        output = summarize_text(text, max_length=2200) if text.strip() else ""
        if text.strip():
            record_operation(request.user, "summarize_text", used_files)
    return render(request, "document_tools/summarize.html", {"output": output, "source_name": source_name})


@handle_tool_errors
@login_required
def compare_page(request):
    diff_output = None
    explanation = None
    source_names = None
    if request.method == "POST":
        left_file = request.FILES.get("left_file")
        right_file = request.FILES.get("right_file")
        left = request.POST.get("left_text", "")
        right = request.POST.get("right_text", "")
        used_files = []
        if left_file:
            left = extract_text_from_upload(left_file)
            used_files.append(left_file)
        if right_file:
            right = extract_text_from_upload(right_file)
            used_files.append(right_file)
        if used_files:
            source_names = ", ".join(f.name for f in used_files)
        compared = compare_text(left, right)
        diff_output = compared.get("diff", "")
        explanation = compared.get("explanation", "")
        if left.strip() or right.strip():
            record_operation(request.user, "compare_documents", used_files)
    return render(
        request,
        "document_tools/compare.html",
        {"diff_output": diff_output, "source_names": source_names, "explanation": explanation},
    )


@handle_tool_errors
@login_required
def translate_page(request):
    output = None
    selected_lang = "es"
    if request.method == "POST":
        text = request.POST.get("text", "")
        target_lang = request.POST.get("target_lang", "es")
        selected_lang = target_lang
        used_files = []
        if request.FILES.get("file"):
            file_obj = request.FILES["file"]
            text = extract_text_from_upload(file_obj)
            used_files = [file_obj]
        output = translate_text(text, target_lang=target_lang) if text.strip() else ""
        if text.strip():
            record_operation(request.user, "translate_text", used_files)
    return render(
        request,
        "document_tools/translate.html",
        {"output": output, "languages": LANGUAGE_CHOICES, "selected_lang": selected_lang},
    )


@handle_tool_errors
@login_required
def analyze_page(request):
    analysis = None
    source_name = None
    text_input = ""
    if request.method == "POST":
        text_input = request.POST.get("text", "")
        file_obj = request.FILES.get("file")
        if file_obj:
            text_input = extract_text_from_upload(file_obj)
            source_name = file_obj.name
            record_operation(request.user, "analyze_text", [file_obj])
        elif text_input.strip():
            record_operation(request.user, "analyze_text", [])
        analysis = analyze_text(text_input) if text_input.strip() else None
    return render(
        request,
        "document_tools/analyze.html",
        {"analysis": analysis, "source_name": source_name, "text_input": text_input},
    )


@handle_tool_errors
@login_required
def docx_to_pdf_page(request):
    if request.method == "POST":
        file_obj = request.FILES.get("file")
        if not file_obj:
            messages.error(request, "Upload a DOCX file.")
            return render(request, "document_tools/docx_to_pdf.html")
        pdf_buffer = docx_to_pdf(file_obj)
        record_operation(request.user, "docx_to_pdf", [file_obj])
        return FileResponse(pdf_buffer, as_attachment=True, filename="converted.pdf")
    return render(request, "document_tools/docx_to_pdf.html")
