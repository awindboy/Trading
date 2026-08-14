from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from typing import Any


@dataclass(frozen=True)
class CodexResponse:
    payload: dict[str, Any]
    usage: dict[str, int]
    model: str


class CodexReplayError(RuntimeError):
    @staticmethod
    def retryable(error: BaseException) -> bool:
        """Identify provider pauses that happen before a decision is accepted."""
        message = str(error).lower()
        return any(
            marker in message
            for marker in (
                "you've hit your usage limit",
                "you have hit your usage limit",
                "usage limit",
                "timed out after",
            )
        )


def generate_codex_decision(
    *,
    request_dir: Path,
    prompt: str,
    images: list[Path],
    schema: dict[str, Any],
    model: str | None = None,
    reasoning_effort: str = "xhigh",
    timeout_seconds: int = 1800,
) -> CodexResponse:
    """Run an isolated Codex judgment over the exact replay packet.

    The working directory contains only the request artifacts needed for this
    stage. The prompt explicitly forbids workspace lookup and the run is
    read-only, so the frozen truth CSV is not an input to the judgment.
    """
    request_dir.mkdir(parents=True, exist_ok=True)
    schema_path = request_dir / "codex_response_schema.json"
    output_path = request_dir / "codex_decision.json"
    stdout_path = request_dir / "codex_stdout.txt"
    schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
    guarded_prompt = (
        "You are the isolated decision provider for a future-blind replay. "
        "Use only the supplied prompt and attached images. Do not inspect the "
        "workspace, truth files, previous runs, or any other files. Do not use "
        "tools. Return only the JSON required by the response schema.\n\n"
        + prompt
    )
    arguments = [
        "exec", "-c", f"model_reasoning_effort={reasoning_effort}",
        "--skip-git-repo-check", "--sandbox", "read-only",
        "--color", "never", "-C", str(request_dir),
        "--output-schema", str(schema_path), "-o", str(output_path),
    ]
    if model:
        arguments.extend(["--model", model])
    for image in images:
        arguments.extend(["--image", str(image)])
    arguments.append("-")
    if os.name == "nt":
        # PATHEXT resolution can select npm's extensionless POSIX shim first,
        # which CreateProcess rejects with WinError 5. Invoke the Windows npm
        # launcher explicitly through cmd.exe.
        launcher = shutil.which("codex.cmd")
        if not launcher:
            raise CodexReplayError("codex.cmd was not found on PATH")
        command = [
            os.environ.get("COMSPEC", "cmd.exe"),
            "/d",
            "/s",
            "/c",
            subprocess.list2cmdline([launcher, *arguments]),
        ]
    else:
        launcher = shutil.which("codex")
        if not launcher:
            raise CodexReplayError("codex was not found on PATH")
        command = [launcher, *arguments]
    request_label = request_dir.name[:12]
    started = time.monotonic()
    print(
        f"[SOL START] request={request_label} model={model or 'codex-cli-default'} "
        f"reasoning={reasoning_effort} timeout={timeout_seconds}s",
        flush=True,
    )
    with stdout_path.open("w", encoding="utf-8", errors="replace") as output_handle:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=output_handle,
            stderr=subprocess.STDOUT,
        )
        assert process.stdin is not None
        process.stdin.write(guarded_prompt)
        process.stdin.close()
        next_heartbeat = 10.0
        while process.poll() is None:
            elapsed = time.monotonic() - started
            if elapsed >= timeout_seconds:
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
                else:
                    process.kill()
                process.wait(timeout=10)
                raise CodexReplayError(
                    f"Codex CLI timed out after {timeout_seconds}s (request={request_label})"
                )
            if elapsed >= next_heartbeat:
                output_handle.flush()
                size = stdout_path.stat().st_size if stdout_path.exists() else 0
                print(
                    f"[SOL WORKING] request={request_label} elapsed={int(elapsed)}s "
                    f"log={size}B",
                    flush=True,
                )
                next_heartbeat += 10.0
            time.sleep(0.5)
        returncode = int(process.returncode or 0)
    elapsed = time.monotonic() - started
    stdout = stdout_path.read_text(encoding="utf-8", errors="replace") if stdout_path.exists() else ""
    print(
        f"[SOL DONE] request={request_label} elapsed={elapsed:.1f}s exit={returncode}",
        flush=True,
    )
    if returncode != 0:
        raise CodexReplayError(
            f"Codex CLI exited {returncode}: "
            f"{stdout[-1000:]}"
        )
    if not output_path.exists():
        raise CodexReplayError("Codex CLI completed without a structured decision")
    try:
        payload = json.loads(output_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise CodexReplayError(f"Codex output is not valid JSON: {exc}") from exc
    prompt_bytes = len(guarded_prompt.encode("utf-8"))
    output_bytes = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    usage = {
        "promptTokenCount": (prompt_bytes + 3) // 4,
        "candidatesTokenCount": (output_bytes + 3) // 4,
        "totalTokenCount": (prompt_bytes + output_bytes + 3) // 4,
    }
    return CodexResponse(payload=payload, usage=usage, model=model or "codex-cli")
