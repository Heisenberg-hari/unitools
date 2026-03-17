document.addEventListener("DOMContentLoaded", () => {
  const MAX_UPLOAD_MB = 4;
  const MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024;

  const formatSize = (bytes) => {
    if (!Number.isFinite(bytes) || bytes <= 0) return "0 B";
    const units = ["B", "KB", "MB", "GB"];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex += 1;
    }
    return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
  };

  const ensureUploadNotice = (form) => {
    let notice = form.querySelector(".upload-limit-notice");
    if (notice) return notice;
    notice = document.createElement("div");
    notice.className = "alert alert-warning d-none upload-limit-notice";
    notice.setAttribute("role", "alert");
    form.prepend(notice);
    return notice;
  };

  const setNotice = (form, message) => {
    const notice = ensureUploadNotice(form);
    if (!message) {
      notice.classList.add("d-none");
      notice.textContent = "";
      return;
    }
    notice.textContent = message;
    notice.classList.remove("d-none");
  };

  const getFormFileStats = (form) => {
    const inputs = form.querySelectorAll('input[type="file"]');
    let total = 0;
    let count = 0;
    inputs.forEach((input) => {
      const files = Array.from(input.files || []);
      files.forEach((file) => {
        total += file.size || 0;
        count += 1;
      });
    });
    return { total, count };
  };

  const uploadForms = document.querySelectorAll('form[enctype="multipart/form-data"]');
  uploadForms.forEach((form) => {
    const fileInputs = form.querySelectorAll('input[type="file"]');
    fileInputs.forEach((input) => {
      input.addEventListener("change", () => {
        const { total, count } = getFormFileStats(form);
        if (!count) {
          setNotice(form, "");
          return;
        }
        if (total > MAX_UPLOAD_BYTES) {
          setNotice(
            form,
            `Upload too large (${formatSize(total)}). Vercel allows about ${MAX_UPLOAD_MB} MB per request. ` +
              "Try fewer/smaller files or compress before upload."
          );
          return;
        }
        setNotice(form, `Selected ${count} file(s): ${formatSize(total)} total.`);
      });
    });

    form.addEventListener("submit", (event) => {
      const { total, count } = getFormFileStats(form);
      if (!count) return;
      if (total > MAX_UPLOAD_BYTES) {
        event.preventDefault();
        setNotice(
          form,
          `Cannot submit ${formatSize(total)}. Max allowed is about ${MAX_UPLOAD_MB} MB per request on this deployment.`
        );
      }
    });
  });

  const zones = document.querySelectorAll(".drop-zone");
  zones.forEach((zone) => {
    const input = zone.querySelector('input[type="file"]');
    if (!input) return;
    zone.addEventListener("click", () => input.click());
    zone.addEventListener("dragover", (e) => {
      e.preventDefault();
      zone.classList.add("active");
    });
    zone.addEventListener("dragleave", () => zone.classList.remove("active"));
    zone.addEventListener("drop", (e) => {
      e.preventDefault();
      zone.classList.remove("active");
      input.files = e.dataTransfer.files;
      input.dispatchEvent(new Event("change"));
    });
  });
});
