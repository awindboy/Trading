#!/usr/bin/env python3
"""Independent V10 Gemini replay for GOLD# January 2025.

This runner builds charts only from rows at or before an explicit cutoff and
asks Gemini for a V9-style discretionary decision. It never reads V9 replay
answers and has no broker or order-execution capability.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.gemini_replay_provider import GeminiReplayError, generate_structured_decision


SOURCE = ROOT / "GOLD#_M1_202201030100_202608282357.csv"
SOURCE_SHA256 = "626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2"
CONTRACT = ROOT / "docs" / "ea" / "v10" / "V10_GEMINI_BEHAVIOR_CONTRACT.md"
SECRET = ROOT / "data" / "mentor_ai_replay_secret.json"
OUTPUT_ROOT = ROOT / "output" / "v10_gemini_jan2025"
HISTORY_START = datetime(2024, 1, 1, 0, 0)
PERIOD_START = datetime(2025, 1, 2, 8, 0)
PERIOD_END = datetime(2025, 1, 31, 23, 57)
TS_FMT = "%Y-%m-%d %H:%M:%S"
SOURCE_TS_FMT = "%Y.%m.%d %H:%M:%S"
EXPECTED_HEADER = [
    "<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>",
    "<TICKVOL>", "<VOL>", "<SPREAD>",
]
FRAME_WINDOWS = {"D1": 270, "H4": 360, "H1": 336, "M15": 320, "M5": 300, "M1": 240}
FRAME_MINUTES = {"D1": 1440, "H4": 240, "H1": 60, "M15": 15, "M5": 5, "M1": 1}


class V10Error(RuntimeError):
    pass


@dataclass
class Bar:
    start: datetime
    open: float
    high: float
    low: float
    close: float


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def parse_cutoff(value: str) -> datetime:
    try:
        parsed = datetime.strptime(value, TS_FMT)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("cutoff must be YYYY-MM-DD HH:MM:SS") from exc
    if parsed < PERIOD_START or parsed > PERIOD_END:
        raise argparse.ArgumentTypeError(
            f"cutoff must stay inside {PERIOD_START:{TS_FMT}} through {PERIOD_END:{TS_FMT}}"
        )
    return parsed


def verify_source(path: Path, expected_sha256: str = SOURCE_SHA256) -> str:
    if not path.is_file():
        raise V10Error(f"source not found: {path}")
    actual = sha256_file(path)
    if actual.lower() != expected_sha256.lower():
        raise V10Error(f"source SHA256 mismatch: expected {expected_sha256}, got {actual}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        header = next(csv.reader(handle, delimiter="\t"), None)
    if header != EXPECTED_HEADER:
        raise V10Error("unexpected M1 source header")
    return actual


def load_revealed_m1(path: Path, cutoff: datetime) -> list[Bar]:
    rows: list[Bar] = []
    last_seen: datetime | None = None
    found_cutoff = False
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        header = next(reader, None)
        if header != EXPECTED_HEADER:
            raise V10Error("unexpected M1 source header")
        for row in reader:
            if len(row) != len(EXPECTED_HEADER):
                raise V10Error("malformed M1 row")
            timestamp = datetime.strptime(f"{row[0]} {row[1]}", SOURCE_TS_FMT)
            if last_seen is not None and timestamp <= last_seen:
                raise V10Error("M1 source is not strictly chronological")
            last_seen = timestamp
            if timestamp < HISTORY_START:
                continue
            if timestamp > cutoff:
                break
            rows.append(
                Bar(timestamp, float(row[2]), float(row[3]), float(row[4]), float(row[5]))
            )
            if timestamp == cutoff:
                found_cutoff = True
    if not found_cutoff:
        raise V10Error("exact cutoff row not found; refusing to round the causal boundary")
    if not rows or rows[-1].start != cutoff:
        raise V10Error("revealed data does not end exactly at cutoff")
    return rows


def parse_binary_m1(line: bytes) -> Bar:
    parts = line.rstrip(b"\r\n").split(b"\t")
    if len(parts) != len(EXPECTED_HEADER):
        raise V10Error("malformed M1 row")
    try:
        timestamp = datetime.strptime(
            f"{parts[0].decode('ascii')} {parts[1].decode('ascii')}", SOURCE_TS_FMT
        )
        return Bar(
            timestamp,
            float(parts[2]),
            float(parts[3]),
            float(parts[4]),
            float(parts[5]),
        )
    except (UnicodeDecodeError, ValueError) as exc:
        raise V10Error("malformed M1 row values") from exc


def bucket_start(timestamp: datetime, minutes: int) -> datetime:
    if minutes == 1440:
        return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
    if minutes == 240:
        return timestamp.replace(
            hour=(timestamp.hour // 4) * 4, minute=0, second=0, microsecond=0
        )
    if minutes == 60:
        return timestamp.replace(minute=0, second=0, microsecond=0)
    return timestamp.replace(
        minute=(timestamp.minute // minutes) * minutes, second=0, microsecond=0
    )


def aggregate(rows: Iterable[Bar], minutes: int) -> list[Bar]:
    result: list[Bar] = []
    current: Bar | None = None
    for row in rows:
        start = bucket_start(row.start, minutes)
        if current is None or current.start != start:
            if current is not None:
                result.append(current)
            current = Bar(start, row.open, row.high, row.low, row.close)
        else:
            current.high = max(current.high, row.high)
            current.low = min(current.low, row.low)
            current.close = row.close
    if current is not None:
        result.append(current)
    return result


def bar_to_json(bar: Bar) -> list[Any]:
    return [bar.start.strftime(TS_FMT), bar.open, bar.high, bar.low, bar.close]


def bar_from_json(value: list[Any]) -> Bar:
    if not isinstance(value, list) or len(value) != 5:
        raise V10Error("invalid cached bar")
    return Bar(datetime.strptime(value[0], TS_FMT), *map(float, value[1:]))


def empty_frames() -> dict[str, list[Bar]]:
    return {name: [] for name in FRAME_WINDOWS}


def update_frames(frames: dict[str, list[Bar]], row: Bar) -> None:
    for name, minutes in FRAME_MINUTES.items():
        bars = frames[name]
        start = row.start if minutes == 1 else bucket_start(row.start, minutes)
        if bars and bars[-1].start == start:
            current = bars[-1]
            current.high = max(current.high, row.high)
            current.low = min(current.low, row.low)
            current.close = row.close
        else:
            bars.append(Bar(start, row.open, row.high, row.low, row.close))
            overflow = len(bars) - FRAME_WINDOWS[name]
            if overflow > 0:
                del bars[:overflow]


def serialize_frames(frames: dict[str, list[Bar]]) -> dict[str, list[list[Any]]]:
    return {name: [bar_to_json(bar) for bar in frames[name]] for name in FRAME_WINDOWS}


def deserialize_frames(raw: dict[str, Any]) -> dict[str, list[Bar]]:
    if set(raw) != set(FRAME_WINDOWS):
        raise V10Error("cached timeframe set is invalid")
    return {name: [bar_from_json(value) for value in raw[name]] for name in FRAME_WINDOWS}


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def save_market_cache(
    path: Path,
    *,
    source: Path,
    source_sha256: str,
    cutoff: datetime,
    resume_offset: int,
    revealed_rows: int,
    revealed_first: datetime,
    frames: dict[str, list[Bar]],
) -> None:
    stat = source.stat()
    atomic_json(
        path,
        {
            "version": 1,
            "sourcePath": str(source.resolve()),
            "sourceSha256": source_sha256,
            "sourceSize": stat.st_size,
            "sourceMtimeNs": stat.st_mtime_ns,
            "historyStart": HISTORY_START.strftime(TS_FMT),
            "cutoff": cutoff.strftime(TS_FMT),
            "resumeOffset": resume_offset,
            "revealedRows": revealed_rows,
            "revealedFirst": revealed_first.strftime(TS_FMT),
            "frames": serialize_frames(frames),
        },
    )


def assert_cached_source(
    source: Path,
    cache: dict[str, Any],
    expected_sha256: str = SOURCE_SHA256,
) -> str:
    if str(source.resolve()) != cache.get("sourcePath"):
        raise V10Error("market cache source path changed")
    stat = source.stat()
    if stat.st_size != cache.get("sourceSize") or stat.st_mtime_ns != cache.get("sourceMtimeNs"):
        actual = verify_source(source, expected_sha256)
        if actual != cache.get("sourceSha256"):
            raise V10Error("market cache source changed")
    with source.open("rb") as handle:
        header = handle.readline().decode("utf-8-sig").rstrip("\r\n").split("\t")
    if header != EXPECTED_HEADER:
        raise V10Error("market cache source header changed")
    return str(cache["sourceSha256"])


def init_market_cache(
    source: Path,
    cutoff: datetime,
    cache_path: Path,
    expected_sha256: str = SOURCE_SHA256,
) -> tuple[dict[str, list[Bar]], dict[str, Any]]:
    source_sha = verify_source(source, expected_sha256)
    frames = empty_frames()
    revealed_rows = 0
    revealed_first: datetime | None = None
    previous: datetime | None = None
    found = False
    resume_offset = -1
    with source.open("rb") as handle:
        header = handle.readline().decode("utf-8-sig").rstrip("\r\n").split("\t")
        if header != EXPECTED_HEADER:
            raise V10Error("unexpected M1 source header")
        while line := handle.readline():
            row = parse_binary_m1(line)
            if row.start < HISTORY_START:
                continue
            if previous is not None and row.start <= previous:
                raise V10Error("M1 source is not strictly chronological")
            previous = row.start
            if row.start > cutoff:
                break
            if revealed_first is None:
                revealed_first = row.start
            update_frames(frames, row)
            revealed_rows += 1
            if row.start == cutoff:
                found = True
                resume_offset = handle.tell()
                break
    if not found or revealed_first is None:
        raise V10Error("exact cutoff row not found; refusing to initialize causal cache")
    save_market_cache(
        cache_path,
        source=source,
        source_sha256=source_sha,
        cutoff=cutoff,
        resume_offset=resume_offset,
        revealed_rows=revealed_rows,
        revealed_first=revealed_first,
        frames=frames,
    )
    return frames, json.loads(cache_path.read_text(encoding="utf-8"))


def load_or_advance_market_cache(
    source: Path,
    cutoff: datetime,
    cache_path: Path,
    expected_sha256: str = SOURCE_SHA256,
) -> tuple[dict[str, list[Bar]], dict[str, Any], str]:
    if not cache_path.is_file():
        frames, cache = init_market_cache(source, cutoff, cache_path, expected_sha256)
        return frames, cache, "initialized"
    cache = json.loads(cache_path.read_text(encoding="utf-8"))
    if cache.get("version") != 1 or cache.get("historyStart") != HISTORY_START.strftime(TS_FMT):
        raise V10Error("unsupported market cache")
    source_sha = assert_cached_source(source, cache, expected_sha256)
    cached_cutoff = datetime.strptime(cache["cutoff"], TS_FMT)
    if cutoff < cached_cutoff:
        raise V10Error("requested cutoff precedes the causal market cache")
    frames = deserialize_frames(cache["frames"])
    if cutoff == cached_cutoff:
        return frames, cache, "reused"

    previous = cached_cutoff
    revealed_rows = int(cache["revealedRows"])
    revealed_first = datetime.strptime(cache["revealedFirst"], TS_FMT)
    found = False
    resume_offset = int(cache["resumeOffset"])
    with source.open("rb") as handle:
        handle.seek(resume_offset)
        while line := handle.readline():
            row = parse_binary_m1(line)
            if row.start <= previous:
                raise V10Error("source chronology or cached byte offset mismatch")
            previous = row.start
            if row.start > cutoff:
                break
            update_frames(frames, row)
            revealed_rows += 1
            if row.start == cutoff:
                found = True
                resume_offset = handle.tell()
                break
    if not found:
        raise V10Error("exact cutoff row not found; causal cache was not advanced")
    save_market_cache(
        cache_path,
        source=source,
        source_sha256=source_sha,
        cutoff=cutoff,
        resume_offset=resume_offset,
        revealed_rows=revealed_rows,
        revealed_first=revealed_first,
        frames=frames,
    )
    cache = json.loads(cache_path.read_text(encoding="utf-8"))
    return frames, cache, "advanced"


@lru_cache(maxsize=None)
def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/malgunbd.ttf" if bold else "C:/Windows/Fonts/malgun.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def draw_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    bars: list[Bar],
    title: str,
    cutoff: datetime,
) -> None:
    left, top, right, bottom = box
    draw.rectangle(box, fill="#0b111b", outline="#334155", width=2)
    draw.text((left + 14, top + 10), f"{title}  |  AS-OF {cutoff:{TS_FMT}}", fill="#e2e8f0", font=_font(20, True))
    chart_left, chart_top = left + 72, top + 50
    chart_right, chart_bottom = right - 18, bottom - 42
    if not bars:
        draw.text((chart_left, chart_top), "NO DATA", fill="#f87171", font=_font(22, True))
        return
    low = min(bar.low for bar in bars)
    high = max(bar.high for bar in bars)
    span = max(high - low, 0.01)
    pad = span * 0.04
    low -= pad
    high += pad
    for level in range(5):
        y = chart_top + (chart_bottom - chart_top) * level / 4
        price = high - (high - low) * level / 4
        draw.line((chart_left, y, chart_right, y), fill="#253247", width=1)
        draw.text((left + 4, int(y) - 8), f"{price:.1f}", fill="#94a3b8", font=_font(13))
    width = max(chart_right - chart_left, 1)
    step = width / max(len(bars), 1)
    body_width = max(1, min(7, int(step * 0.65)))

    def price_y(price: float) -> int:
        return int(chart_top + (high - price) / (high - low) * (chart_bottom - chart_top))

    for index, bar in enumerate(bars):
        x = int(chart_left + (index + 0.5) * step)
        color = "#5eead4" if bar.close >= bar.open else "#f87171"
        draw.line((x, price_y(bar.high), x, price_y(bar.low)), fill=color, width=1)
        y1, y2 = price_y(bar.open), price_y(bar.close)
        if y1 == y2:
            draw.line((x - body_width // 2, y1, x + body_width // 2, y1), fill=color, width=2)
        else:
            draw.rectangle(
                (x - body_width // 2, min(y1, y2), x + body_width // 2, max(y1, y2)),
                fill=color,
            )
    label_indexes = sorted(set([0, len(bars) // 4, len(bars) // 2, 3 * len(bars) // 4, len(bars) - 1]))
    for index in label_indexes:
        x = int(chart_left + (index + 0.5) * step)
        label = bars[index].start.strftime("%m-%d\n%H:%M")
        draw.multiline_text((x - 25, chart_bottom + 6), label, fill="#94a3b8", font=_font(12), align="center")
    last = bars[-1]
    draw.text(
        (right - 430, top + 12),
        f"O {last.open:.2f}  H {last.high:.2f}  L {last.low:.2f}  C {last.close:.2f}",
        fill="#cbd5e1",
        font=_font(16),
    )


def render_pair(
    path: Path,
    top_name: str,
    top_bars: list[Bar],
    bottom_name: str,
    bottom_bars: list[Bar],
    cutoff: datetime,
) -> None:
    image = Image.new("RGB", (1800, 1200), "#070b12")
    draw = ImageDraw.Draw(image)
    draw_panel(draw, (20, 20, 1780, 590), top_bars, top_name, cutoff)
    draw_panel(draw, (20, 610, 1780, 1180), bottom_bars, bottom_name, cutoff)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True)


def render_packet(frames: dict[str, list[Bar]], cutoff: datetime, output_dir: Path) -> list[Path]:
    visible = {name: bars[-FRAME_WINDOWS[name]:] for name, bars in frames.items()}
    images = [
        output_dir / "01_parent_D1_H4.png",
        output_dir / "02_child_H1_M15.png",
        output_dir / "03_execution_M5_M1.png",
    ]
    render_pair(images[0], "D1 PARENT", visible["D1"], "H4 PARENT", visible["H4"], cutoff)
    render_pair(images[1], "H1 STRUCTURE", visible["H1"], "M15 CHILD", visible["M15"], cutoff)
    render_pair(images[2], "M5 LOCAL", visible["M5"], "M1 EXECUTION", visible["M1"], cutoff)
    return images


def recent_ohlc(frames: dict[str, list[Bar]], count: int = 8) -> str:
    sections: list[str] = []
    for name in ("D1", "H4", "H1", "M15", "M5", "M1"):
        sections.append(f"[{name} latest {count} bars]")
        for bar in frames[name][-count:]:
            sections.append(
                f"{bar.start:{TS_FMT}} O={bar.open:.2f} H={bar.high:.2f} "
                f"L={bar.low:.2f} C={bar.close:.2f}"
            )
    return "\n".join(sections)


def response_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "schemaVersion": {"type": "string", "enum": ["v10-1"]},
            "cutoff": {"type": "string"},
            "decisionState": {"type": "string", "enum": ["OBSERVE", "ARMED", "TRADEABLE", "RESOLVED"]},
            "action": {
                "type": "string",
                "enum": ["NO_TRADE", "NOT_YET", "ENTER_LONG", "ENTER_SHORT", "HOLD", "EXIT"],
            },
            "direction": {"type": "string", "enum": ["NONE", "LONG", "SHORT"]},
            "parentJourney": {"type": "string"},
            "parentChanged": {"type": "boolean"},
            "parentChangeReason": {"type": "string"},
            "activeMemories": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "zone": {"type": "string"},
                        "role": {"type": "string", "enum": ["PARENT", "CHILD_TRANSIT", "EXECUTION"]},
                        "function": {"type": "string"},
                    },
                    "required": ["zone", "role", "function"],
                },
            },
            "childRoute": {"type": "string"},
            "falsificationAnchor": {"type": "string"},
            "genuineRestorationBehavior": {"type": "string"},
            "destination": {"type": "string"},
            "routeState": {"type": "string", "enum": ["BLOCKED", "TO_MEMORY", "OPEN_ROUTE", "UNRESOLVED"]},
            "structuralAsymmetry": {"type": "string"},
            "uncertainties": {"type": "array", "items": {"type": "string"}},
            "decisionReason": {"type": "string"},
            "nextReviewMinutes": {"type": "integer", "enum": [15, 30, 60, 180, 360]},
        },
        "required": [
            "schemaVersion", "cutoff", "decisionState", "action", "direction",
            "parentJourney", "parentChanged", "parentChangeReason", "activeMemories",
            "childRoute", "falsificationAnchor", "genuineRestorationBehavior",
            "destination", "routeState", "structuralAsymmetry", "uncertainties",
            "decisionReason", "nextReviewMinutes",
        ],
    }


def build_prompt(cutoff: datetime, frames: dict[str, list[Bar]], prior_state: dict[str, Any] | None) -> str:
    position = prior_state.get("openPosition") if prior_state else None
    prior_decision = prior_state.get("lastDecision") if prior_state else None
    return f"""V10 GOLD# January 2025 future-hidden replay.

CAUSAL CUTOFF: {cutoff:{TS_FMT}}
CURRENT M1 CLOSE: {frames['M1'][-1].close:.2f}

All attached charts and all OHLC rows end at or before the cutoff. Do not use knowledge of what happened later on this historical date.

OPEN V10 POSITION:
{json.dumps(position, ensure_ascii=False, indent=2) if position else 'NONE'}

PRIOR V10 DECISION STATE:
{json.dumps(prior_decision, ensure_ascii=False, indent=2) if prior_decision else 'NONE - this is the first V10 decision'}

Exact recent OHLC for reading candle chronology:
{recent_ohlc(frames)}

Read the multi-timeframe chart adaptively under the V10 behavior contract. Return one causal decision. If no position is open, do not return HOLD or EXIT. If a position is open, do not open a second trade. Preserve an earlier thesis unless newly revealed evidence materially changes it.
"""


def load_secret(path: Path, slot_override: int | None = None) -> tuple[str, str, int]:
    if not path.is_file():
        raise V10Error(f"Gemini secret file not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    keys = raw.get("apiKeys") or []
    slot = slot_override if slot_override is not None else int(raw.get("activeApiKeySlot") or 1)
    if slot < 1 or slot > len(keys) or not str(keys[slot - 1]).strip():
        raise V10Error("active Gemini API key slot is unavailable")
    config = raw.get("config") or {}
    model = str(config.get("model") or "gemini-3.5-flash-lite")
    return str(keys[slot - 1]).strip(), model, slot


def load_state(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def validate_decision(decision: dict[str, Any], cutoff: datetime, state: dict[str, Any] | None) -> None:
    if decision.get("schemaVersion") != "v10-1":
        raise V10Error("Gemini returned an unexpected schemaVersion")
    if decision.get("cutoff") != cutoff.strftime(TS_FMT):
        raise V10Error("Gemini cutoff does not match the requested causal cutoff")
    action = decision.get("action")
    direction = decision.get("direction")
    open_position = state.get("openPosition") if state else None
    if open_position and action not in {"HOLD", "EXIT"}:
        raise V10Error("open position requires HOLD or EXIT")
    if not open_position and action in {"HOLD", "EXIT"}:
        raise V10Error("flat state cannot HOLD or EXIT")
    if action == "ENTER_LONG" and direction != "LONG":
        raise V10Error("ENTER_LONG requires LONG direction")
    if action == "ENTER_SHORT" and direction != "SHORT":
        raise V10Error("ENTER_SHORT requires SHORT direction")
    if action in {"NO_TRADE", "NOT_YET"} and direction not in {"NONE", "LONG", "SHORT"}:
        raise V10Error("invalid observational direction")
    if action in {"ENTER_LONG", "ENTER_SHORT"}:
        if not str(decision.get("falsificationAnchor", "")).strip():
            raise V10Error("entry requires a falsification anchor")
        if not str(decision.get("genuineRestorationBehavior", "")).strip():
            raise V10Error("entry requires observable restoration behavior")


def save_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_json(path, payload)


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def update_state(
    previous: dict[str, Any] | None,
    cutoff: datetime,
    current_close: float,
    decision: dict[str, Any],
) -> dict[str, Any]:
    state = dict(previous or {})
    position = state.get("openPosition")
    action = decision["action"]
    if action in {"ENTER_LONG", "ENTER_SHORT"}:
        position = {
            "openedAt": cutoff.strftime(TS_FMT),
            "direction": decision["direction"],
            "entryReference": current_close,
            "falsificationAnchor": decision["falsificationAnchor"],
            "genuineRestorationBehavior": decision["genuineRestorationBehavior"],
            "destination": decision["destination"],
            "routeState": decision["routeState"],
            "frozenChildRoute": decision["childRoute"],
        }
    elif action == "EXIT":
        position = None
    state.update(
        {
            "version": 1,
            "period": "2025-01",
            "lastCutoff": cutoff.strftime(TS_FMT),
            "lastDecision": decision,
            "openPosition": position,
        }
    )
    return state


def run_step(args: argparse.Namespace) -> int:
    total_started = time.perf_counter()
    run_dir = OUTPUT_ROOT / args.run_id
    state_path = run_dir / "state.json"
    state = load_state(state_path)
    if state:
        previous_cutoff = datetime.strptime(state["lastCutoff"], TS_FMT)
        if args.cutoff <= previous_cutoff:
            raise V10Error("new cutoff must be later than the persisted V10 cutoff")

    market_started = time.perf_counter()
    frames, market_cache, cache_action = load_or_advance_market_cache(
        args.source, args.cutoff, run_dir / "market_cache.json"
    )
    market_ms = round((time.perf_counter() - market_started) * 1000, 2)
    source_sha = str(market_cache["sourceSha256"])
    step_name = args.cutoff.strftime("%Y%m%d_%H%M%S")
    step_dir = run_dir / "steps" / step_name
    chart_started = time.perf_counter()
    images = [
        step_dir / "01_parent_D1_H4.png",
        step_dir / "02_child_H1_M15.png",
        step_dir / "03_execution_M5_M1.png",
    ]
    if not all(image.is_file() for image in images):
        images = render_packet(frames, args.cutoff, step_dir)
        chart_action = "rendered"
    else:
        chart_action = "reused"
    chart_ms = round((time.perf_counter() - chart_started) * 1000, 2)
    prompt = build_prompt(args.cutoff, frames, state)
    contract_text = args.contract.read_text(encoding="utf-8")
    (step_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    (step_dir / "system_instruction.md").write_text(contract_text, encoding="utf-8")

    packet = {
        "pipeline": "v10-gemini-v9-style-jan2025",
        "runId": args.run_id,
        "cutoff": args.cutoff.strftime(TS_FMT),
        "historyStart": HISTORY_START.strftime(TS_FMT),
        "source": args.source.name,
        "sourceSha256": source_sha,
        "revealedRows": int(market_cache["revealedRows"]),
        "revealedFirst": market_cache["revealedFirst"],
        "revealedLast": market_cache["cutoff"],
        "images": [
            {"name": image.name, "sha256": sha256_file(image)} for image in images
        ],
        "promptSha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "contractSha256": hashlib.sha256(contract_text.encode("utf-8")).hexdigest(),
        "localTimingMs": {
            "marketData": market_ms,
            "charts": chart_ms,
            "cacheAction": cache_action,
            "chartAction": chart_action,
        },
        "dryRun": bool(args.dry_run),
    }
    save_json(step_dir / "packet.json", packet)
    if args.dry_run:
        print(json.dumps(packet, ensure_ascii=False, indent=2))
        return 0

    api_key, configured_model, api_key_slot = load_secret(args.secret, args.api_key_slot)
    model = args.model or configured_model
    api_started = time.perf_counter()
    response = generate_structured_decision(
        api_key=api_key,
        model=model,
        prompt=prompt,
        system_instruction=contract_text,
        images=images,
        media_resolutions=["MEDIA_RESOLUTION_HIGH"] * len(images),
        schema=response_schema(),
        temperature=0.0,
        max_output_tokens=args.max_output_tokens,
        thinking_level=args.thinking_level,
        timeout_seconds=args.timeout_seconds,
        raw_response_path=step_dir / "raw_response.json",
    )
    api_ms = round((time.perf_counter() - api_started) * 1000, 2)
    decision = response.payload
    validate_decision(decision, args.cutoff, state)
    record = {
        "pipeline": packet["pipeline"],
        "runId": args.run_id,
        "cutoff": args.cutoff.strftime(TS_FMT),
        "model": response.model,
        "apiKeySlot": api_key_slot,
        "thinkingLevel": args.thinking_level,
        "usage": response.usage,
        "timingMs": {
            "marketData": market_ms,
            "charts": chart_ms,
            "api": api_ms,
            "total": round((time.perf_counter() - total_started) * 1000, 2),
            "cacheAction": cache_action,
            "chartAction": chart_action,
        },
        "packet": packet,
        "decision": decision,
    }
    save_json(step_dir / "decision.json", record)
    append_jsonl(run_dir / "decisions.jsonl", record)
    new_state = update_state(state, args.cutoff, frames["M1"][-1].close, decision)
    save_json(state_path, new_state)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default="v10_jan2025_gemini_001")
    parser.add_argument("--cutoff", type=parse_cutoff, required=True)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    parser.add_argument("--secret", type=Path, default=SECRET)
    parser.add_argument("--api-key-slot", type=int)
    parser.add_argument("--model")
    parser.add_argument("--thinking-level", choices=("minimal", "low", "medium", "high"), default="high")
    parser.add_argument("--max-output-tokens", type=int, default=8192)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return run_step(args)
    except (V10Error, GeminiReplayError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"V10_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
