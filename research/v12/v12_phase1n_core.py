"""Pure helpers for the V12 Phase-1N lower-timeframe information audit."""

from __future__ import annotations

from datetime import datetime
import math
from typing import Iterable

import numpy as np


CONTRACT_VERSION = "v12-phase1n-lower-timeframe-temporal-information-v1"


def micro_path_features(lower: Iterable[object], direction: int, main_open: float,
                        scale: float, prefix: str) -> dict[str, float]:
    """Summarize only already-completed lower-timeframe HA records."""
    rows = list(lower)
    if not rows or not math.isfinite(scale) or scale <= 0:
        return {}
    signs = np.asarray([direction * int(row.ha_dir) for row in rows], dtype=float)
    closes = np.asarray([float(row.raw_close) for row in rows], dtype=float)
    bodies = np.asarray([direction * float(row.ha_body) for row in rows], dtype=float)
    raw_path = float(np.abs(np.diff(np.r_[main_open, closes])).sum())
    net = direction * (closes[-1] - main_open)
    return {
        f"{prefix}_aligned_fraction": float(np.mean(signs > 0)),
        f"{prefix}_directional_net_atr": float(net / scale),
        f"{prefix}_path_efficiency_signed": float(net / raw_path) if raw_path > 0 else 0.0,
        f"{prefix}_transitions": int(np.sum(signs[1:] != signs[:-1])),
        f"{prefix}_body_efficiency": float(bodies.sum() / max(np.abs(bodies).sum(), 1e-12)),
    }


def wave_distribution_features(lower: Iterable[object], direction: int, main_open: float,
                               main_high: float, main_low: float, scale: float,
                               prefix: str = "wave") -> dict[str, float]:
    """Encode a lower-bar price-time distribution without exposing later bars."""
    rows = list(lower)
    width = max(main_high - main_low, 1e-12)
    if not rows or not math.isfinite(scale) or scale <= 0:
        return {}
    typical = np.asarray([(float(r.raw_high) + float(r.raw_low) + float(r.raw_close)) / 3.0 for r in rows])
    closes = np.asarray([float(r.raw_close) for r in rows])
    opens = np.asarray([float(r.raw_open) for r in rows])
    position = np.clip((typical - main_low) / width, 0.0, 1.0)
    counts, _ = np.histogram(position, bins=np.linspace(0.0, 1.0, 9))
    probability = counts[counts > 0] / max(counts.sum(), 1)
    entropy = float(-(probability * np.log(probability)).sum() / np.log(8.0)) if len(probability) else 0.0
    median = float(np.median(position))
    path = float(np.abs(np.diff(np.r_[main_open, closes])).sum())
    directional = direction * (closes - opens)
    mass_denominator = float(np.abs(closes - opens).sum())
    favorable_mass = float(np.clip(directional, 0, None).sum() / mass_denominator) if mass_denominator > 0 else 0.5
    return {
        f"{prefix}_price_time_median": median,
        f"{prefix}_entropy_8bin": entropy,
        f"{prefix}_dispersion_atr": float(np.std(typical) / scale),
        f"{prefix}_favorable_directional_mass": favorable_mass,
        f"{prefix}_median_close_density": float(np.mean(np.abs(position - median) <= 0.10)),
        f"{prefix}_settlement_aligned": float(direction * (closes[-1] - (main_high + main_low) / 2.0) / width),
        f"{prefix}_path_efficiency_aligned": float(direction * (closes[-1] - main_open) / path) if path > 0 else 0.0,
    }


def direction_relation(child_direction: int, parent_direction: object) -> str:
    text = str(parent_direction).upper()
    if text not in {"LONG", "SHORT"}:
        return "NO_DIRECTION"
    parent = 1 if text == "LONG" else -1
    return "ALIGNED" if parent == int(child_direction) else "OPPOSED"


def age_hours(decision: datetime, observed_at: object) -> float:
    if observed_at is None or str(observed_at) in {"", "nan", "NaT"}:
        return math.nan
    value = datetime.fromisoformat(str(observed_at).replace(" ", "T"))
    if value > decision:
        raise ValueError("parent observation is later than the decision")
    return (decision - value).total_seconds() / 3600.0
