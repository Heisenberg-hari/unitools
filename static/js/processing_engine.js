// Minimal client-side processing helpers based on unifile.md.
export async function logOperationToServer(toolName, fileName, fileSize) {
  try {
    await fetch("/api/log-operation/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken(),
      },
      body: JSON.stringify({
        tool_name: toolName,
        file_name: fileName,
        file_size: fileSize,
      }),
    });
  } catch (err) {
    console.warn("metadata log failed:", err);
  }
}

function getCSRFToken() {
  return document.cookie.match(/csrftoken=([^;]+)/)?.[1] || "";
}

