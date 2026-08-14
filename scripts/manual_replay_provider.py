from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError


@dataclass(frozen=True)
class ManualResponse:
    payload: dict[str, Any]
    usage: dict[str, int]
    model: str


class ManualReplayError(RuntimeError):
    pass


def wait_for_manual_decision(
    *,
    request_dir: Path,
    prompt: str,
    images: list[Path],
    response_schema: dict[str, Any] | None = None,
    timeout_seconds: int = 3600,
) -> ManualResponse:
    request_dir.mkdir(parents=True, exist_ok=True)
    decision_path = request_dir / "manual_decision.json"
    request_path = request_dir / "manual_request.json"
    prompt_path = request_dir / "prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8")
    request_payload = {
        "decisionPath": str(decision_path),
        "promptPath": str(prompt_path),
        "images": [str(path) for path in images],
        "promptCharacters": len(prompt),
        "promptUtf8Bytes": len(prompt.encode("utf-8")),
    }
    validator: Draft202012Validator | None = None
    if response_schema is not None:
        try:
            Draft202012Validator.check_schema(response_schema)
        except SchemaError as exc:
            raise ManualReplayError(f"invalid manual response schema: {exc.message}") from exc
        validator = Draft202012Validator(response_schema)
        request_payload["responseSchema"] = response_schema
    request_path.write_text(
        json.dumps(
            request_payload,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"[MANUAL CODEX WAIT] decision={decision_path}", flush=True)
    deadline = time.monotonic() + timeout_seconds
    last_invalid_text: str | None = None
    while time.monotonic() < deadline:
        if decision_path.exists():
            try:
                decision_text = decision_path.read_text(encoding="utf-8-sig")
                payload = json.loads(decision_text)
            except (OSError, json.JSONDecodeError):
                # OneDrive may expose the destination before a copy/replace has
                # released its write lock or completed the JSON body.
                time.sleep(0.25)
                continue
            if validator is not None:
                try:
                    validator.validate(payload)
                except ValidationError as exc:
                    if decision_text != last_invalid_text:
                        location = "/".join(str(part) for part in exc.absolute_path)
                        suffix = f" at {location}" if location else ""
                        print(
                            f"[MANUAL CODEX INVALID] {exc.message}{suffix}; "
                            "waiting for corrected manual_decision.json",
                            flush=True,
                        )
                        last_invalid_text = decision_text
                    time.sleep(0.25)
                    continue
            output_bytes = len(
                json.dumps(payload, ensure_ascii=False).encode("utf-8")
            )
            # This is a payload-size estimate, not Codex billing usage.
            usage = {
                "promptTokenCount": (len(prompt.encode("utf-8")) + 3) // 4,
                "candidatesTokenCount": (output_bytes + 3) // 4,
                "totalTokenCount": (len(prompt.encode("utf-8")) + output_bytes + 3) // 4,
            }
            return ManualResponse(payload=payload, usage=usage, model="manual-codex")
        time.sleep(0.25)
    raise ManualReplayError(f"manual decision timed out: {decision_path}")
