#!/usr/bin/env python3
"""Audit a V13 policy-replay MT5 journal against its frozen action ledger.

The parser treats the journal as execution evidence, not as research input.  It
requires the successful ENTRY/EXIT stream to be an exact ordered match to the
ledger and derives realized economics from the balance deltas emitted by EA
version 13.301 or later.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


MARKER = "V13Q75_EVENT|"
SUCCESS_KINDS = {"ENTRY", "EXIT"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--journal", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--ltf-policy", type=Path)
    parser.add_argument("--child1-reference", type=Path)
    return parser.parse_args()


def read_journal(path: Path) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-16")
    records: list[dict[str, object]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if MARKER not in line:
            continue
        prefix, payload = line.split(MARKER, 1)
        parts = payload.split("|")
        kind = parts[0]
        fields: dict[str, str] = {}
        for part in parts[1:]:
            if "=" in part:
                key, value = part.split("=", 1)
                fields[key] = value
        records.append(
            {
                "line_number": line_number,
                "log_prefix": prefix,
                "kind": kind,
                "fields": fields,
            }
        )
    return records


def load_ledger(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def as_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def max_loss_streak(values: list[float]) -> int:
    best = current = 0
    for value in values:
        if value < 0:
            current += 1
            best = max(best, current)
        elif value > 0:
            current = 0
    return best


def economics(values: list[float]) -> dict[str, float | int | None]:
    wins = [value for value in values if value > 0]
    losses = [value for value in values if value < 0]
    flats = len(values) - len(wins) - len(losses)
    gross_win = sum(wins)
    gross_loss = -sum(losses)
    equity = peak = 0.0
    max_drawdown = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
    average_win = gross_win / len(wins) if wins else None
    average_loss = gross_loss / len(losses) if losses else None
    return {
        "trades": len(values),
        "wins": len(wins),
        "losses": len(losses),
        "flats": flats,
        "nonflat_win_rate": len(wins) / (len(wins) + len(losses)) if wins or losses else None,
        "net_profit": sum(values),
        "gross_profit": gross_win,
        "gross_loss": gross_loss,
        "profit_factor": gross_win / gross_loss if gross_loss else None,
        "average_win": average_win,
        "average_loss": average_loss,
        "payoff_ratio": average_win / average_loss if average_win is not None and average_loss else None,
        "expectancy": sum(values) / len(values) if values else None,
        "realized_max_drawdown": max_drawdown,
        "max_consecutive_losses": max_loss_streak(values),
    }


def block_quality(values: list[float], sizes: tuple[int, ...] = (10, 25, 50, 100)) -> dict[str, object]:
    result: dict[str, object] = {}
    for size in sizes:
        slices = [values[index:index + size] for index in range(0, len(values), size) if len(values[index:index + size]) == size]
        blocks = [sum(block) for block in slices]
        high_win_negative = sum(
            (sum(value > 0 for value in block) / sum(value != 0 for value in block) > 0.5)
            and sum(block) < 0
            for block in slices
        )
        ordered = sorted(blocks)
        if not ordered:
            median = None
        elif len(ordered) % 2:
            median = ordered[len(ordered) // 2]
        else:
            middle = len(ordered) // 2
            median = (ordered[middle - 1] + ordered[middle]) / 2
        result[str(size)] = {
            "blocks": len(blocks),
            "positive_share": sum(value > 0 for value in blocks) / len(blocks) if blocks else None,
            "median_usd": median,
            "high_win_rate_negative_blocks": high_win_negative,
            "high_win_rate_negative_share": high_win_negative / len(blocks) if blocks else None,
        }
    return result


def build_h4_run_map(args: argparse.Namespace) -> tuple[dict[str, int], dict[str, object] | None]:
    if args.ltf_policy is None or args.child1_reference is None:
        return {}, None
    ltf = load_ledger(args.ltf_policy)
    c1 = load_ledger(args.child1_reference)
    ltf.sort(key=lambda row: (row["event_ts"], int(row["h4_run_id"])))
    c1.sort(key=lambda row: (row["entry_time"], int(row["journey"])))
    mapping: dict[str, int] = {
        f"LTF{index:06d}": int(row["h4_run_id"])
        for index, row in enumerate(ltf, start=1)
    }
    candidate_offsets: list[int] = []
    parsed_c1 = [
        {
            **row,
            "entry_dt": datetime.strptime(row["entry_time"], "%Y-%m-%d %H:%M:%S"),
            "exit_dt": datetime.strptime(row["exit_time"], "%Y-%m-%d %H:%M:%S"),
        }
        for row in c1
    ]
    for row in ltf:
        timestamp = datetime.strptime(row["event_ts"], "%Y-%m-%d %H:%M:%S")
        direction = int(row["direction"])
        for child in parsed_c1:
            if int(child["side"]) == direction and child["entry_dt"] <= timestamp < child["exit_dt"]:
                candidate_offsets.append(int(row["h4_run_id"]) - int(child["journey"]))
                break
    if not candidate_offsets:
        return mapping, {"status": "FAILED", "reason": "no_cross_lane_run_alignment"}
    offset_counts = Counter(candidate_offsets)
    offset, support = offset_counts.most_common(1)[0]
    for index, row in enumerate(c1, start=1):
        mapping[f"C1{index:06d}"] = int(row["journey"]) + offset
    return mapping, {
        "status": "PASS",
        "inferred_h4_run_offset": offset,
        "alignment_observations": len(candidate_offsets),
        "modal_offset_support": support,
        "modal_offset_share": support / len(candidate_offsets),
        "offset_counts": {str(key): value for key, value in sorted(offset_counts.items())},
    }


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    ledger = load_ledger(args.ledger)
    journal = read_journal(args.journal)
    h4_run_map, h4_run_alignment = build_h4_run_map(args)

    kind_counts = Counter(str(record["kind"]) for record in journal)
    successes = [record for record in journal if record["kind"] in SUCCESS_KINDS]
    success_tuples = [
        (
            int(record["fields"]["row"]),
            str(record["fields"]["id"]),
            str(record["kind"]),
        )
        for record in successes
    ]
    expected_tuples = [
        (index + 2, row["event_id"], row["action"])
        for index, row in enumerate(ledger)
    ]
    first_mismatch = next(
        (
            index
            for index, pair in enumerate(zip(expected_tuples, success_tuples))
            if pair[0] != pair[1]
        ),
        None,
    )
    exact_action_parity = (
        len(success_tuples) == len(expected_tuples)
        and first_mismatch is None
    )

    failures = [record for record in journal if record["kind"] == "ORDER_FAIL"]
    failed_rows = Counter(int(record["fields"]["row"]) for record in failures)
    failure_retcodes = Counter(record["fields"].get("retcode", "") for record in failures)
    successful_rows = {row_number for row_number, _, _ in success_tuples}
    unresolved_failed_rows = sorted(set(failed_rows) - successful_rows)

    by_event: dict[str, dict[str, object]] = defaultdict(dict)
    ledger_by_event: dict[str, dict[str, str]] = {}
    for row in ledger:
        event = ledger_by_event.setdefault(row["event_id"], {})
        event[row["action"]] = row
    for record in successes:
        fields = record["fields"]
        event = by_event[str(fields["id"])]
        event[str(record["kind"])] = record

    event_rows: list[dict[str, object]] = []
    for event_id, action_records in by_event.items():
        if "ENTRY" not in action_records or "EXIT" not in action_records:
            continue
        entry_record = action_records["ENTRY"]
        exit_record = action_records["EXIT"]
        entry_fields = entry_record["fields"]
        exit_fields = exit_record["fields"]
        entry_ledger = ledger_by_event[event_id]["ENTRY"]
        exit_ledger = ledger_by_event[event_id]["EXIT"]
        entry_delta = as_float(entry_fields.get("balance_delta"))
        exit_delta = as_float(exit_fields.get("balance_delta"))
        pnl = None if entry_delta is None or exit_delta is None else entry_delta + exit_delta
        direction = entry_ledger["direction"]
        entry_fill = as_float(entry_fields.get("fill"))
        exit_fill = as_float(exit_fields.get("fill"))
        entry_expected = float(entry_ledger["expected_price"])
        exit_expected = float(exit_ledger["expected_price"])
        if entry_fill is None or exit_fill is None:
            adverse_slippage = None
        elif direction == "LONG":
            adverse_slippage = (entry_fill - entry_expected) + (exit_expected - exit_fill)
        else:
            adverse_slippage = (entry_expected - entry_fill) + (exit_fill - exit_expected)
        exit_time = datetime.strptime(exit_fields["time"], "%Y.%m.%d %H:%M:%S")
        event_rows.append(
            {
                "event_id": event_id,
                "policy_lane": entry_ledger["policy_lane"],
                "direction": direction,
                "entry_policy_time": entry_ledger["action_time"],
                "entry_execution_time": entry_fields["time"],
                "exit_policy_time": exit_ledger["action_time"],
                "exit_execution_time": exit_fields["time"],
                "entry_expected_price": entry_expected,
                "entry_fill": entry_fill,
                "exit_expected_price": exit_expected,
                "exit_fill": exit_fill,
                "adverse_slippage_price": adverse_slippage,
                "entry_balance_delta": entry_delta,
                "exit_balance_delta": exit_delta,
                "realized_pnl": pnl,
                "h4_run_id": h4_run_map.get(event_id),
                "exit_year": exit_time.year,
                "exit_line_number": exit_record["line_number"],
            }
        )
    event_rows.sort(key=lambda row: int(row["exit_line_number"]))

    has_balance_delta = len(event_rows) == len(ledger_by_event) and all(
        row["realized_pnl"] is not None for row in event_rows
    )
    all_values = [float(row["realized_pnl"]) for row in event_rows if row["realized_pnl"] is not None]
    by_lane: dict[str, list[float]] = defaultdict(list)
    by_year: dict[str, list[float]] = defaultdict(list)
    for row in event_rows:
        if row["realized_pnl"] is None:
            continue
        by_lane[str(row["policy_lane"])].append(float(row["realized_pnl"]))
        by_year[str(row["exit_year"])].append(float(row["realized_pnl"]))

    trimmed_by_h4_run = None
    if has_balance_delta and h4_run_map and all(row["h4_run_id"] is not None for row in event_rows):
        run_totals: dict[int, float] = defaultdict(float)
        for row in event_rows:
            run_totals[int(row["h4_run_id"])] += float(row["realized_pnl"])
        ranked = sorted(run_totals.items(), key=lambda pair: pair[1], reverse=True)
        trimmed_by_h4_run = {
            str(count): sum(all_values) - sum(value for _, value in ranked[:count])
            for count in (1, 3, 5, 10, 20)
        }

    init_ok = kind_counts.get("INIT_OK", 0)
    replay_complete = kind_counts.get("REPLAY_COMPLETE", 0)
    halts = kind_counts.get("HALT", 0)
    completion_fields = next(
        (record["fields"] for record in journal if record["kind"] == "REPLAY_COMPLETE"),
        {},
    )
    pass_status = (
        exact_action_parity
        and not unresolved_failed_rows
        and init_ok == 1
        and replay_complete == 1
        and halts == 0
        and kind_counts.get("ENTRY_EXPIRED", 0) == 0
        and kind_counts.get("EXIT_NO_POSITION", 0) == 0
        and has_balance_delta
    )

    summary = {
        "status": "PASS" if pass_status else "FAIL",
        "ledger": str(args.ledger),
        "ledger_sha256": sha256(args.ledger),
        "journal": str(args.journal),
        "journal_sha256": sha256(args.journal),
        "ledger_action_rows": len(ledger),
        "ledger_events": len(ledger_by_event),
        "journal_marker_counts": dict(sorted(kind_counts.items())),
        "successful_action_rows": len(successes),
        "exact_ordered_action_parity": exact_action_parity,
        "first_mismatch_zero_based": first_mismatch,
        "order_fail_attempts": len(failures),
        "order_fail_rows": len(failed_rows),
        "order_fail_retcodes": dict(sorted(failure_retcodes.items())),
        "maximum_retries_for_one_row": max(failed_rows.values(), default=0),
        "unresolved_failed_rows": unresolved_failed_rows,
        "has_complete_balance_delta_evidence": has_balance_delta,
        "tester_completion": {
            "balance": as_float(completion_fields.get("balance")),
            "equity": as_float(completion_fields.get("equity")),
            "maximum_actual_tick_equity_drawdown": as_float(completion_fields.get("max_equity_drawdown")),
            "maximum_concurrent_positions": int(completion_fields["max_open"]) if completion_fields.get("max_open") else None,
        },
        "h4_run_alignment": h4_run_alignment,
        "economics": economics(all_values) if has_balance_delta else None,
        "chronological_nonoverlapping_block_quality": block_quality(all_values) if has_balance_delta else None,
        "top_profitable_h4_runs_removed_net_profit": trimmed_by_h4_run,
        "economics_by_lane": {
            lane: economics(values) for lane, values in sorted(by_lane.items())
        } if has_balance_delta else None,
        "economics_by_exit_year": {
            year: economics(values) for year, values in sorted(by_year.items())
        } if has_balance_delta else None,
    }

    event_path = args.out_dir / "v13_policy_replay_actual_tick_events.csv"
    with event_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(event_rows[0].keys()))
        writer.writeheader()
        writer.writerows(event_rows)
    marker_fields = [
        "line_number", "kind", "row", "id", "time", "action", "retcode",
        "reason", "lane", "dir", "ticket", "fill", "expected",
        "balance_delta", "before_volume", "events", "balance", "equity",
        "max_equity_drawdown", "max_open",
    ]
    marker_path = args.out_dir / "v13_policy_replay_journal_markers.csv"
    with marker_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=marker_fields)
        writer.writeheader()
        for record in journal:
            fields = record["fields"]
            writer.writerow(
                {
                    "line_number": record["line_number"],
                    "kind": record["kind"],
                    **{name: fields.get(name, "") for name in marker_fields[2:]},
                }
            )
    summary_path = args.out_dir / "v13_policy_replay_actual_tick_parity.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if not pass_status:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
