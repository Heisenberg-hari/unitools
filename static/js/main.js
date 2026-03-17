document.addEventListener("DOMContentLoaded", () => {
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

