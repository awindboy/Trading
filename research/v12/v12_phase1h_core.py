"""Pure compact-head helpers for V12 Phase-1H."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


CONTRACT_VERSION = "v12-phase1h-compact-conviction-head-v1"


def train_quintile_thresholds(scores: np.ndarray) -> np.ndarray:
    values = np.asarray(scores, dtype=float)
    if len(values) < 5 or not np.isfinite(values).all():
        raise ValueError("training scores must contain at least five finite values")
    return np.quantile(values, [0.2, 0.4, 0.6, 0.8])


def apply_quintile_thresholds(scores: np.ndarray, thresholds: np.ndarray) -> np.ndarray:
    values = np.asarray(scores, dtype=float)
    cuts = np.asarray(thresholds, dtype=float)
    if cuts.shape != (4,) or np.any(cuts[1:] < cuts[:-1]):
        raise ValueError("invalid quintile thresholds")
    return np.searchsorted(cuts, values, side="right") + 1


def compact_path_derivatives(frame: pd.DataFrame, prefixes: tuple[str, ...]) -> pd.DataFrame:
    output = frame.copy()
    for prefix in prefixes:
        minutes = pd.to_numeric(output[f"{prefix}_observed_post_minutes"], errors="coerce")
        reentries = pd.to_numeric(output[f"{prefix}_outside_to_inside_reentries"], errors="coerce")
        hours = minutes / 60.0
        output[f"{prefix}_reentry_rate_per_hour"] = np.where(hours > 0, reentries / hours, 0.0)
        transition = pd.to_numeric(output[f"{prefix}_minutes_since_last_transition"], errors="coerce")
        output[f"{prefix}_log_minutes_since_last_transition"] = np.log1p(transition.clip(lower=0))
    return output


def build_h4_ha_features(market: pd.DataFrame) -> pd.DataFrame:
    work = market[["timestamp", "open", "high", "low", "close"]].copy()
    work["h4_open"] = pd.to_datetime(work["timestamp"]).dt.floor("4h")
    h4 = work.groupby("h4_open", sort=True).agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"),
        observed_m1=("timestamp", "size"),
    ).reset_index()
    previous_close = h4["close"].shift(1)
    true_range = pd.concat([
        h4["high"] - h4["low"],
        (h4["high"] - previous_close).abs(),
        (h4["low"] - previous_close).abs(),
    ], axis=1).max(axis=1)
    atr = np.full(len(h4), np.nan, dtype=float)
    if len(h4) >= 180:
        atr[179] = float(true_range.iloc[:180].mean())
        for index in range(180, len(h4)):
            atr[index] = (atr[index - 1] * 179.0 + float(true_range.iloc[index])) / 180.0
    h4["atr180"] = atr
    h4["causal_scale"] = h4["atr180"].shift(1)
    specs = {"fast": (2.0, 0.25), "std": (1.0, 0.50), "slow": (2.0, 0.75)}
    for name, (close_weight, open_alpha) in specs.items():
        close = (h4["open"] + h4["high"] + h4["low"] + close_weight * h4["close"]) / (3.0 + close_weight)
        open_values = np.full(len(h4), np.nan, dtype=float)
        if len(h4):
            open_values[0] = 0.5 * (float(h4.iloc[0]["open"]) + float(h4.iloc[0]["close"]))
            for index in range(1, len(h4)):
                open_values[index] = open_alpha * open_values[index - 1] + (1.0 - open_alpha) * float(close.iloc[index - 1])
        h4[f"{name}_open"] = open_values
        h4[f"{name}_close"] = close
        h4[f"{name}_direction"] = np.where(close >= open_values, 1, -1)
    return h4


def attach_ha_features(children: pd.DataFrame, h4: pd.DataFrame) -> pd.DataFrame:
    state = h4.set_index("h4_open")
    output = children.copy()
    output["_prior_h4_open"] = pd.to_datetime(output["decision_time"]) - pd.Timedelta(hours=4)
    rows = []
    for _, child in output.iterrows():
        bar = state.loc[child["_prior_h4_open"]]
        direction = 1 if child["direction"] == "LONG" else -1
        scale = float(bar["causal_scale"])
        item = child.to_dict()
        aligned = []
        directions = []
        for name in ("fast", "std", "slow"):
            body = direction * (float(bar[f"{name}_close"]) - float(bar[f"{name}_open"])) / scale
            flag = int(int(bar[f"{name}_direction"]) == direction)
            item[f"ha_{name}_body_aligned_atr180"] = body
            item[f"ha_{name}_aligned"] = flag
            aligned.append(flag)
            directions.append(int(bar[f"{name}_direction"]))
        item["ha_aligned_count"] = sum(aligned)
        item["ha_direction_disagreement_count"] = int(directions[0] != directions[1]) + int(directions[1] != directions[2])
        rows.append(item)
    return pd.DataFrame(rows).drop(columns=["_prior_h4_open"], errors="ignore")


TILT_MULTIPLIERS = {1: 0.75, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.25}


def capital_summary(frame: pd.DataFrame, multiplier: pd.Series | np.ndarray | None = None) -> dict[str, float]:
    if multiplier is None:
        multiplier = np.ones(len(frame), dtype=float)
    mult = np.asarray(multiplier, dtype=float)
    funded = pd.to_numeric(frame["funded_units"], errors="coerce").to_numpy(float) * mult
    stopped = pd.to_numeric(frame["stopped_loss_units"], errors="coerce").to_numpy(float) * mult
    net_r = pd.to_numeric(frame["combined_R_units"], errors="coerce").to_numpy(float) * mult
    tail = pd.to_numeric(frame["right_tail_ge_5R_units"], errors="coerce").to_numpy(float) * mult
    exposure = float(funded.sum())
    return {
        "children": int(len(frame)),
        "funded_units": exposure,
        "stopped_units": float(stopped.sum()),
        "net_R_units": float(net_r.sum()),
        "right_tail_ge_5R_units": float(tail.sum()),
        "stopped_units_per_100": float(stopped.sum() / exposure * 100.0) if exposure else np.nan,
        "net_R_per_unit": float(net_r.sum() / exposure) if exposure else np.nan,
        "right_tail_per_unit": float(tail.sum() / exposure) if exposure else np.nan,
    }


def tilt_summary(frame: pd.DataFrame) -> dict[str, float]:
    multipliers = frame["conviction_band"].map(TILT_MULTIPLIERS).to_numpy(float)
    return capital_summary(frame, multipliers)


@dataclass(frozen=True)
class Gate:
    gate: str
    passed: bool
    detail: str

