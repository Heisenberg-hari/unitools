import json
import os
from pathlib import Path
from urllib import error, request


def _env(name, default=None):
    value = os.getenv(name)
    if value:
        return value
    env_file = Path(__file__).resolve().parents[1] / ".env"
    if not env_file.exists():
        return default
    try:
        for raw in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == name:
                return v.strip().strip('"').strip("'")
    except Exception:
        return default
    return default


def is_llm_enabled():
    return bool(_env("LLAMA_API_KEY"))


def call_llm(system_prompt, user_prompt, max_output_tokens=900):
    api_key = _env("LLAMA_API_KEY")
    if not api_key:
        raise RuntimeError("LLM is not configured. Set LLAMA_API_KEY.")

    base_url = _env("LLAMA_BASE_URL", "https://api.together.xyz/v1")
    model = _env("LLAMA_MODEL", "meta-llama/Llama-3.3-70B-Instruct-Turbo")
    endpoint = base_url.rstrip("/") + "/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": int(max_output_tokens),
    }

    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "UniTools/1.0",
            "HTTP-Referer": _env("LLAMA_HTTP_REFERER", "http://localhost:8000"),
            "X-Title": _env("LLAMA_APP_NAME", "UniTools"),
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        if exc.code == 403:
            if "openrouter.ai" in base_url:
                raise RuntimeError(
                    "Llama/OpenRouter forbidden (403/1010). Use an OpenRouter key (sk-or-v1-...), "
                    "set LLAMA_BASE_URL=https://openrouter.ai/api/v1, and verify model access."
                ) from exc
            raise RuntimeError(
                "Llama request forbidden (403/1010). Verify LLAMA_API_KEY, LLAMA_BASE_URL, "
                "and LLAMA_MODEL for your provider."
            ) from exc
        raise RuntimeError(f"Llama request failed: {detail}") from exc

    choices = body.get("choices", [])
    if not choices:
        return "No response generated."
    message = choices[0].get("message", {}) or {}
    text = (message.get("content", "") or "").strip()
    return text or "No response generated."
