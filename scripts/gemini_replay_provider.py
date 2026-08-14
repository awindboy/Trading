from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class GeminiResponse:
    payload: dict[str, Any]
    usage: dict[str, int]
    model: str


class GeminiReplayError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        usage: dict[str, int] | None = None,
        request_was_sent: bool = False,
        provider_call_count: int = 0,
        recoverable: bool = False,
    ) -> None:
        super().__init__(message)
        self.usage = usage or {
            "promptTokenCount": 0,
            "candidatesTokenCount": 0,
            "totalTokenCount": 0,
        }
        self.request_was_sent = request_was_sent
        self.provider_call_count = provider_call_count or (1 if request_was_sent else 0)
        self.recoverable = recoverable


def _usage(raw: dict[str, Any]) -> dict[str, int]:
    usage_raw = raw.get("usageMetadata", {})
    details = {
        str(item.get("modality", "UNKNOWN")): int(item.get("tokenCount", 0) or 0)
        for item in usage_raw.get("promptTokensDetails", [])
        if isinstance(item, dict)
    }
    return {
        "promptTokenCount": int(usage_raw.get("promptTokenCount", 0) or 0),
        "promptTextTokenCount": details.get("TEXT", 0),
        "promptImageTokenCount": details.get("IMAGE", 0),
        "candidatesTokenCount": int(usage_raw.get("candidatesTokenCount", 0) or 0),
        "thoughtsTokenCount": int(usage_raw.get("thoughtsTokenCount", 0) or 0),
        "cachedContentTokenCount": int(
            usage_raw.get("cachedContentTokenCount", 0) or 0
        ),
        "totalTokenCount": int(usage_raw.get("totalTokenCount", 0) or 0),
    }


def _decode_json_text(text: str) -> dict[str, Any] | None:
    value = text.strip()
    attempts = [value]
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", value, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        attempts.append(fenced.group(1).strip())
    opening = value.find("{")
    if opening >= 0:
        attempts.append(value[opening:])
    for candidate in attempts:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            try:
                payload, _ = json.JSONDecoder().raw_decode(candidate)
            except json.JSONDecodeError:
                continue
        if isinstance(payload, dict):
            return payload
    return None


def extract_structured_payload(raw: dict[str, Any]) -> dict[str, Any]:
    candidates = raw.get("candidates", [])
    if not candidates:
        raise KeyError("response contains no candidates")
    parts = candidates[0].get("content", {}).get("parts", [])
    non_thought = [
        str(part["text"])
        for part in parts
        if isinstance(part, dict) and "text" in part and not bool(part.get("thought", False))
    ]
    all_text = [
        str(part["text"])
        for part in parts
        if isinstance(part, dict) and "text" in part
    ]
    attempts = [*non_thought, "\n".join(non_thought), *all_text, "\n".join(all_text)]
    for text in attempts:
        payload = _decode_json_text(text)
        if payload is not None:
            return payload
    raise ValueError("no content part contained a JSON object")


def _image_part(path: Path, media_resolution: str) -> dict[str, Any]:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return {
        "inlineData": {
            "mimeType": mime,
            "data": base64.b64encode(path.read_bytes()).decode("ascii"),
        },
        "mediaResolution": {"level": media_resolution},
    }


def build_generate_content_body(
    *,
    prompt: str,
    images: list[Path],
    media_resolutions: list[str],
    schema: dict[str, Any],
    temperature: float,
    max_output_tokens: int,
    thinking_level: str | None = None,
    system_instruction: str | None = None,
) -> dict[str, Any]:
    if len(media_resolutions) != len(images):
        raise GeminiReplayError("media resolution count does not match image count")
    parts: list[dict[str, Any]] = [{"text": prompt}]
    parts.extend(
        _image_part(path, resolution)
        for path, resolution in zip(images, media_resolutions)
    )
    body: dict[str, Any] = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_output_tokens,
            "responseMimeType": "application/json",
            "responseJsonSchema": schema,
        },
    }
    if thinking_level is not None:
        normalized = thinking_level.strip().lower()
        if normalized not in {"minimal", "low", "medium", "high"}:
            raise GeminiReplayError(
                "Gemini thinking level must be minimal, low, medium, or high"
            )
        body["generationConfig"]["thinkingConfig"] = {
            "thinkingLevel": normalized
        }
    if system_instruction is not None:
        if not system_instruction.strip():
            raise GeminiReplayError("Gemini system instruction is empty")
        body["systemInstruction"] = {"parts": [{"text": system_instruction}]}
    return body


def generate_structured_decision(
    *,
    api_key: str,
    model: str,
    prompt: str,
    system_instruction: str | None = None,
    images: list[Path],
    media_resolutions: list[str] | None = None,
    schema: dict[str, Any],
    temperature: float = 0.1,
    max_output_tokens: int = 4096,
    thinking_level: str | None = None,
    timeout_seconds: int = 120,
    raw_response_path: Path | None = None,
) -> GeminiResponse:
    if not api_key.strip():
        raise GeminiReplayError("Gemini API key is empty")
    resolutions = media_resolutions or ["MEDIA_RESOLUTION_HIGH"] * len(images)
    body = build_generate_content_body(
        prompt=prompt,
        system_instruction=system_instruction,
        images=images,
        media_resolutions=resolutions,
        schema=schema,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        thinking_level=thinking_level,
    )
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{quote(model, safe='')}:generateContent?key={quote(api_key, safe='')}"
    )
    request = Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise GeminiReplayError(
            f"Gemini HTTP {exc.code}: {detail}", request_was_sent=True
        ) from exc
    except (URLError, TimeoutError) as exc:
        raise GeminiReplayError(
            f"Gemini request failed: {exc}", request_was_sent=True
        ) from exc

    if raw_response_path is not None:
        raw_response_path.parent.mkdir(parents=True, exist_ok=True)
        raw_response_path.write_text(
            json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    candidates = raw.get("candidates", [])
    usage = _usage(raw)
    if not candidates:
        raise GeminiReplayError(
            f"Gemini returned no candidate: {json.dumps(raw)[:1000]}",
            usage=usage,
            request_was_sent=True,
            recoverable=True,
        )
    try:
        payload = extract_structured_payload(raw)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        finish_reason = candidates[0].get("finishReason", "UNKNOWN")
        part_kinds = [
            "thought-text" if part.get("thought") and "text" in part else (
                "text" if "text" in part else "+".join(sorted(part))
            )
            for part in candidates[0].get("content", {}).get("parts", [])
            if isinstance(part, dict)
        ]
        raise GeminiReplayError(
            "Gemini response contained no parseable structured JSON "
            f"(finishReason={finish_reason}, parts={part_kinds})",
            usage=usage,
            request_was_sent=True,
            recoverable=True,
        ) from exc
    return GeminiResponse(payload=payload, usage=usage, model=model)
