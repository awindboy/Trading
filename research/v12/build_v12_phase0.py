#!/usr/bin/env python3
"""Build the exhaustive V12 Phase-0 C1/C2 observation universe.

This builder intentionally stops at a frozen causal cutoff.  It hashes the full
local files for provenance, but it parses no post-cutoff price field.  Native
MT5 timeframe exports are used only to verify the raw-M1 reconstruction.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Iterable, Iterator, Optional

from v12_phase0_core import (
    EVENT_DEFINITION_VERSION,
    LANE_PARENT_TF,
    M1Row,
    MultiTimeframeAggregator,
    StreamQuality,
    TIMEFRAME_MINUTES,
    attach_wilder_atr,
    bar_to_flat_dict,
    bucket_end,
    build_parent_events,
    enrich_extreme_times,
    iso_broker_label,
    parse_broker_timestamp,
    price_points,
    sha256_file,
    sha256_json_file,
)


REFERENCE_MARKERS = {
    "M5": "_M5_",
    "M15": "_M15_",
    "M30": "_M30_",
    "H1": "_H1_",
    "H4": "_H4_",
    "D1": "_Daily_",
    "W1": "_Weekly_",
}


@dataclass
class PrefixAudit:
    prefix_sha256: Optional[str] = None
    prefix_bytes: int = 0
    parsed_price_rows: int = 0
    first_unrevealed_timestamp: Optional[datetime] = None
    post_cutoff_price_rows_parsed: int = 0

    def to_dict(self) -> dict:
        return {
            "prefix_sha256": self.prefix_sha256,
            "prefix_bytes": self.prefix_bytes,
            "parsed_price_rows": self.parsed_price_rows,
            "first_unrevealed_timestamp": (
                iso_broker_label(self.first_unrevealed_timestamp)
                if self.first_unrevealed_timestamp
                else None
            ),
            "post_cutoff_price_rows_parsed": self.post_cutoff_price_rows_parsed,
        }


def parse_cutoff(text: str) -> datetime:
    normalized = text.strip().replace(" ", "T")
    return datetime.fromisoformat(normalized)


def _header_map(raw_header: bytes) -> dict[str, int]:
    columns = raw_header.decode("utf-8-sig").rstrip("\r\n").split("\t")
    required = {"<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>", "<TICKVOL>", "<VOL>", "<SPREAD>"}
    missing = required.difference(columns)
    if missing:
        raise ValueError(f"raw M1 header missing fields: {sorted(missing)}")
    return {name: columns.index(name) for name in required}


def iter_m1_prefix(
    path: Path,
    cutoff: datetime,
    *,
    audit: Optional[PrefixAudit] = None,
) -> Iterator[M1Row]:
    digest = hashlib.sha256()
    prefix_bytes = 0
    with path.open("rb") as handle:
        raw_header = handle.readline()
        if not raw_header:
            raise ValueError(f"empty M1 source: {path}")
        index = _header_map(raw_header)
        digest.update(raw_header)
        prefix_bytes += len(raw_header)

        for raw_line in handle:
            if not raw_line.strip():
                continue
            values = raw_line.decode("utf-8").rstrip("\r\n").split("\t")
            timestamp = parse_broker_timestamp(values[index["<DATE>"]], values[index["<TIME>"]])
            if timestamp > cutoff:
                if audit is not None:
                    audit.first_unrevealed_timestamp = timestamp
                break
            digest.update(raw_line)
            prefix_bytes += len(raw_line)
            row = M1Row(
                timestamp=timestamp,
                open=float(values[index["<OPEN>"]]),
                high=float(values[index["<HIGH>"]]),
                low=float(values[index["<LOW>"]]),
                close=float(values[index["<CLOSE>"]]),
                tick_volume=int(values[index["<TICKVOL>"]]),
                volume=int(values[index["<VOL>"]]),
                spread=int(values[index["<SPREAD>"]]),
            )
            if audit is not None:
                audit.parsed_price_rows += 1
            yield row

    if audit is not None:
        audit.prefix_sha256 = digest.hexdigest()
        audit.prefix_bytes = prefix_bytes


def exact_prefix_audit(new_source: Path, trusted_source: Path) -> dict:
    trusted_size = trusted_source.stat().st_size
    trusted_hash = sha256_file(trusted_source)
    digest = hashlib.sha256()
    remaining = trusted_size
    with new_source.open("rb") as handle:
        while remaining:
            block = handle.read(min(1024 * 1024, remaining))
            if not block:
                break
            digest.update(block)
            remaining -= len(block)
        has_extension = bool(handle.read(1))
    new_prefix_hash = digest.hexdigest() if remaining == 0 else None
    return {
        "trusted_source": str(trusted_source),
        "trusted_bytes": trusted_size,
        "trusted_sha256": trusted_hash,
        "new_source_first_trusted_bytes_sha256": new_prefix_hash,
        "exact_byte_prefix_match": remaining == 0 and new_prefix_hash == trusted_hash,
        "new_source_has_extension": has_extension,
    }


def discover_files(data_dir: Path) -> tuple[Path, dict[str, Path]]:
    files = sorted(path for path in data_dir.iterdir() if path.is_file() and path.suffix.lower() == ".csv")
    m1 = [path for path in files if "_M1_" in path.name]
    if len(m1) != 1:
        raise ValueError(f"expected exactly one M1 file in {data_dir}, found {len(m1)}")
    references: dict[str, Path] = {}
    for timeframe, marker in REFERENCE_MARKERS.items():
        matches = [path for path in files if marker in path.name]
        if len(matches) != 1:
            raise ValueError(f"expected exactly one {timeframe} reference, found {len(matches)}")
        references[timeframe] = matches[0]
    return m1[0], references


def read_reference_prefix(path: Path, timeframe: str, cutoff: datetime) -> tuple[dict[datetime, dict], dict]:
    bars: dict[datetime, dict] = {}
    duplicates = 0
    first_unrevealed: Optional[datetime] = None
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"missing reference header: {path}")
        has_time = "<TIME>" in reader.fieldnames
        for row in reader:
            start = parse_broker_timestamp(row["<DATE>"], row.get("<TIME>") if has_time else None)
            # Do not parse any price field from the unseen holdout.
            if bucket_end(start, timeframe) > cutoff:
                first_unrevealed = start
                break
            if start in bars:
                duplicates += 1
            bars[start] = {
                "open": float(row["<OPEN>"]),
                "high": float(row["<HIGH>"]),
                "low": float(row["<LOW>"]),
                "close": float(row["<CLOSE>"]),
                "tick_volume": int(row["<TICKVOL>"]),
                "volume": int(row["<VOL>"]),
                "spread": int(row["<SPREAD>"]),
            }
    metadata = {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "parsed_completed_rows": len(bars),
        "duplicate_open_times": duplicates,
        "first_unrevealed_bar": iso_broker_label(first_unrevealed) if first_unrevealed else None,
        "post_cutoff_price_rows_parsed": 0,
    }
    return bars, metadata


def compare_reconstruction(reconstructed, reference: dict[datetime, dict]) -> dict:
    rebuilt = {bar.open_time: bar for bar in reconstructed}
    missing_in_rebuild = sorted(set(reference).difference(rebuilt))
    missing_in_reference = sorted(set(rebuilt).difference(reference))
    ohlc_mismatch = 0
    tick_volume_mismatch = 0
    volume_mismatch = 0
    samples: list[dict] = []
    for key in sorted(set(rebuilt).intersection(reference)):
        left = rebuilt[key]
        right = reference[key]
        price_fields = ("open", "high", "low", "close")
        bad_prices = [
            field
            for field in price_fields
            if price_points(getattr(left, field)) != price_points(right[field])
        ]
        if bad_prices:
            ohlc_mismatch += 1
        if left.tick_volume != right["tick_volume"]:
            tick_volume_mismatch += 1
        if left.volume != right["volume"]:
            volume_mismatch += 1
        if (bad_prices or left.tick_volume != right["tick_volume"] or left.volume != right["volume"]) and len(samples) < 12:
            samples.append(
                {
                    "open_time": iso_broker_label(key),
                    "price_fields": bad_prices,
                    "rebuilt": {
                        "open": left.open,
                        "high": left.high,
                        "low": left.low,
                        "close": left.close,
                        "tick_volume": left.tick_volume,
                        "volume": left.volume,
                    },
                    "reference": right,
                }
            )
    return {
        "rebuilt_rows": len(rebuilt),
        "reference_rows": len(reference),
        "common_rows": len(set(rebuilt).intersection(reference)),
        "missing_in_rebuild": len(missing_in_rebuild),
        "missing_in_reference": len(missing_in_reference),
        "ohlc_mismatch_rows": ohlc_mismatch,
        "tick_volume_mismatch_rows": tick_volume_mismatch,
        "volume_mismatch_rows": volume_mismatch,
        "ohlc_and_coverage_exact": not missing_in_rebuild and not missing_in_reference and ohlc_mismatch == 0,
        "tick_volume_exact": tick_volume_mismatch == 0,
        "volume_exact": volume_mismatch == 0,
        "missing_in_rebuild_examples": [iso_broker_label(value) for value in missing_in_rebuild[:12]],
        "missing_in_reference_examples": [iso_broker_label(value) for value in missing_in_reference[:12]],
        "mismatch_examples": samples,
    }


def write_csv(path: Path, rows: list[dict], fieldnames: Optional[list[str]] = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not fieldnames:
            return
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_prepare_output(path: Path, replace: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not replace:
            raise FileExistsError(f"output directory is not empty: {path}; pass --replace-output")
        for child in path.iterdir():
            if not child.is_file() or not child.name.startswith("V12_PHASE0_"):
                raise ValueError(f"refusing to replace unexpected output path: {child}")
            child.unlink()
    path.mkdir(parents=True, exist_ok=True)


def make_summary(events: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str, str], Counter] = defaultdict(Counter)
    for event in events:
        year = event["decision_time"][:4]
        key = (event["lane"], year, event["interaction"])
        grouped[key]["events"] += 1
        if event["hypothesis_direction"] != "NONE":
            grouped[key]["directional"] += 1
        if event["ordering_precision"] == "AMBIGUOUS":
            grouped[key]["ambiguous"] += 1
    lane_year_totals = Counter((event["lane"], event["decision_time"][:4]) for event in events)
    rows: list[dict] = []
    for (lane, year, interaction), counter in sorted(grouped.items()):
        total = lane_year_totals[(lane, year)]
        rows.append(
            {
                "lane": lane,
                "year": year,
                "interaction": interaction,
                "events": counter["events"],
                "share_of_lane_year": counter["events"] / total if total else None,
                "directional_events": counter["directional"],
                "ambiguous_order_events": counter["ambiguous"],
            }
        )
    return rows


def make_blind_pack(events: list[dict], per_stratum: int = 12) -> list[dict]:
    strata: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for event in events:
        key = (event["lane"], event["decision_time"][:4], event["interaction"])
        strata[key].append(event)
    selected: list[dict] = []
    for key in sorted(strata):
        candidates = sorted(
            strata[key],
            key=lambda row: hashlib.sha256(row["parent_id"].encode("ascii")).hexdigest(),
        )
        selected.extend(candidates[:per_stratum])
    selected.sort(key=lambda row: (row["decision_time"], row["lane"]))
    keep = [
        "parent_id",
        "lane",
        "decision_time",
        "interaction",
        "hypothesis_direction",
        "c1_open_time",
        "c1_open",
        "c1_high",
        "c1_low",
        "c1_close",
        "c1_midpoint",
        "c1_range_atr",
        "c2_open_time",
        "c2_open",
        "c2_high",
        "c2_low",
        "c2_close",
        "c2_range_atr",
        "close_location_c1",
        "first_high_breach_time",
        "first_low_breach_time",
        "extreme_ordering",
        "ordering_precision",
    ]
    return [{field: event[field] for field in keep} for event in selected]


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=repo_root / "data" / "GOLD#")
    parser.add_argument("--trusted-prefix", type=Path, default=repo_root / "GOLD#_M1_202201030100_202608282357.csv")
    parser.add_argument("--clock-spec", type=Path, default=Path(__file__).with_name("v12_broker_clock_spec.json"))
    parser.add_argument("--cutoff", help="MT5 broker-label cutoff; defaults to clock spec")
    parser.add_argument("--output", type=Path, default=repo_root / "output" / "v12_phase0_event_universe_20260923")
    parser.add_argument("--replace-output", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    spec = json.loads(args.clock_spec.read_text(encoding="utf-8"))
    cutoff = parse_cutoff(args.cutoff or spec["development_evidence_cutoff"])
    m1_source, references = discover_files(args.data_dir)
    safe_prepare_output(args.output, args.replace_output)

    full_source_hash = sha256_file(m1_source)
    source_file_metadata = {
        "path": str(m1_source),
        "bytes": m1_source.stat().st_size,
        "full_file_sha256": full_source_hash,
    }
    prefix_match = exact_prefix_audit(m1_source, args.trusted_prefix) if args.trusted_prefix.exists() else {
        "trusted_source": str(args.trusted_prefix),
        "status": "MISSING",
        "exact_byte_prefix_match": False,
    }

    prefix_audit = PrefixAudit()
    stream_quality = StreamQuality()
    aggregator = MultiTimeframeAggregator()
    previous: Optional[M1Row] = None
    rows_by_year: Counter = Counter()
    for row in iter_m1_prefix(m1_source, cutoff, audit=prefix_audit):
        stream_quality.observe(row, previous)
        aggregator.observe(row)
        rows_by_year[str(row.timestamp.year)] += 1
        previous = row

    if prefix_audit.prefix_sha256 is None:
        raise RuntimeError("prefix hash was not finalized")
    for bars in aggregator.completed.values():
        attach_wilder_atr(bars)

    broker_spec_hash = sha256_json_file(args.clock_spec)
    decisions, events = build_parent_events(
        aggregator.completed,
        symbol=spec["symbol"],
        source_prefix_sha256=prefix_audit.prefix_sha256,
        broker_clock_spec_sha256=broker_spec_hash,
    )

    # A second causal pass records first extreme breaches.  It still stops at
    # the same cutoff and parses zero holdout price rows.
    enrich_extreme_times(iter_m1_prefix(m1_source, cutoff), events)
    event_by_id = {event["parent_id"]: event for event in events}
    for decision in decisions:
        decision["c2"]["ordering_precision"] = event_by_id[decision["parent_id"]]["ordering_precision"]

    reference_quality: dict[str, dict] = {}
    parity: dict[str, dict] = {}
    for timeframe, path in references.items():
        native, metadata = read_reference_prefix(path, timeframe, cutoff)
        reference_quality[timeframe] = metadata
        parity[timeframe] = compare_reconstruction(aggregator.completed[timeframe], native)

    quality = {
        "contract": {
            "generation": "V12",
            "phase": "PHASE_0_OBSERVATION_ONLY",
            "event_definition_version": EVENT_DEFINITION_VERSION,
            "cutoff": iso_broker_label(cutoff),
            "cutoff_namespace": spec["timestamp_semantics"]["namespace"],
            "post_cutoff_price_rows_parsed": 0,
            "future_outcomes_joined": False,
        },
        "source": source_file_metadata,
        "causal_prefix": prefix_audit.to_dict(),
        "trusted_prefix_audit": prefix_match,
        "stream_quality": stream_quality.to_dict(),
        "rows_by_year": dict(sorted(rows_by_year.items())),
        "terminal_unconfirmed_buckets": aggregator.terminal_buckets(),
        "completed_bar_counts": {tf: len(bars) for tf, bars in aggregator.completed.items()},
        "reference_files": reference_quality,
        "raw_m1_reconstruction_parity": parity,
        "gates": {
            "trusted_history_exact": bool(prefix_match.get("exact_byte_prefix_match")),
            "strict_chronology": stream_quality.non_monotonic_timestamps == 0 and stream_quality.duplicate_timestamps == 0,
            "ohlc_valid": stream_quality.invalid_ohlc_rows == 0,
            "point_grid_valid": stream_quality.off_grid_price_rows == 0,
            "all_reference_ohlc_and_coverage_exact": all(value["ohlc_and_coverage_exact"] for value in parity.values()),
            "all_reference_tick_volume_exact": all(value["tick_volume_exact"] for value in parity.values()),
            "holdout_prices_unread": prefix_audit.post_cutoff_price_rows_parsed == 0,
        },
    }

    for timeframe in ("H1", "H4", "D1", "W1"):
        write_csv(
            args.output / f"V12_PHASE0_{timeframe}_BARS.csv",
            [bar_to_flat_dict(bar) for bar in aggregator.completed[timeframe]],
        )
    write_csv(args.output / "V12_PHASE0_PARENT_EVENTS.csv", events)
    write_csv(args.output / "V12_PHASE0_SUMMARY.csv", make_summary(events))
    write_csv(args.output / "V12_PHASE0_BLIND_REVIEW.csv", make_blind_pack(events))
    with (args.output / "V12_PHASE0_DECISIONS.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for decision in decisions:
            handle.write(json.dumps(decision, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    write_json(args.output / "V12_PHASE0_DATA_QUALITY.json", quality)

    output_hashes = {
        path.name: {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
        for path in sorted(args.output.glob("V12_PHASE0_*"))
        if path.name != "V12_PHASE0_MANIFEST.json"
    }
    manifest = {
        "generation": "V12",
        "phase": "PHASE_0_OBSERVATION_ONLY",
        "pipeline_files": {
            path.name: {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in (
                Path(__file__).resolve(),
                Path(__file__).with_name("v12_phase0_core.py"),
                Path(__file__).with_name("v12_crt_event_contract.schema.json"),
                Path(__file__).with_name("validate_v12_event_schema.py"),
                Path(__file__).with_name("validate_v12_phase0_output.py"),
                Path(__file__).with_name("test_v12_phase0.py"),
                args.clock_spec.resolve(),
            )
        },
        "event_definition_version": EVENT_DEFINITION_VERSION,
        "broker_clock_spec": str(args.clock_spec),
        "broker_clock_spec_sha256": broker_spec_hash,
        "source_m1": source_file_metadata,
        "source_causal_prefix_sha256": prefix_audit.prefix_sha256,
        "cutoff": iso_broker_label(cutoff),
        "decision_records": len(decisions),
        "directional_hypotheses": sum(event["hypothesis_direction"] != "NONE" for event in events),
        "outcome_records": 0,
        "entry_authority": False,
        "performance_claim_allowed": False,
        "files": output_hashes,
    }
    write_json(args.output / "V12_PHASE0_MANIFEST.json", manifest)

    print(json.dumps({
        "status": "PASS" if all(quality["gates"].values()) else "REVIEW_REQUIRED",
        "output": str(args.output),
        "cutoff": iso_broker_label(cutoff),
        "m1_rows": stream_quality.rows,
        "events": len(events),
        "directional_hypotheses": manifest["directional_hypotheses"],
        "gates": quality["gates"],
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if all(quality["gates"].values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
