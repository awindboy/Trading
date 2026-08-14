from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from typing import Any


DEFAULT_AI_PROVIDER = "gemini"
DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"
DEFAULT_GEMINI_TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class AiConfig:
    provider: str
    model: str
    api_key: str
    enabled: bool


def data_dir() -> Path:
    env_path = Path(__import__("os").environ.get("TRADING_JOURNAL_DATA_DIR", ""))
    if env_path:
        return env_path
    return Path(__file__).resolve().parents[1] / "data"


def config_path() -> Path:
    directory = data_dir()
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "ai_feedback_config.json"


def _normalize_provider(value: str) -> str:
    provider = str(value or "").strip().lower()
    if provider in {"gemini", "google", "google-gemini", "google gemini"}:
        return DEFAULT_AI_PROVIDER
    return DEFAULT_AI_PROVIDER if not provider else provider


def _default_config() -> AiConfig:
    return AiConfig(provider=DEFAULT_AI_PROVIDER, model=DEFAULT_GEMINI_MODEL, api_key="", enabled=True)


def read_ai_feedback_config() -> AiConfig:
    cfg = _default_config()
    env = __import__("os").environ
    file_path = config_path()

    if file_path.exists():
        try:
            raw = json.loads(file_path.read_text(encoding="utf-8-sig"))
            cfg = AiConfig(
                provider=_normalize_provider(str(raw.get("provider", cfg.provider)) if isinstance(raw, dict) else cfg.provider),
                model=str((raw.get("model") if isinstance(raw, dict) else cfg.model) or cfg.model).strip() or cfg.model,
                api_key=str((raw.get("apiKey") if isinstance(raw, dict) else cfg.api_key) or "").strip(),
                enabled=bool((raw.get("enabled") if isinstance(raw, dict) else cfg.enabled)),
            )
        except (OSError, json.JSONDecodeError):
            pass

    env_api_key = str(env.get("GEMINI_API_KEY") or env.get("GOOGLE_API_KEY") or "").strip()
    if env_api_key:
        cfg = AiConfig(provider=cfg.provider, model=cfg.model, api_key=env_api_key, enabled=cfg.enabled)

    if "AI_FEEDBACK_PROVIDER" in env:
        cfg = AiConfig(
            provider=_normalize_provider(env.get("AI_FEEDBACK_PROVIDER", cfg.provider)),
            model=cfg.model,
            api_key=cfg.api_key,
            enabled=cfg.enabled,
        )

    if "AI_FEEDBACK_MODEL" in env:
        cfg = AiConfig(
            provider=cfg.provider,
            model=str(env.get("AI_FEEDBACK_MODEL", cfg.model) or cfg.model).strip() or cfg.model,
            api_key=cfg.api_key,
            enabled=cfg.enabled,
        )

    if "AI_FEEDBACK_ENABLED" in env:
        cfg = AiConfig(
            provider=cfg.provider,
            model=cfg.model,
            api_key=cfg.api_key,
            enabled=str(env.get("AI_FEEDBACK_ENABLED", "") ).strip().lower() in {"1", "true", "yes", "on"},
        )

    return cfg


def write_ai_feedback_config(provider: str, model: str, api_key: str | None = None, enabled: bool = True) -> AiConfig:
    current = read_ai_feedback_config()
    next_key = current.api_key if api_key is None else str(api_key or "").strip()
    normalized = AiConfig(
        provider=_normalize_provider(provider),
        model=str(model or DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL,
        api_key=next_key,
        enabled=bool(enabled),
    )
    payload = {
        "provider": normalized.provider,
        "model": normalized.model,
        "apiKey": normalized.api_key,
        "enabled": normalized.enabled,
    }
    path = config_path()
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8-sig")
    return normalized


def ai_feedback_provider_payload() -> dict[str, Any]:
    cfg = read_ai_feedback_config()
    has_key = bool(cfg.api_key)
    return {
        "provider": cfg.provider,
        "model": cfg.model,
        "enabled": bool(cfg.enabled),
        "hasApiKey": has_key,
        "keyPreview": "****" + cfg.api_key[-4:] if has_key else "",
        "ready": bool(cfg.enabled) and cfg.provider == "gemini" and has_key,
        "message": "AI 분석은 Gemini + API key가 설정되면 활성화됩니다." if bool(cfg.enabled) else "AI 분석이 비활성화되어 로컬 결과만 생성됩니다.",
    }


def parse_ai_output(payload_text: str) -> dict[str, Any] | None:
    if not isinstance(payload_text, str):
        return None
    text = payload_text.strip()
    if not text:
        return None

    start = text.find("{")
    if start < 0:
        return None
    level = 0
    end = -1
    for index in range(start, len(text)):
        char = text[index]
        if char == "{":
            level += 1
        elif char == "}":
            level -= 1
            if level == 0:
                end = index
                break
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None

    return None


def generate_gemini_review(prompt: str, config: AiConfig | None = None, timeout: int = DEFAULT_GEMINI_TIMEOUT_SECONDS) -> dict[str, Any] | None:
    cfg = config or read_ai_feedback_config()
    if not cfg.enabled:
        return None
    if cfg.provider != "gemini":
        return None
    if not cfg.api_key:
        return None
    model = str(cfg.model or DEFAULT_GEMINI_MODEL)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={quote(cfg.api_key)}"
    body = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt,
                    }
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 1500,
        },
    }

    request = Request(url, method="POST")
    request.add_header("Content-Type", "application/json")
    request.data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError):
        return None

    try:
        data = json.loads(raw)
        candidates = data.get("candidates") if isinstance(data, dict) else []
        if not isinstance(candidates, list) or not candidates:
            return None
        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text") if isinstance(candidates[0], dict) else None
        if not isinstance(text, str) or not text.strip():
            return None
        parsed = parse_ai_output(text)
        if isinstance(parsed, dict):
            return parsed

        return {"verdict": text.strip(), "feedback": [text.strip()], "improvements": [], "nextRules": []}
    except (json.JSONDecodeError, TypeError, IndexError):
        return None
