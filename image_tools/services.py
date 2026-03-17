import io
import logging
import zipfile
from django.core.files.base import ContentFile

logger = logging.getLogger("unitools")


def _save_with_quality(img, fmt, quality):
    buf = io.BytesIO()
    save_kwargs = {"format": fmt}
    if fmt in ("JPEG", "WEBP"):
        save_kwargs["quality"] = quality
        save_kwargs["optimize"] = True
    img.save(buf, **save_kwargs)
    buf.seek(0)
    return buf


def compress_image(file_obj, quality=70, target_bytes=None):
    try:
        from PIL import Image

        img = Image.open(file_obj)
        fmt = img.format or "JPEG"
        if target_bytes and fmt in ("JPEG", "WEBP"):
            low, high = 10, 95
            best = _save_with_quality(img, fmt, quality)
            while low <= high:
                mid = (low + high) // 2
                candidate = _save_with_quality(img, fmt, mid)
                if candidate.getbuffer().nbytes <= target_bytes:
                    best = candidate
                    low = mid + 1
                else:
                    high = mid - 1
            buf = best
        else:
            buf = _save_with_quality(img, fmt, quality)
        return ContentFile(buf.read(), name=f"compressed.{fmt.lower()}")
    except Exception as exc:
        logger.exception("compress_image failed: %s", exc)
        raise


def convert_image_format(file_obj, target_format="png"):
    try:
        from PIL import Image

        img = Image.open(file_obj).convert("RGB")
        buf = io.BytesIO()
        fmt = target_format.upper()
        if fmt == "JPG":
            fmt = "JPEG"
        img.save(buf, format=fmt)
        buf.seek(0)
        ext = "jpg" if fmt == "JPEG" else target_format.lower()
        return ContentFile(buf.read(), name=f"converted.{ext}")
    except Exception as exc:
        logger.exception("convert_image_format failed: %s", exc)
        raise


def images_to_pdf(file_list):
    try:
        from PIL import Image

        images = []
        for file_obj in file_list:
            img = Image.open(file_obj).convert("RGB")
            images.append(img)
        if not images:
            raise RuntimeError("Upload at least one image.")
        buf = io.BytesIO()
        first, rest = images[0], images[1:]
        first.save(buf, format="PDF", save_all=True, append_images=rest)
        buf.seek(0)
        return ContentFile(buf.read(), name="images.pdf")
    except Exception as exc:
        logger.exception("images_to_pdf failed: %s", exc)
        raise


def resize_image(file_obj, width=1200, height=800):
    try:
        from PIL import Image

        img = Image.open(file_obj)
        resized = img.resize((width, height))
        buf = io.BytesIO()
        fmt = img.format or "PNG"
        resized.save(buf, format=fmt)
        buf.seek(0)
        return ContentFile(buf.read(), name=f"resized.{fmt.lower()}")
    except Exception as exc:
        logger.exception("resize_image failed: %s", exc)
        raise


def watermark_image(file_obj, watermark_text="UniTools"):
    try:
        from PIL import Image, ImageDraw, ImageFont

        image = Image.open(file_obj).convert("RGBA")
        overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        # Match PDF watermark behavior: large, centered, and diagonal.
        base_size = max(28, int(min(image.width, image.height) * 0.12))
        font = None
        for font_name in ("arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"):
            try:
                font = ImageFont.truetype(font_name, base_size)
                break
            except OSError:
                continue
        if font is None:
            font = ImageFont.load_default()

        text_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
        text_draw = ImageDraw.Draw(text_layer)
        bbox = text_draw.textbbox((0, 0), watermark_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        pos = ((image.width - text_w) // 2, (image.height - text_h) // 2)
        text_draw.text(pos, watermark_text, fill=(255, 255, 255, 90), font=font)

        rotated = text_layer.rotate(45, resample=Image.Resampling.BICUBIC, center=(image.width // 2, image.height // 2))
        overlay = Image.alpha_composite(overlay, rotated)
        out = Image.alpha_composite(image, overlay).convert("RGB")
        buf = io.BytesIO()
        out.save(buf, format="PNG")
        buf.seek(0)
        return ContentFile(buf.read(), name="watermarked.png")
    except Exception as exc:
        logger.exception("watermark_image failed: %s", exc)
        raise


def remove_background(file_obj):
    try:
        from PIL import Image, ImageFilter

        raw = file_obj.read()
        file_obj.seek(0)
        try:
            from rembg import remove

            result_bytes = remove(raw)
            out = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
            alpha = out.split()[-1].filter(ImageFilter.MedianFilter(size=3)).filter(ImageFilter.GaussianBlur(radius=0.8))
            out.putalpha(alpha)
        except (Exception, SystemExit) as rembg_exc:
            logger.warning("remove_background fallback active: %s", rembg_exc)
            # Fallback heuristic when rembg is unavailable or misconfigured.
            img = Image.open(io.BytesIO(raw)).convert("RGBA")
            px = img.load()
            w, h = img.size
            corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
            avg = tuple(sum(c[i] for c in corners) // 4 for i in range(3))
            tol = 35
            for y in range(h):
                for x in range(w):
                    r, g, b, a = px[x, y]
                    if abs(r - avg[0]) < tol and abs(g - avg[1]) < tol and abs(b - avg[2]) < tol:
                        px[x, y] = (r, g, b, 0)
            out = img.filter(ImageFilter.SMOOTH)
        buf = io.BytesIO()
        out.save(buf, format="PNG")
        buf.seek(0)
        return ContentFile(buf.read(), name="no_background.png")
    except Exception as exc:
        logger.exception("remove_background failed: %s", exc)
        raise


def batch_rename(files, prefix="image"):
    try:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for idx, file_obj in enumerate(files, start=1):
                name = getattr(file_obj, "name", f"file_{idx}")
                ext = name.rsplit(".", 1)[-1].lower() if "." in name else "bin"
                archive.writestr(f"{prefix}_{idx}.{ext}", file_obj.read())
                file_obj.seek(0)
        buf.seek(0)
        return buf
    except Exception as exc:
        logger.exception("batch_rename failed: %s", exc)
        raise
