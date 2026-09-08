#!/usr/bin/env python3
"""Fail-closed V9 causal replay helper for the authoritative GOLD# M1 TSV.

This utility is intentionally NOT a general future-data explorer. It creates and
advances a revealed prefix only to an explicit cutoff row, records a byte offset
for efficient monotonic continuation, and builds chart-timeframe snapshots only
from that revealed prefix.

The source file is verified against the authoritative SHA256 by default.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import BinaryIO, Iterable, Iterator, Optional

AUTHORITATIVE_SHA256 = "626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2"
EXPECTED_HEADER = [
    "<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>",
    "<TICKVOL>", "<VOL>", "<SPREAD>",
]
STATE_VERSION = 1
TS_FMT = "%Y.%m.%d %H:%M:%S"
CLI_TS_FMT = "%Y-%m-%d %H:%M:%S"


class CausalReplayError(RuntimeError):
    pass


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def parse_cli_ts(value: str) -> datetime:
    try:
        return datetime.strptime(value, CLI_TS_FMT)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"timestamp must be YYYY-MM-DD HH:MM:SS, got {value!r}"
        ) from exc


def parse_row_ts(line: bytes) -> datetime:
    # Parse only DATE/TIME fields for chronology. The full line is never printed.
    parts = line.rstrip(b"\r\n").split(b"\t", 2)
    if len(parts) < 3:
        raise CausalReplayError("malformed M1 row: fewer than 3 tab-separated fields")
    try:
        text = parts[0].decode("ascii") + " " + parts[1].decode("ascii")
        return datetime.strptime(text, TS_FMT)
    except Exception as exc:
        raise CausalReplayError("malformed DATE/TIME in M1 row") from exc


def parse_header(line: bytes) -> list[str]:
    text = line.decode("utf-8-sig").rstrip("\r\n")
    return text.split("\t")


def verify_source(source: Path, expected_sha256: str) -> str:
    if not source.is_file():
        raise CausalReplayError(f"source does not exist: {source}")
    actual = sha256_file(source)
    if actual.lower() != expected_sha256.lower():
        raise CausalReplayError(
            "source SHA256 mismatch; refusing to continue\n"
            f"expected: {expected_sha256}\nactual:   {actual}"
        )
    with source.open("rb") as f:
        header = parse_header(f.readline())
    if header != EXPECTED_HEADER:
        raise CausalReplayError(
            f"unexpected M1 header; expected {EXPECTED_HEADER!r}, got {header!r}"
        )
    return actual


def atomic_json_write(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(obj, f, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def save_state(
    state_path: Path,
    *,
    source: Path,
    source_sha256: str,
    revealed: Path,
    history_start: datetime,
    cutoff: datetime,
    resume_offset: int,
    rows: int,
) -> None:
    state = {
        "version": STATE_VERSION,
        "source_basename": source.name,
        "source_sha256": source_sha256,
        "source_size": source.stat().st_size,
        "revealed_path": str(revealed),
        "revealed_sha256": sha256_file(revealed),
        "history_start": history_start.strftime(CLI_TS_FMT),
        "cutoff": cutoff.strftime(CLI_TS_FMT),
        "resume_offset": resume_offset,
        "revealed_rows": rows,
    }
    atomic_json_write(state_path, state)


def load_state(path: Path) -> dict:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise CausalReplayError(f"cannot read replay state: {path}") from exc
    if state.get("version") != STATE_VERSION:
        raise CausalReplayError("unsupported replay-state version")
    return state


def init_revealed(
    source: Path,
    revealed: Path,
    state_path: Path,
    history_start: datetime,
    cutoff: datetime,
    expected_sha256: str,
) -> None:
    if cutoff < history_start:
        raise CausalReplayError("cutoff precedes history_start")
    source_sha = verify_source(source, expected_sha256)
    revealed.parent.mkdir(parents=True, exist_ok=True)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(prefix=revealed.name + ".", suffix=".tmp", dir=revealed.parent)
    found_cutoff = False
    rows_written = 0
    resume_offset = -1
    previous_ts: Optional[datetime] = None
    try:
        with source.open("rb") as src, os.fdopen(fd, "wb") as dst:
            header = src.readline()
            if parse_header(header) != EXPECTED_HEADER:
                raise CausalReplayError("source header changed after verification")
            dst.write(header)
            while True:
                line = src.readline()
                if not line:
                    break
                ts = parse_row_ts(line)
                if previous_ts is not None and ts <= previous_ts:
                    raise CausalReplayError(
                        f"source is not strictly chronological near {ts.strftime(CLI_TS_FMT)}"
                    )
                previous_ts = ts
                if ts < history_start:
                    continue
                if ts > cutoff:
                    # We never emit this row. A cutoff that is not an actual M1 row is
                    # rejected rather than rounded forward/backward silently.
                    break
                dst.write(line)
                rows_written += 1
                if ts == cutoff:
                    found_cutoff = True
                    resume_offset = src.tell()
                    break
        if not found_cutoff:
            raise CausalReplayError(
                "exact cutoff row was not found; refusing to infer/round cutoff. "
                "Use a known M1 timestamp."
            )
        os.replace(tmp_name, revealed)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)

    save_state(
        state_path,
        source=source,
        source_sha256=source_sha,
        revealed=revealed,
        history_start=history_start,
        cutoff=cutoff,
        resume_offset=resume_offset,
        rows=rows_written,
    )
    audit_revealed(revealed, cutoff)


def advance_revealed(
    source: Path,
    revealed: Path,
    state_path: Path,
    new_cutoff: datetime,
    expected_sha256: str,
) -> None:
    state = load_state(state_path)
    old_cutoff = parse_cli_ts(state["cutoff"])
    history_start = parse_cli_ts(state["history_start"])
    if new_cutoff <= old_cutoff:
        raise CausalReplayError("advance cutoff must be later than current state cutoff")

    source_sha = verify_source(source, expected_sha256)
    if source_sha != state.get("source_sha256"):
        raise CausalReplayError("state source hash does not match verified source")
    if source.stat().st_size != state.get("source_size"):
        raise CausalReplayError("source size differs from frozen replay state")
    if not revealed.is_file():
        raise CausalReplayError(f"revealed prefix missing: {revealed}")
    current_output_sha = sha256_file(revealed)
    if current_output_sha != state.get("revealed_sha256"):
        raise CausalReplayError("revealed prefix was modified; refusing to advance")

    resume_offset = int(state["resume_offset"])
    rows_written = int(state["revealed_rows"])
    fd, tmp_name = tempfile.mkstemp(prefix=revealed.name + ".", suffix=".tmp", dir=revealed.parent)
    found_cutoff = False
    new_resume_offset = -1
    previous_ts = old_cutoff
    try:
        with os.fdopen(fd, "wb") as dst:
            with revealed.open("rb") as old:
                shutil.copyfileobj(old, dst, length=8 * 1024 * 1024)
            with source.open("rb") as src:
                src.seek(resume_offset)
                while True:
                    line = src.readline()
                    if not line:
                        break
                    ts = parse_row_ts(line)
                    if ts <= previous_ts:
                        raise CausalReplayError("source chronology/offset mismatch while advancing")
                    previous_ts = ts
                    if ts > new_cutoff:
                        break
                    dst.write(line)
                    rows_written += 1
                    if ts == new_cutoff:
                        found_cutoff = True
                        new_resume_offset = src.tell()
                        break
        if not found_cutoff:
            raise CausalReplayError(
                "exact new cutoff row was not found; output left unchanged. "
                "Use a known M1 timestamp."
            )
        os.replace(tmp_name, revealed)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)

    save_state(
        state_path,
        source=source,
        source_sha256=source_sha,
        revealed=revealed,
        history_start=history_start,
        cutoff=new_cutoff,
        resume_offset=new_resume_offset,
        rows=rows_written,
    )
    audit_revealed(revealed, new_cutoff)


def iter_revealed_rows(path: Path) -> Iterator[tuple[datetime, list[str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        try:
            header = next(reader)
        except StopIteration as exc:
            raise CausalReplayError("revealed file is empty") from exc
        if header != EXPECTED_HEADER:
            raise CausalReplayError("revealed file has unexpected header")
        previous: Optional[datetime] = None
        for row in reader:
            if len(row) != len(EXPECTED_HEADER):
                raise CausalReplayError("malformed revealed row")
            ts = datetime.strptime(row[0] + " " + row[1], TS_FMT)
            if previous is not None and ts <= previous:
                raise CausalReplayError("revealed file is not strictly chronological")
            previous = ts
            yield ts, row


def audit_revealed(path: Path, cutoff: datetime) -> dict:
    first: Optional[datetime] = None
    last: Optional[datetime] = None
    count = 0
    for ts, _ in iter_revealed_rows(path):
        if first is None:
            first = ts
        last = ts
        count += 1
        if ts > cutoff:
            raise CausalReplayError(
                f"CAUSAL BREACH: revealed timestamp {ts} exceeds cutoff {cutoff}"
            )
    if last != cutoff:
        raise CausalReplayError(
            f"revealed max timestamp must equal cutoff; got {last}, expected {cutoff}"
        )
    return {
        "rows": count,
        "first": first.strftime(CLI_TS_FMT) if first else None,
        "last": last.strftime(CLI_TS_FMT) if last else None,
        "cutoff": cutoff.strftime(CLI_TS_FMT),
        "sha256": sha256_file(path),
    }


@dataclass
class Bar:
    start: datetime
    open: float
    high: float
    low: float
    close: float
    tickvol: int
    vol: int
    spread: int
    observed_rows: int


def bucket_start(ts: datetime, minutes: int) -> datetime:
    if minutes < 60:
        minute = (ts.minute // minutes) * minutes
        return ts.replace(minute=minute, second=0, microsecond=0)
    if minutes == 60:
        return ts.replace(minute=0, second=0, microsecond=0)
    if minutes == 240:
        hour = (ts.hour // 4) * 4
        return ts.replace(hour=hour, minute=0, second=0, microsecond=0)
    raise ValueError(f"unsupported timeframe minutes: {minutes}")


def aggregate(path: Path, minutes: int) -> tuple[list[Bar], datetime]:
    bars: list[Bar] = []
    current: Optional[Bar] = None
    max_ts: Optional[datetime] = None
    for ts, row in iter_revealed_rows(path):
        max_ts = ts
        bstart = bucket_start(ts, minutes)
        o, h, l, c = map(float, row[2:6])
        tickvol, vol, spread = map(int, row[6:9])
        if current is None or current.start != bstart:
            if current is not None:
                bars.append(current)
            current = Bar(bstart, o, h, l, c, tickvol, vol, spread, 1)
        else:
            current.high = max(current.high, h)
            current.low = min(current.low, l)
            current.close = c
            current.tickvol += tickvol
            current.vol += vol
            current.spread = spread
            current.observed_rows += 1
    if current is not None:
        bars.append(current)
    if max_ts is None:
        raise CausalReplayError("revealed file contains no data rows")
    return bars, max_ts


def write_bars(path: Path, bars: list[Bar], minutes: int, cutoff: datetime) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow([
            "<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>",
            "<TICKVOL>", "<VOL>", "<SPREAD>", "<OBSERVED_ROWS>", "<PARTIAL>",
        ])
        for b in bars:
            bucket_end = b.start + timedelta(minutes=minutes) - timedelta(minutes=1)
            partial = 1 if bucket_end > cutoff else 0
            w.writerow([
                b.start.strftime("%Y.%m.%d"), b.start.strftime("%H:%M:%S"),
                f"{b.open:.8f}".rstrip("0").rstrip("."),
                f"{b.high:.8f}".rstrip("0").rstrip("."),
                f"{b.low:.8f}".rstrip("0").rstrip("."),
                f"{b.close:.8f}".rstrip("0").rstrip("."),
                b.tickvol, b.vol, b.spread, b.observed_rows, partial,
            ])


def previous_completed_h4_atr14(bars: list[Bar], cutoff: datetime) -> Optional[dict]:
    completed = [b for b in bars if b.start + timedelta(hours=4) <= cutoff + timedelta(minutes=1)]
    if len(completed) < 14:
        return None
    trs: list[float] = []
    prev_close: Optional[float] = None
    for b in completed:
        if prev_close is None:
            tr = b.high - b.low
        else:
            tr = max(b.high - b.low, abs(b.high - prev_close), abs(b.low - prev_close))
        trs.append(tr)
        prev_close = b.close
    if len(trs) < 14:
        return None
    atr = sum(trs[:14]) / 14.0
    for tr in trs[14:]:
        atr = ((atr * 13.0) + tr) / 14.0
    b = completed[-1]
    return {
        "h4_bar_start": b.start.strftime(CLI_TS_FMT),
        "atr14_wilder": atr,
        "definition": "previous fully completed H4 Wilder ATR14 at revealed cutoff",
    }


def snapshot(revealed: Path, out_dir: Path) -> None:
    # Determine cutoff from the revealed file itself; no source file is consulted.
    rows = list(iter_revealed_rows(revealed))
    if not rows:
        raise CausalReplayError("revealed file contains no rows")
    cutoff = rows[-1][0]
    out_dir.mkdir(parents=True, exist_ok=True)
    tf_map = {"M5": 5, "M15": 15, "H1": 60, "H4": 240}
    all_bars: dict[str, list[Bar]] = {}
    for name, minutes in tf_map.items():
        bars, max_ts = aggregate(revealed, minutes)
        if max_ts != cutoff:
            raise CausalReplayError("snapshot cutoff inconsistency")
        all_bars[name] = bars
        write_bars(out_dir / f"{name}.tsv", bars, minutes, cutoff)
    atr = previous_completed_h4_atr14(all_bars["H4"], cutoff)
    meta = {
        "cutoff": cutoff.strftime(CLI_TS_FMT),
        "revealed_sha256": sha256_file(revealed),
        "timeframes": {k: len(v) for k, v in all_bars.items()},
        "previous_completed_h4_atr14": atr,
        "note": "All outputs derive only from the already-revealed prefix. Last higher-TF bar may be PARTIAL=1.",
    }
    atomic_json_write(out_dir / "snapshot.json", meta)


def cmd_verify(args: argparse.Namespace) -> None:
    actual = verify_source(args.source, args.expected_sha256)
    print(json.dumps({"ok": True, "sha256": actual, "source": str(args.source)}, indent=2))


def cmd_init(args: argparse.Namespace) -> None:
    init_revealed(
        args.source, args.output, args.state, args.history_start, args.cutoff, args.expected_sha256
    )
    print(json.dumps(audit_revealed(args.output, args.cutoff), indent=2))


def cmd_advance(args: argparse.Namespace) -> None:
    advance_revealed(args.source, args.output, args.state, args.cutoff, args.expected_sha256)
    print(json.dumps(audit_revealed(args.output, args.cutoff), indent=2))


def cmd_audit(args: argparse.Namespace) -> None:
    print(json.dumps(audit_revealed(args.input, args.cutoff), indent=2))


def cmd_snapshot(args: argparse.Namespace) -> None:
    snapshot(args.input, args.out_dir)
    print((args.out_dir / "snapshot.json").read_text(encoding="utf-8"), end="")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    def add_sha(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--expected-sha256", default=AUTHORITATIVE_SHA256)

    sp = sub.add_parser("verify", help="verify source SHA256 and schema only")
    sp.add_argument("--source", type=Path, required=True)
    add_sha(sp)
    sp.set_defaults(func=cmd_verify)

    sp = sub.add_parser("init", help="create a revealed prefix ending exactly at cutoff")
    sp.add_argument("--source", type=Path, required=True)
    sp.add_argument("--history-start", type=parse_cli_ts, required=True)
    sp.add_argument("--cutoff", type=parse_cli_ts, required=True)
    sp.add_argument("--output", type=Path, required=True)
    sp.add_argument("--state", type=Path, required=True)
    add_sha(sp)
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("advance", help="monotonically advance an existing revealed prefix")
    sp.add_argument("--source", type=Path, required=True)
    sp.add_argument("--cutoff", type=parse_cli_ts, required=True)
    sp.add_argument("--output", type=Path, required=True)
    sp.add_argument("--state", type=Path, required=True)
    add_sha(sp)
    sp.set_defaults(func=cmd_advance)

    sp = sub.add_parser("audit", help="assert a revealed prefix ends exactly at cutoff")
    sp.add_argument("--input", type=Path, required=True)
    sp.add_argument("--cutoff", type=parse_cli_ts, required=True)
    sp.set_defaults(func=cmd_audit)

    sp = sub.add_parser("snapshot", help="build M5/M15/H1/H4 only from revealed prefix")
    sp.add_argument("--input", type=Path, required=True)
    sp.add_argument("--out-dir", type=Path, required=True)
    sp.set_defaults(func=cmd_snapshot)
    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
        return 0
    except CausalReplayError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
