#!/usr/bin/env python3
"""Build the causal descriptive H4/H1 market-flow state ledgers.

This script is research tooling, not a trading strategy.
It intentionally uses only the consumed answer-sheet periods and enforces
information-known cutoffs so 2025-07 and the 2021 reserve are never read as
research authority.

Inputs are broker-time H4/H1 TSV exports with columns:
<DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE>

State labels are deliberately redundant: three causal views are combined by
2-of-3 majority. Disagreement is preserved as UNRESOLVED / AMBIGUOUS instead
of being forced into a direction.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

BLOCKS = [
    ("2025H1", pd.Timestamp("2025-01-01"), pd.Timestamp("2025-07-01")),
    ("2026JF", pd.Timestamp("2026-01-01"), pd.Timestamp("2026-03-01")),
]


def load_tf(path: str | Path) -> pd.DataFrame:
    d = pd.read_csv(
        path,
        sep="\t",
        usecols=["<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>"],
    )
    d["dt"] = pd.to_datetime(d["<DATE>"] + " " + d["<TIME>"], format="%Y.%m.%d %H:%M:%S")
    return d.rename(
        columns={"<OPEN>": "open", "<HIGH>": "high", "<LOW>": "low", "<CLOSE>": "close"}
    )[["dt", "open", "high", "low", "close"]]


def majority3(row: pd.Series) -> str:
    vc = row.value_counts()
    return str(vc.index[0]) if int(vc.iloc[0]) >= 2 else "AMBIGUOUS"


def state_side(st: object) -> str:
    st = str(st)
    if st.endswith("_UP"):
        return "UP"
    if st.endswith("_DOWN"):
        return "DOWN"
    if st == "BALANCE":
        return "BALANCE"
    if st == "WARMUP":
        return "WARMUP"
    return "AMBIGUOUS"


def combine_slow(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    out = []
    for aa, bb in zip(a, b):
        if aa == bb and aa in ("UP", "DOWN"):
            out.append(aa)
        elif aa in ("UP", "DOWN") and bb == "BAL":
            out.append(aa)
        elif bb in ("UP", "DOWN") and aa == "BAL":
            out.append(bb)
        else:
            out.append("BAL")
    return np.asarray(out, dtype=object)


def role_state(slow: np.ndarray, fast: np.ndarray) -> np.ndarray:
    out = []
    for s, f in zip(slow, fast):
        if s == "BAL":
            out.append("BALANCE")
        elif f == s:
            out.append("MIG_" + s)
        elif f == "BAL":
            out.append("PAUSE_" + s)
        else:
            out.append("REPAIR_" + s)
    return np.asarray(out, dtype=object)


def build_h4(raw: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for block, start, end in BLOCKS:
        x = raw[(raw.dt >= start) & (raw.dt < end)].copy().reset_index(drop=True)
        x["block"] = block
        prev = x.close.shift(1)
        tr = pd.concat(
            [x.high - x.low, (x.high - prev).abs(), (x.low - prev).abs()], axis=1
        ).max(axis=1)
        x["atr14"] = tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
        x["ema20"] = x.close.ewm(span=20, adjust=False, min_periods=20).mean()
        x["ema50"] = x.close.ewm(span=50, adjust=False, min_periods=50).mean()

        # View A: EMA slow context + 8-H4 fast price context.
        e20_lag3 = x.ema20.shift(3)
        slow_a1 = np.where(
            (x.close > x.ema20) & (x.ema20 > e20_lag3),
            "UP",
            np.where((x.close < x.ema20) & (x.ema20 < e20_lag3), "DOWN", "BAL"),
        )
        slow_a2 = np.where(
            (x.close > x.ema20) & (x.ema20 > x.ema50),
            "UP",
            np.where((x.close < x.ema20) & (x.ema20 < x.ema50), "DOWN", "BAL"),
        )
        slow_a = combine_slow(slow_a1, slow_a2)
        c8 = x.close.shift(8)
        hi8 = x.high.rolling(8, min_periods=8).max()
        lo8 = x.low.rolling(8, min_periods=8).min()
        mid8 = (hi8 + lo8) / 2
        fast_a = np.where(
            (x.close > c8) & (x.close > mid8),
            "UP",
            np.where((x.close < c8) & (x.close < mid8), "DOWN", "BAL"),
        )
        x["state_A"] = role_state(slow_a, fast_a)

        # View B: price-only 20-H4 slow / 6-H4 fast.
        c20 = x.close.shift(20)
        hi20 = x.high.rolling(20, min_periods=20).max()
        lo20 = x.low.rolling(20, min_periods=20).min()
        mid20 = (hi20 + lo20) / 2
        slow_b = np.where(
            (x.close > c20) & (x.close > mid20),
            "UP",
            np.where((x.close < c20) & (x.close < mid20), "DOWN", "BAL"),
        )
        c6 = x.close.shift(6)
        hi6 = x.high.rolling(6, min_periods=6).max()
        lo6 = x.low.rolling(6, min_periods=6).min()
        mid6 = (hi6 + lo6) / 2
        fast_b = np.where(
            (x.close > c6) & (x.close > mid6),
            "UP",
            np.where((x.close < c6) & (x.close < mid6), "DOWN", "BAL"),
        )
        x["state_B"] = role_state(slow_b, fast_b)

        # View C: EMA50 slower direction / EMA20 faster direction.
        e50_lag4 = x.ema50.shift(4)
        slow_c = np.where(
            (x.close > x.ema50) & (x.ema50 > e50_lag4),
            "UP",
            np.where((x.close < x.ema50) & (x.ema50 < e50_lag4), "DOWN", "BAL"),
        )
        x["state_C"] = role_state(slow_c, slow_a1)

        # Strict in-period warmup: do not use the locked July or Dec-2025 as warmup.
        x.loc[:55, ["state_A", "state_B", "state_C"]] = "WARMUP"

        exact = x[["state_A", "state_B", "state_C"]]
        x["role_state_majority"] = exact.apply(majority3, axis=1)
        x["role_agree_n"] = exact.apply(lambda r: int(r.value_counts().max()), axis=1)
        sides = exact.map(state_side)
        x["macro_state_majority"] = sides.apply(majority3, axis=1)
        x["macro_agree_n"] = sides.apply(lambda r: int(r.value_counts().max()), axis=1)
        x["flow_state"] = x.role_state_majority
        unresolved = (x.role_state_majority == "AMBIGUOUS") & x.macro_state_majority.isin(["UP", "DOWN"])
        x.loc[unresolved, "flow_state"] = "UNRESOLVED_" + x.loc[unresolved, "macro_state_majority"]
        x["known_at"] = x.dt + pd.Timedelta(hours=4)
        # Information-known boundary is the authority boundary.
        x = x[x.known_at < end].copy()
        parts.append(x)
    return pd.concat(parts, ignore_index=True)


def build_h4_runs(h4: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for block, g in h4.groupby("block"):
        g = g[g.flow_state != "WARMUP"].reset_index(drop=True)
        rid = (g.flow_state != g.flow_state.shift()).cumsum()
        seq = []
        for _, z in g.groupby(rid):
            seq.append(
                {
                    "block": block,
                    "state": z.flow_state.iloc[0],
                    "macro_state": z.macro_state_majority.iloc[0],
                    "start": z.dt.iloc[0],
                    "end": z.dt.iloc[-1] + pd.Timedelta(hours=4),
                    "bars": len(z),
                    "hours": len(z) * 4,
                    "open": z.open.iloc[0],
                    "close": z.close.iloc[-1],
                    "high": z.high.max(),
                    "low": z.low.min(),
                    "median_macro_agree_n": z.macro_agree_n.median(),
                    "median_role_agree_n": z.role_agree_n.median(),
                }
            )
        r = pd.DataFrame(seq)
        r["prev_state"] = r.state.shift(1)
        r["next_state"] = r.state.shift(-1)
        rows.append(r)
    return pd.concat(rows, ignore_index=True)


def build_h1(raw: pd.DataFrame, h4: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for block, start, end in BLOCKS:
        x = raw[(raw.dt >= start) & (raw.dt < end)].copy().reset_index(drop=True)
        x["block"] = block
        x["ema20"] = x.close.ewm(span=20, adjust=False, min_periods=20).mean()
        x["ema50"] = x.close.ewm(span=50, adjust=False, min_periods=50).mean()
        e20_lag3 = x.ema20.shift(3)
        x["state_ema20"] = np.where(
            (x.close > x.ema20) & (x.ema20 > e20_lag3),
            "UP",
            np.where((x.close < x.ema20) & (x.ema20 < e20_lag3), "DOWN", "BALANCE"),
        )
        c8 = x.close.shift(8)
        hi8 = x.high.rolling(8, min_periods=8).max()
        lo8 = x.low.rolling(8, min_periods=8).min()
        mid8 = (hi8 + lo8) / 2
        x["state_net_mid"] = np.where(
            (x.close > c8) & (x.close > mid8),
            "UP",
            np.where((x.close < c8) & (x.close < mid8), "DOWN", "BALANCE"),
        )
        x["state_ema_stack"] = np.where(
            (x.close > x.ema20) & (x.ema20 > x.ema50),
            "UP",
            np.where((x.close < x.ema20) & (x.ema20 < x.ema50), "DOWN", "BALANCE"),
        )
        x.loc[:49, ["state_ema20", "state_net_mid", "state_ema_stack"]] = "WARMUP"
        views = x[["state_ema20", "state_net_mid", "state_ema_stack"]]
        x["h1_state_consensus"] = views.apply(majority3, axis=1)
        x["h1_agree_n"] = views.apply(lambda r: int(r.value_counts().max()), axis=1)
        x["known_at"] = x.dt + pd.Timedelta(hours=1)
        x = x[x.known_at < end].copy()

        hh = h4[(h4.block == block) & (h4.flow_state != "WARMUP")].sort_values("known_at")
        x = pd.merge_asof(
            x.sort_values("known_at"),
            hh[["known_at", "macro_state_majority", "flow_state", "macro_agree_n", "role_agree_n"]].sort_values("known_at"),
            on="known_at",
            direction="backward",
        )

        def relation(row: pd.Series) -> str:
            H = row.macro_state_majority
            L = row.h1_state_consensus
            if H not in ("UP", "DOWN"):
                return "H4_NON_DIRECTIONAL"
            if L == H:
                return "ALIGNED"
            if L in ("UP", "DOWN"):
                return "COUNTERFLOW"
            return "LOCAL_BALANCE"

        x["h1_vs_h4_relation"] = x.apply(relation, axis=1)
        parts.append(x)
    return pd.concat(parts, ignore_index=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--h4", required=True)
    ap.add_argument("--h1", required=True)
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    h4 = build_h4(load_tf(args.h4))
    h4_runs = build_h4_runs(h4)
    h1 = build_h1(load_tf(args.h1), h4)

    h4.to_csv(out / "CONTINUOUS_H4_FLOW_STATE_LEDGER.csv", index=False)
    h4_runs.to_csv(out / "CONTINUOUS_H4_FLOW_RUN_LEDGER.csv", index=False)
    h1.to_csv(out / "CONTINUOUS_H1_NESTED_STATE_LEDGER.csv", index=False)
    print(f"H4 state rows: {len(h4)}")
    print(f"H4 runs: {len(h4_runs)}")
    print(f"H1 nested rows: {len(h1)}")


if __name__ == "__main__":
    main()
