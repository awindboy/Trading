"""Replay a frozen manual Q1 decision ledger against MT5 M1 OHLC data.

This is an execution model, not a decision engine. It never adds, removes, or
scores scenarios. Decisions are loaded only from manual_decisions.json.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "output" / "mentor_q1_manual_review"
DECISIONS = REVIEW / "manual_decisions.json"
DATASET = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz"
OUTPUT = REVIEW / "execution"
CHARTS = OUTPUT / "charts"
UTC = timezone.utc
Q1_END = int(datetime(2025, 4, 1, tzinfo=UTC).timestamp())


def iso(timestamp: int) -> str:
    return datetime.fromtimestamp(int(timestamp), UTC).isoformat()


def decision_hash() -> str:
    return hashlib.sha256(DECISIONS.read_bytes()).hexdigest()


def load_inputs() -> tuple[list[dict], np.ndarray]:
    payload = json.loads(DECISIONS.read_text(encoding="utf-8"))
    plans = [
        item
        for item in payload["decisions"]
        if item["decision"] in {"PLAN", "PLAN_IF_FLAT"}
    ]
    rates = np.load(DATASET, allow_pickle=False)["rates"]
    return plans, rates[rates["time"] < Q1_END]


def first_index_after(rates: np.ndarray, timestamp: int) -> int:
    return int(np.searchsorted(rates["time"], timestamp + 1, side="left"))


def simulate_plan(plan: dict, rates: np.ndarray) -> dict:
    """Use a conservative M1 OHLC limit-order model after the decision bar."""
    direction = plan["direction"]
    entry = float(plan["entry"])
    stop = float(plan["stop_loss"])
    target = float(plan["take_profit"])
    as_of = int(datetime.fromisoformat(plan["as_of"]).timestamp())
    index = first_index_after(rates, as_of)
    filled_at: int | None = None

    for bar in rates[index:]:
        timestamp = int(bar["time"])
        low = float(bar["low"])
        high = float(bar["high"])

        if filled_at is None:
            touched = low <= entry <= high
            invalidated = low <= stop if direction == "long" else high >= stop
            if touched:
                filled_at = timestamp
                # If entry and stop/target lie in the same M1 bar, use the
                # adverse path. Tick ordering is unavailable in this dataset.
                if direction == "long":
                    if low <= stop:
                        return outcome(plan, "SL", timestamp, entry, stop, filled_at, "same_bar_adverse")
                    if high >= target:
                        return outcome(plan, "TP", timestamp, entry, target, filled_at, "same_bar")
                else:
                    if high >= stop:
                        return outcome(plan, "SL", timestamp, entry, stop, filled_at, "same_bar_adverse")
                    if low <= target:
                        return outcome(plan, "TP", timestamp, entry, target, filled_at, "same_bar")
                continue
            if invalidated:
                return outcome(plan, "CANCELLED", timestamp, None, None, None, "zone_invalidated_before_fill")
            continue

        if direction == "long":
            stop_hit = low <= stop
            target_hit = high >= target
        else:
            stop_hit = high >= stop
            target_hit = low <= target
        if stop_hit and target_hit:
            return outcome(plan, "SL", timestamp, entry, stop, filled_at, "same_bar_adverse")
        if stop_hit:
            return outcome(plan, "SL", timestamp, entry, stop, filled_at, "bar_extreme")
        if target_hit:
            return outcome(plan, "TP", timestamp, entry, target, filled_at, "bar_extreme")

    return outcome(plan, "UNFILLED", None, None, None, None, "q1_end")


def outcome(
    plan: dict,
    status: str,
    exit_at: int | None,
    entry_price: float | None,
    exit_price: float | None,
    filled_at: int | None,
    execution_note: str,
) -> dict:
    direction = plan["direction"]
    risk = abs(float(plan["entry"]) - float(plan["stop_loss"]))
    result = {
        "candidate_no": plan["candidate_no"],
        "as_of": plan["as_of"],
        "decision": plan["decision"],
        "direction": direction,
        "entry": float(plan["entry"]),
        "stop_loss": float(plan["stop_loss"]),
        "take_profit": float(plan["take_profit"]),
        "status": status,
        "entry_at": None if filled_at is None else iso(filled_at),
        "exit_at": None if exit_at is None else iso(exit_at),
        "entry_price": entry_price,
        "exit_price": exit_price,
        "execution_note": execution_note,
        "holding_minutes": None if filled_at is None or exit_at is None else int((exit_at - filled_at) // 60),
        "r_multiple": None,
    }
    if entry_price is not None and exit_price is not None:
        pnl = exit_price - entry_price if direction == "long" else entry_price - exit_price
        result["r_multiple"] = round(pnl / risk, 6)
    return result


def choose_timeframe(holding_minutes: int) -> int:
    if holding_minutes <= 6 * 60:
        return 60
    if holding_minutes <= 24 * 60:
        return 300
    if holding_minutes <= 5 * 24 * 60:
        return 900
    if holding_minutes <= 14 * 24 * 60:
        return 1800
    return 3600


def aggregate(rates: np.ndarray, seconds: int) -> np.ndarray:
    starts = (rates["time"] // seconds) * seconds
    unique, first = np.unique(starts, return_index=True)
    last = np.r_[first[1:] - 1, len(rates) - 1]
    output = np.empty(len(unique), dtype=rates.dtype)
    output["time"] = unique
    output["open"] = rates["open"][first]
    output["high"] = np.maximum.reduceat(rates["high"], first)
    output["low"] = np.minimum.reduceat(rates["low"], first)
    output["close"] = rates["close"][last]
    output["tick_volume"] = rates["tick_volume"][last]
    output["spread"] = rates["spread"][last]
    output["real_volume"] = rates["real_volume"][last]
    return output


def render_position_box(record: dict, rates: np.ndarray) -> Path:
    filled_at = int(datetime.fromisoformat(record["entry_at"]).timestamp())
    exit_at = int(datetime.fromisoformat(record["exit_at"]).timestamp())
    holding = max(1, int(record["holding_minutes"]))
    timeframe = choose_timeframe(holding)
    padding = max(timeframe * 50, (exit_at - filled_at) // 4)
    subset = rates[(rates["time"] >= filled_at - padding) & (rates["time"] <= exit_at + padding)]
    bars = aggregate(subset, timeframe)
    epoch_number = mdates.date2num(datetime(1970, 1, 1, tzinfo=UTC))
    dates = bars["time"].astype(float) / 86_400 + epoch_number
    width = timeframe / 86400 * 0.68

    fig, ax = plt.subplots(figsize=(13, 6), facecolor="#0a0f14")
    ax.set_facecolor("#0a0f14")
    for when, bar in zip(dates, bars):
        up = bar["close"] >= bar["open"]
        color = "#55c8be" if up else "#ec7777"
        ax.vlines(when, bar["low"], bar["high"], color=color, linewidth=0.8, alpha=0.9)
        bottom = min(bar["open"], bar["close"])
        height = max(abs(bar["close"] - bar["open"]), 0.01)
        ax.add_patch(Rectangle((when - width / 2, bottom), width, height, color=color, alpha=0.95, linewidth=0))

    left = filled_at / 86_400 + epoch_number
    right = exit_at / 86_400 + epoch_number
    entry = record["entry"]
    stop = record["stop_loss"]
    target = record["take_profit"]
    if record["direction"] == "long":
        profitable = (entry, target)
        risk = (stop, entry)
    else:
        profitable = (target, entry)
        risk = (entry, stop)
    ax.add_patch(Rectangle((left, min(profitable)), right - left, abs(profitable[1] - profitable[0]), facecolor="#34c38f", edgecolor="none", alpha=0.20))
    ax.add_patch(Rectangle((left, min(risk)), right - left, abs(risk[1] - risk[0]), facecolor="#e45757", edgecolor="none", alpha=0.20))

    ax.grid(color="#24303c", alpha=0.45, linewidth=0.6)
    ax.tick_params(colors="#90a4b5")
    for spine in ax.spines.values():
        spine.set_color("#2a3642")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d\n%H:%M", tz=UTC))
    title = (
        f"Q1 manual #{record['candidate_no']:02d} | {record['direction'].upper()} | "
        f"{record['status']} | {holding}m | {timeframe // 60}m chart"
    )
    ax.set_title(title, color="#edf5fb", loc="left", fontsize=12, fontweight="bold")
    fig.tight_layout()
    destination = CHARTS / f"{record['candidate_no']:02d}_{record['as_of'][:10]}_{record['direction']}_{record['status']}.png"
    fig.savefig(destination, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)
    return destination


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    CHARTS.mkdir(parents=True, exist_ok=True)
    plans, rates = load_inputs()
    records = [simulate_plan(plan, rates) for plan in plans]
    for record in records:
        if record["status"] in {"SL", "TP"}:
            record["chart"] = str(render_position_box(record, rates).relative_to(ROOT)).replace("\\", "/")

    filled = [record for record in records if record["status"] in {"SL", "TP"}]
    wins = [record for record in filled if record["status"] == "TP"]
    losses = [record for record in filled if record["status"] == "SL"]
    summary = {
        "schema": "mentor-q1-manual-execution-v1",
        "decision_sha256": decision_hash(),
        "data": "MT5 GOLD M1 OHLC; no tick replay available",
        "model": "next-bar limit retest; pre-fill stop invalidation; same-bar SL/TP collision resolved adversely",
        "planned": len(records),
        "filled": len(filled),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": None if not filled else round(len(wins) / len(filled), 6),
        "total_r": round(sum(record["r_multiple"] for record in filled), 6),
        "average_r": None if not filled else round(sum(record["r_multiple"] for record in filled) / len(filled), 6),
        "cancelled": sum(record["status"] == "CANCELLED" for record in records),
        "unfilled": sum(record["status"] == "UNFILLED" for record in records),
        "records": records,
    }
    (OUTPUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    with (OUTPUT / "trades.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=sorted({key for record in records for key in record}))
        writer.writeheader()
        writer.writerows(records)
    print(json.dumps({key: summary[key] for key in summary if key != "records"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
