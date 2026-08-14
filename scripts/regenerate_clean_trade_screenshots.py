from __future__ import annotations

import argparse
import base64
import json
import math
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import MetaTrader5 as mt5


ROOT = Path(__file__).resolve().parents[1]
JOURNAL_FILE = ROOT / "data" / "journal.json"
OUTPUT_DIR = ROOT / "output" / "clean_trade_screenshots"
KST = timezone(timedelta(hours=9))


@dataclass
class ChartPlan:
    timeframe_name: str
    timeframe_value: int
    before: timedelta
    after: timedelta


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        number = float(value)
        return number if math.isfinite(number) else default
    except (TypeError, ValueError):
        return default


def plan_for_duration(open_time: datetime, close_time: datetime) -> ChartPlan:
    minutes = max(1.0, (close_time - open_time).total_seconds() / 60)
    if minutes <= 35:
        return ChartPlan("M1", mt5.TIMEFRAME_M1, timedelta(minutes=18), timedelta(minutes=18))
    if minutes <= 180:
        return ChartPlan("M5", mt5.TIMEFRAME_M5, timedelta(minutes=45), timedelta(minutes=45))
    if minutes <= 900:
        return ChartPlan("M15", mt5.TIMEFRAME_M15, timedelta(hours=2), timedelta(hours=2))
    return ChartPlan("H1", mt5.TIMEFRAME_H1, timedelta(hours=8), timedelta(hours=8))


def rates_for_trade(symbol: str, plan: ChartPlan, start: datetime, end: datetime) -> list[dict[str, Any]]:
    if not mt5.symbol_select(symbol, True):
        raise RuntimeError(f"symbol_select failed for {symbol}: {mt5.last_error()}")

    rates = mt5.copy_rates_range(symbol, plan.timeframe_value, start, end)
    if rates is None or len(rates) == 0:
        raise RuntimeError(f"copy_rates_range returned no bars for {symbol} {plan.timeframe_name}: {mt5.last_error()}")

    rows: list[dict[str, Any]] = []
    for rate in rates:
        rows.append(
            {
                "time": datetime.fromtimestamp(int(rate["time"]), tz=timezone.utc),
                "open": float(rate["open"]),
                "high": float(rate["high"]),
                "low": float(rate["low"]),
                "close": float(rate["close"]),
            }
        )
    return rows


def price_limits(rows: list[dict[str, Any]], levels: list[float]) -> tuple[float, float]:
    lows = [row["low"] for row in rows]
    highs = [row["high"] for row in rows]
    visible_levels = [level for level in levels if level > 0]
    low = min(lows + visible_levels)
    high = max(highs + visible_levels)
    span = max(high - low, abs(high) * 0.001, 0.01)
    return low - span * 0.12, high + span * 0.12


def draw_candles(ax: Any, rows: list[dict[str, Any]], timeframe_name: str) -> None:
    xs = [mdates.date2num(row["time"]) for row in rows]
    if len(xs) > 1:
        candle_width = (xs[1] - xs[0]) * 0.62
    else:
        candle_width = {"M1": 0.00045, "M5": 0.0018, "M15": 0.0055, "H1": 0.022}.get(timeframe_name, 0.001)

    for x_value, row in zip(xs, rows):
        open_price = row["open"]
        close_price = row["close"]
        high_price = row["high"]
        low_price = row["low"]
        is_up = close_price >= open_price
        color = "#21c79a" if is_up else "#ff5f7e"
        ax.vlines(x_value, low_price, high_price, color=color, linewidth=1.05, alpha=0.95)
        body_low = min(open_price, close_price)
        body_height = max(abs(close_price - open_price), 0.00001)
        ax.add_patch(
            Rectangle(
                (x_value - candle_width / 2, body_low),
                candle_width,
                body_height,
                facecolor=color,
                edgecolor=color,
                linewidth=0.8,
                alpha=0.9,
            )
        )


def add_price_line(ax: Any, price: float, label: str, color: str, linestyle: str = "-") -> None:
    if price <= 0:
        return
    ax.axhline(price, color=color, linewidth=1.25, linestyle=linestyle, alpha=0.95)
    ax.text(
        0.995,
        price,
        f" {label} {price:g}",
        color=color,
        fontsize=9,
        fontweight="bold",
        va="center",
        ha="right",
        transform=ax.get_yaxis_transform(),
        bbox={"facecolor": "#10161f", "edgecolor": color, "alpha": 0.85, "boxstyle": "round,pad=0.22"},
    )


def add_time_marker(ax: Any, when: datetime, price: float, label: str, color: str, direction: str) -> None:
    x_value = mdates.date2num(when)
    ax.axvline(x_value, color=color, linewidth=1.15, linestyle="--", alpha=0.9)
    marker = "^" if direction == "long" else "v"
    ax.scatter([x_value], [price], marker=marker, s=115, color=color, edgecolor="#0b1118", linewidth=1.2, zorder=5)
    ax.annotate(
        label,
        xy=(x_value, price),
        xytext=(0, 16 if direction == "long" else -22),
        textcoords="offset points",
        ha="center",
        va="bottom" if direction == "long" else "top",
        color=color,
        fontsize=10,
        fontweight="bold",
        bbox={"facecolor": "#10161f", "edgecolor": color, "alpha": 0.88, "boxstyle": "round,pad=0.28"},
    )


def render_trade(trade: dict[str, Any], output_path: Path) -> None:
    meta = trade.get("brokerMeta") or {}
    symbol = str(trade.get("symbol") or "").strip()
    direction = str(trade.get("direction") or "long").lower()
    open_time = parse_time(str(meta.get("openTime") or trade.get("createdAt")))
    close_time = parse_time(str(meta.get("closeTime") or trade.get("updatedAt") or trade.get("createdAt")))
    plan = plan_for_duration(open_time, close_time)
    start = open_time - plan.before
    end = close_time + plan.after
    rows = rates_for_trade(symbol, plan, start, end)

    entry = as_float(trade.get("entryPrice"))
    exit_price = as_float(trade.get("exitPrice"))
    stop = as_float(trade.get("stopPrice"))
    target = as_float(trade.get("targetPrice"))

    fig, ax = plt.subplots(figsize=(16, 9), dpi=120)
    fig.patch.set_facecolor("#0b1118")
    ax.set_facecolor("#10161f")

    draw_candles(ax, rows, plan.timeframe_name)
    add_price_line(ax, entry, "ENTRY", "#4da3ff")
    add_price_line(ax, exit_price, "EXIT", "#f8d866")
    add_price_line(ax, stop, "SL", "#ff5f7e", "--")

    low, high = price_limits(rows, [entry, exit_price, stop])
    candle_span = max(row["high"] for row in rows) - min(row["low"] for row in rows)
    target_is_near = target > 0 and low - candle_span <= target <= high + candle_span
    if target_is_near:
        low, high = price_limits(rows, [entry, exit_price, stop, target])
        add_price_line(ax, target, "TP", "#21c79a", "--")

    add_time_marker(ax, open_time, entry, "ENTRY", "#4da3ff", direction)
    add_time_marker(ax, close_time, exit_price, "EXIT", "#f8d866", direction)

    ax.set_ylim(low, high)
    ax.grid(True, color="#2a3442", linewidth=0.7, alpha=0.45)
    ax.tick_params(colors="#aab6c5", labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#263241")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M", tz=timezone.utc))
    fig.autofmt_xdate(rotation=0, ha="center")
    pnl = as_float(trade.get("brokerPnl"))
    title = (
        f"{symbol} {direction.upper()} | {plan.timeframe_name} clean replay | "
        f"MT5 {open_time.strftime('%H:%M')} -> {close_time.strftime('%H:%M')} | "
        f"KST {open_time.astimezone(KST).strftime('%H:%M')} -> {close_time.astimezone(KST).strftime('%H:%M')} | "
        f"PnL ${pnl:.2f}"
    )
    ax.set_title(title, color="#eef4ff", fontsize=13, fontweight="bold", pad=14)
    if target > 0 and not target_is_near:
        ax.text(
            0.01,
            0.02,
            f"TP {target:g} is outside the focused price range",
            transform=ax.transAxes,
            color="#21c79a",
            fontsize=9,
            alpha=0.9,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(pad=1.3)
    fig.savefig(output_path, facecolor=fig.get_facecolor())
    plt.close(fig)


def image_data_url(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=datetime.now().astimezone().date().isoformat())
    parser.add_argument("--write-journal", action="store_true")
    args = parser.parse_args()

    document = json.loads(JOURNAL_FILE.read_text(encoding="utf-8-sig"))
    trades = [trade for trade in document.get("trades", []) if trade.get("date") == args.date]
    if not trades:
        print(f"No trades found for {args.date}")
        return 0

    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rendered: list[tuple[dict[str, Any], Path]] = []
    for trade in trades:
        meta = trade.get("brokerMeta") or {}
        position_id = meta.get("positionId") or str(trade.get("id") or "").split(":")[-1]
        output_path = OUTPUT_DIR / f"{trade.get('symbol')}_{position_id}_clean_replay.png"
        render_trade(trade, output_path)
        rendered.append((trade, output_path))
        print(f"rendered {trade.get('id')} -> {output_path}")

    mt5.shutdown()

    if args.write_journal:
        backup_dir = ROOT / "data" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"journal-{datetime.now():%Y%m%d-%H%M%S}-before-clean-screenshot-replay.json"
        shutil.copy2(JOURNAL_FILE, backup_path)
        for trade, output_path in rendered:
            trade["screenshot"] = image_data_url(output_path)
            trade["screenshotName"] = output_path.name
        document["updatedAt"] = datetime.now().astimezone().isoformat(timespec="seconds")
        JOURNAL_FILE.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"updated journal: {JOURNAL_FILE}")
        print(f"backup: {backup_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
