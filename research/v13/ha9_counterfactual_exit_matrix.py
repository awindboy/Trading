"""Fixed-entry counterfactual exit matrix for V13 HA-9 trade-mode research.

This is consumed-development research, not trading authority.  Actual MT5
entries are held fixed.  Completed H1/H4 bars are consumed chronologically and
an exit is executable only at the next available bar open.  The script never
chooses the best exit per trade; it compares predeclared horizon policies.

H1/H4 exports are Bid OHLC.  A LONG exit sells at Bid.  A SHORT exit buys at
the next-open Ask proxy (Bid open + exported spread * 0.01).  This proxy is not
a substitute for Strategy Tester tick execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


POINT = 0.01
EPS = 1e-9


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_bars(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep="\t")
    frame["time"] = pd.to_datetime(
        frame["<DATE>"] + " " + frame["<TIME>"], format="%Y.%m.%d %H:%M:%S"
    )
    frame = frame.rename(
        columns={
            "<OPEN>": "open",
            "<HIGH>": "high",
            "<LOW>": "low",
            "<CLOSE>": "close",
            "<SPREAD>": "spread",
        }
    )
    assert frame.time.is_monotonic_increasing
    return frame[["time", "open", "high", "low", "close", "spread"]].copy()


def add_ha(frame: pd.DataFrame, fast: bool = False) -> pd.DataFrame:
    out = frame.copy().reset_index(drop=True)
    opens: list[float] = []
    closes: list[float] = []
    colors: list[int] = []
    previous_open: float | None = None
    previous_close: float | None = None
    previous_color = 0
    for row in out.itertuples(index=False):
        close = (row.open + row.high + row.low + row.close) / 4.0
        if previous_open is None:
            open_ = (row.open + row.close) / 2.0
        elif fast:
            open_ = 0.25 * previous_open + 0.75 * previous_close
        else:
            open_ = (previous_open + previous_close) / 2.0
        color = 1 if close > open_ else -1 if close < open_ else previous_color
        opens.append(open_)
        closes.append(close)
        colors.append(color)
        previous_open, previous_close, previous_color = open_, close, color
    out["ha_open"] = opens
    out["ha_close"] = closes
    out["ha_color"] = colors
    # A completed bar is observable and executable at the next available open.
    out["known_at"] = out.time.shift(-1)
    out["execution_bid_open"] = out.open.shift(-1)
    out["execution_spread"] = out.spread.shift(-1)
    return out


def executable_exit_price(side: int, bid_open: float, spread_points: float) -> float:
    return float(bid_open) if side == 1 else float(bid_open + spread_points * POINT)


def first_opposite_exit(
    states: pd.DataFrame,
    entry_time: pd.Timestamp,
    journey_end: pd.Timestamp,
    side: int,
) -> tuple[pd.Timestamp, float] | None:
    eligible = states.loc[
        (states.known_at > entry_time)
        & (states.known_at <= journey_end)
        & (states.ha_color == -side)
    ]
    if eligible.empty:
        return None
    row = eligible.iloc[0]
    return pd.Timestamp(row.known_at), executable_exit_price(
        side, float(row.execution_bid_open), float(row.execution_spread)
    )


def next_h1_exit(
    h1: pd.DataFrame, exit_time: pd.Timestamp, side: int
) -> tuple[pd.Timestamp, float] | None:
    eligible = h1.loc[h1.known_at > exit_time]
    if eligible.empty:
        return None
    row = eligible.iloc[0]
    return pd.Timestamp(row.known_at), executable_exit_price(
        side, float(row.execution_bid_open), float(row.execution_spread)
    )


def max_drawdown(values: np.ndarray) -> float:
    equity = np.cumsum(values.astype(float))
    peaks = np.maximum.accumulate(np.r_[0.0, equity])
    return float(np.max(peaks[1:] - equity)) if len(equity) else 0.0


def max_loss_streak(values: np.ndarray) -> int:
    best = current = 0
    for value in values:
        if value < -EPS:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return int(best)


def block_stats(frame: pd.DataFrame, pnl: str, size: int) -> dict:
    values = frame.sort_values(["entry_time", "journey", "child"])[pnl].to_numpy(float)
    blocks = [values[i : i + size].sum() for i in range(0, len(values), size) if len(values[i : i + size]) == size]
    return {
        "size": size,
        "n_blocks": len(blocks),
        "positive_share": float(np.mean(np.asarray(blocks) > EPS)) if blocks else None,
        "median_usd": float(np.median(blocks)) if blocks else None,
    }


def stats(frame: pd.DataFrame, pnl: str, exit_time: str) -> dict:
    values = frame[pnl].to_numpy(float)
    wins = int((values > EPS).sum())
    losses = int((values < -EPS).sum())
    flats = int(len(values) - wins - losses)
    gross_win = float(values[values > EPS].sum())
    gross_loss = float(-values[values < -EPS].sum())
    realized = frame.assign(_exit=pd.to_datetime(frame[exit_time])).sort_values(
        ["_exit", "journey", "child"]
    )[pnl].to_numpy(float)
    return {
        "n": len(values),
        "wins": wins,
        "losses": losses,
        "flats": flats,
        "win_rate_nonflat": wins / (wins + losses) if wins + losses else None,
        "net_usd": float(values.sum()),
        "profit_factor": gross_win / gross_loss if gross_loss else None,
        "mean_usd": float(values.mean()) if len(values) else None,
        "median_usd": float(np.median(values)) if len(values) else None,
        "max_realized_sequence_dd_usd": max_drawdown(realized),
        "max_realized_consecutive_losses": max_loss_streak(realized),
        "entry_sequence_blocks": {
            str(size): block_stats(frame, pnl, size) for size in (25, 50, 100)
        },
    }


def scenario_summary(frame: pd.DataFrame, name: str) -> dict:
    return stats(frame, f"{name}_pnl", f"{name}_exit_time")


def compare_population(frame: pd.DataFrame, scenarios: list[str]) -> dict:
    return {name: scenario_summary(frame, name) for name in scenarios}


def install_conditional_scenario(
    frame: pd.DataFrame,
    name: str,
    selector: pd.Series,
) -> None:
    frame[f"{name}_pnl"] = frame.actual_pnl
    frame[f"{name}_exit_time"] = frame.actual_exit_time
    frame.loc[selector, f"{name}_pnl"] = frame.loc[selector, "one_h1_extension_pnl"]
    frame.loc[selector, f"{name}_exit_time"] = frame.loc[
        selector, "one_h1_extension_exit_time"
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trade-ledger", type=Path, required=True)
    parser.add_argument("--h1", type=Path, required=True)
    parser.add_argument("--h4", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.output.mkdir(parents=True, exist_ok=True)

    ledger = pd.read_csv(arguments.trade_ledger)
    for column in (
        "entry_time",
        "exit_time",
        "journey_end_time",
        "proof_h4_end",
    ):
        ledger[column] = pd.to_datetime(ledger[column])

    h1 = add_ha(load_bars(arguments.h1), fast=False)
    h4_std = add_ha(load_bars(arguments.h4), fast=False)
    h4_fast = add_ha(load_bars(arguments.h4), fast=True)

    records: list[dict] = []
    for row in ledger.itertuples(index=False):
        record = row._asdict()
        side = int(row.side)
        entry_price = float(row.entry_price_actual)
        journey_end = pd.Timestamp(row.journey_end_time)

        record["actual_exit_time"] = pd.Timestamp(row.exit_time)
        record["actual_exit_price"] = float(row.exit_price_actual)
        record["actual_pnl"] = float(row.profit_actual)

        # Long-horizon comparator uses the actual report Journey close price.
        record["std_h4_exit_time"] = journey_end
        record["std_h4_exit_price"] = float(row.journey_exit_price_actual)
        record["std_h4_pnl"] = side * (record["std_h4_exit_price"] - entry_price)

        for name, states in (("h1_opposite", h1), ("fast_h4_opposite", h4_fast)):
            candidate = first_opposite_exit(
                states, pd.Timestamp(row.entry_time), journey_end, side
            )
            if candidate is None:
                record[f"{name}_exit_time"] = journey_end
                record[f"{name}_exit_price"] = record["std_h4_exit_price"]
                record[f"{name}_fallback_std"] = True
            else:
                record[f"{name}_exit_time"], record[f"{name}_exit_price"] = candidate
                record[f"{name}_fallback_std"] = False
            record[f"{name}_pnl"] = side * (
                float(record[f"{name}_exit_price"]) - entry_price
            )

        extension = next_h1_exit(h1, pd.Timestamp(row.exit_time), side)
        if extension is None or extension[0] > journey_end:
            record["one_h1_extension_exit_time"] = journey_end
            record["one_h1_extension_exit_price"] = record["std_h4_exit_price"]
            record["one_h1_extension_fallback_std"] = True
        else:
            record["one_h1_extension_exit_time"], record["one_h1_extension_exit_price"] = extension
            record["one_h1_extension_fallback_std"] = False
        record["one_h1_extension_pnl"] = side * (
            float(record["one_h1_extension_exit_price"]) - entry_price
        )
        records.append(record)

    out = pd.DataFrame(records)
    # Child #1 stays actual in every combined-strategy counterfactual.
    add_ons = out.loc[out.child >= 2].copy()
    child_1 = out.loc[out.child == 1].copy()
    scenarios = ["actual", "h1_opposite", "fast_h4_opposite", "std_h4"]

    timeout_mask = (out.child >= 2) & (out.exit_reason == "PROOF_TIMEOUT")
    install_conditional_scenario(out, "timeout_extend_all", timeout_mask)
    install_conditional_scenario(
        out,
        "timeout_extend_repaired",
        timeout_mask & (out.h1_path_state_by_exit == "repaired"),
    )
    install_conditional_scenario(
        out,
        "timeout_extend_opposed_mixed",
        timeout_mask
        & out.h1_path_state_by_exit.isin(
            ["persistent_opposition", "unrepaired_mixed"]
        ),
    )
    conditional_scenarios = [
        "timeout_extend_all",
        "timeout_extend_repaired",
        "timeout_extend_opposed_mixed",
    ]
    add_ons = out.loc[out.child >= 2].copy()
    child_1 = out.loc[out.child == 1].copy()

    combined = {}
    for name in scenarios:
        combined_frame = out.copy()
        if name != "actual":
            combined_frame.loc[combined_frame.child == 1, f"{name}_pnl"] = combined_frame.loc[
                combined_frame.child == 1, "actual_pnl"
            ]
            combined_frame.loc[combined_frame.child == 1, f"{name}_exit_time"] = combined_frame.loc[
                combined_frame.child == 1, "actual_exit_time"
            ]
        combined[name] = scenario_summary(combined_frame, name)

    timeout_losses = add_ons.loc[
        (add_ons.actual_pnl < -EPS)
        & (add_ons.hold_hours >= 4.0)
        & (add_ons.hold_hours < 8.0)
    ].copy()
    fast_winners = add_ons.loc[
        (add_ons.actual_pnl > EPS) & (add_ons.hold_hours < 4.0)
    ].copy()
    proof_timeouts = add_ons.loc[add_ons.exit_reason == "PROOF_TIMEOUT"].copy()
    actionable_timeouts = proof_timeouts.loc[
        ~proof_timeouts.one_h1_extension_fallback_std.astype(bool)
    ].copy()
    proof_timeout_losses = proof_timeouts.loc[proof_timeouts.actual_pnl < -EPS].copy()
    proof_timeout_winners = proof_timeouts.loc[proof_timeouts.actual_pnl > EPS].copy()

    timeout_scenarios = scenarios + ["one_h1_extension"]
    state_summaries: dict[str, dict] = {}
    for column in (
        "h1_path_state_by_exit",
        "signal_h4_delta_contract",
        "signal_h4_wick_present",
        "signal_h4_wick_reappeared",
        "fast_opposed",
    ):
        state_summaries[column] = {}
        for value, group in timeout_losses.groupby(column, dropna=False):
            state_summaries[column][str(value)] = compare_population(group, timeout_scenarios)

    summary = {
        "status": "CONSUMED DEVELOPMENT / FIXED-ENTRY EXIT MATRIX / NOT ACTION AUTHORITY",
        "source_hashes": {
            "trade_ledger": sha256(arguments.trade_ledger),
            "h1": sha256(arguments.h1),
            "h4": sha256(arguments.h4),
        },
        "execution_proxy": {
            "long_exit": "next available raw Bid open",
            "short_exit": "next available raw Bid open + exported spread * 0.01",
            "warning": "bar-open spread proxy; official economics require MT5 real ticks",
        },
        "population": {
            "children": len(out),
            "child_1": len(child_1),
            "add_ons": len(add_ons),
            "timeout_losses_4_8h": len(timeout_losses),
            "fast_winners_under_4h": len(fast_winners),
            "proof_timeouts": len(proof_timeouts),
            "actionable_timeouts_with_one_h1_available": len(actionable_timeouts),
            "proof_timeout_losses": len(proof_timeout_losses),
            "proof_timeout_winners": len(proof_timeout_winners),
        },
        "all_add_ons": compare_population(add_ons, scenarios),
        "combined_child1_actual": combined,
        "conditional_timeout_extensions_combined": compare_population(
            out, ["actual"] + conditional_scenarios
        ),
        "conditional_timeout_extensions_add_ons": compare_population(
            add_ons, ["actual"] + conditional_scenarios
        ),
        "proof_timeouts_all": compare_population(
            proof_timeouts, ["actual", "one_h1_extension"] + scenarios[1:]
        ),
        "actionable_timeouts": compare_population(
            actionable_timeouts, ["actual", "one_h1_extension"]
        ),
        "proof_timeout_losses": compare_population(
            proof_timeout_losses, ["actual", "one_h1_extension"] + scenarios[1:]
        ),
        "proof_timeout_winners": compare_population(
            proof_timeout_winners, ["actual", "one_h1_extension"] + scenarios[1:]
        ),
        "timeout_losses_4_8h": compare_population(timeout_losses, timeout_scenarios),
        "fast_winners_under_4h": compare_population(fast_winners, scenarios),
        "timeout_loss_state_summaries": state_summaries,
        "causal_contract": {
            "entries": "actual MT5 entries remain fixed",
            "h1_exit": "first opposite completed standard H1 HA, executable next H1 open",
            "fast_h4_exit": "first opposite completed FAST-R25 H4 HA, executable next H4 open",
            "std_h4_exit": "actual MT5 Journey close from the report",
            "one_h1_extension": "one additional completed H1 after actual exit; diagnostic only",
            "conditional_timeout_extensions": "post-hoc diagnostics on the consumed sample; not candidate rules",
            "selection": "no per-trade hindsight selection of the best exit",
        },
    }

    summary["proof_timeout_by_exit_state"] = {}
    for value, group in proof_timeouts.groupby("h1_path_state_by_exit", dropna=False):
        summary["proof_timeout_by_exit_state"][str(value)] = compare_population(
            group, ["actual", "one_h1_extension"]
        )

    summary["actionable_timeout_by_exit_state"] = {}
    for value, group in actionable_timeouts.groupby("h1_path_state_by_exit", dropna=False):
        summary["actionable_timeout_by_exit_state"][str(value)] = compare_population(
            group, ["actual", "one_h1_extension"]
        )

    summary["year_conditional_timeout_extensions"] = {}
    out["entry_year"] = out.entry_time.dt.year
    for year, group in out.groupby("entry_year"):
        summary["year_conditional_timeout_extensions"][str(int(year))] = compare_population(
            group, ["actual"] + conditional_scenarios
        )

    out.to_csv(arguments.output / "counterfactual_exit_ledger.csv", index=False)
    timeout_losses.to_csv(arguments.output / "timeout_loss_exit_matrix.csv", index=False)
    fast_winners.to_csv(arguments.output / "fast_winner_exit_matrix.csv", index=False)
    (arguments.output / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
