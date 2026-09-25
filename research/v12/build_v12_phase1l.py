#!/usr/bin/env python3
"""Build the frozen V12 Phase-1L H1 main-timeframe feasibility study."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from build_v12_phase0 import PrefixAudit, iter_m1_prefix, parse_cutoff
from build_v12_phase1d import write_csv, write_json
from v12_phase0_core import sha256_file
from v12_phase1l_core import (
    CONTRACT_VERSION, Bar, BarAggregator, HAStream, equal_stop_budget, rank_auc,
    scorecard, true_range,
)


PREFIX = "V12_PHASE1L_"
OLD_V10_CUTOFF = pd.Timestamp("2026-08-28 23:57:00")


def safe_output(path: Path, replace: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not replace:
            raise FileExistsError(path)
        for child in path.iterdir():
            if not child.is_file() or not child.name.startswith(PREFIX):
                raise ValueError(f"refusing to replace unexpected output: {child}")
            child.unlink()
    path.mkdir(parents=True, exist_ok=True)


def verify_hash(path: Path, expected: str, label: str) -> None:
    observed = sha256_file(path)
    if observed != expected:
        raise ValueError(f"{label} hash mismatch: {observed} != {expected}")


class LaneEngine:
    def __init__(self, name: str, minutes: int):
        self.name = name
        self.minutes = minutes
        self.bars: list[Bar] = []
        self.fast = HAStream(2.0, 0.25)
        self.std = HAStream(1.0, 0.50)
        self.slow = HAStream(2.0, 0.75)
        self.atr180: list[float] = []
        self.last_dir = 0
        self.run_id = 0
        self.run_k = 0
        self.run_record_ids: list[int] = []
        self.records: list[dict] = []
        self.active_ids: list[int] = []

    def update_atr(self, bar: Bar) -> None:
        i = len(self.bars) - 1
        tr = true_range(bar, self.bars[i - 1] if i else None)
        if i < 179:
            self.atr180.append(math.nan)
        elif i == 179:
            values = [true_range(candidate, self.bars[j - 1] if j else None) for j, candidate in enumerate(self.bars[:180])]
            self.atr180.append(float(np.mean(values)))
        else:
            self.atr180.append((self.atr180[-1] * 179.0 + tr) / 180.0)

    def close_record(self, record_id: int, when: datetime, price: float, reason: str, gap: bool = False) -> None:
        row = self.records[record_id]
        if row.get("exit_time") is not None:
            return
        risk = abs(float(row["entry"]) - float(row["stop"]))
        row.update(
            exit_time=when, exit=price, exit_reason=reason,
            stop_hit=int(reason.startswith("HARD_SL")), gap_stop=int(gap),
            R=int(row["dir"]) * (price - float(row["entry"])) / risk,
            position_hours=(when - row["entry_time"]).total_seconds() / 3600.0,
        )

    def finish_run(self, decision: datetime, ts: datetime, o: float, h: float, l: float) -> None:
        for record_id in self.run_record_ids:
            row = self.records[record_id]
            row["L"] = self.run_k
            row["run_end_decision"] = decision
            if row.get("exit_time") is None:
                stop = float(row["stop"])
                touched = l <= stop if int(row["dir"]) > 0 else h >= stop
                if touched:
                    self.close_record(record_id, ts, stop, "HARD_SL_NHA_SAME_M1_AMBIGUOUS",
                                      o <= stop if int(row["dir"]) > 0 else o >= stop)
                    risk = abs(float(row["entry"]) - stop)
                    row["same_m1_exit_stop_ambiguous"] = 1
                    row["alternative_fast_exit_R"] = int(row["dir"]) * (o - float(row["entry"])) / risk
                else:
                    self.close_record(record_id, ts, o, "FAST_NHA")
            row["label_available_at"] = max(decision, row["exit_time"])
        self.active_ids = [i for i in self.active_ids if self.records[i].get("exit_time") is None]
        self.run_record_ids = []

    def on_complete(self, bar: Bar, ts: datetime, o: float, h: float, l: float,
                    features: dict | None = None) -> None:
        self.bars.append(bar)
        fast = self.fast.append(bar)
        self.std.append(bar)
        self.slow.append(bar)
        self.update_atr(bar)
        decision = bar.start + timedelta(minutes=self.minutes)
        flip = self.last_dir != 0 and fast.ha_dir != self.last_dir
        if self.last_dir == 0:
            self.run_id, self.run_k = 1, 1
        elif flip:
            self.finish_run(decision, ts, o, h, l)
            self.run_id += 1
            self.run_k = 1
        else:
            self.run_k += 1
        self.last_dir = fast.ha_dir
        i = len(self.bars) - 1
        if i < 181 or ts - decision > timedelta(minutes=self.minutes):
            return
        scale = self.atr180[i - 1]
        if not math.isfinite(scale) or scale <= 0:
            return
        stop = self.std.records[i - 1].ha_low if fast.ha_dir > 0 else self.std.records[i - 1].ha_high
        if (fast.ha_dir > 0 and stop >= o) or (fast.ha_dir < 0 and stop <= o):
            return
        row = {
            "signal_id": f"{self.name}_{decision:%Y%m%d%H%M}_{'L' if fast.ha_dir > 0 else 'S'}_{self.run_k}",
            "main_tf": self.name, "decision": decision, "entry_time": ts,
            "year": decision.year, "dir": fast.ha_dir, "k": self.run_k,
            "rid": self.run_id, "entry": o, "stop": stop,
            "stop_dist_atr": abs(o - stop) / scale,
            "fast_body_atr": fast.ha_dir * fast.ha_body / scale,
            "std_align": int(self.std.records[i].ha_dir == fast.ha_dir),
            "slow_align": int(self.slow.records[i].ha_dir == fast.ha_dir),
            "exit_time": None, "exit": None, "exit_reason": None,
            "stop_hit": None, "gap_stop": 0, "same_m1_exit_stop_ambiguous": 0,
            "alternative_fast_exit_R": None, "R": None, "position_hours": None,
            "L": None, "run_end_decision": None, "label_available_at": None,
        }
        row.update(features or {})
        record_id = len(self.records)
        self.records.append(row)
        self.run_record_ids.append(record_id)
        self.active_ids.append(record_id)

    def check_stops(self, ts: datetime, o: float, h: float, l: float) -> None:
        survivors = []
        for record_id in self.active_ids:
            row = self.records[record_id]
            if row.get("exit_time") is not None:
                continue
            stop = float(row["stop"])
            touched = l <= stop if int(row["dir"]) > 0 else h >= stop
            if touched:
                gap = o <= stop if int(row["dir"]) > 0 else o >= stop
                self.close_record(record_id, ts, stop, "HARD_SL_GAP" if gap else "HARD_SL", gap)
            else:
                survivors.append(record_id)
        self.active_ids = survivors

    def frame(self) -> pd.DataFrame:
        resolved = [row for row in self.records if row.get("L") is not None and row.get("exit_time") is not None]
        return pd.DataFrame(resolved).sort_values(["decision", "signal_id"]).reset_index(drop=True)


def h1_features(bar: Bar, decision: datetime, direction: int, scale: float,
                m15: HAStream, h4: LaneEngine) -> dict:
    sub = [row for row in m15.records[-8:] if bar.start <= row.start < decision][-4:]
    if len(sub) != 4:
        return {}
    signs = np.asarray([direction * row.ha_dir for row in sub], dtype=float)
    closes = np.asarray([row.raw_close for row in sub], dtype=float)
    path = float(np.abs(np.diff(np.r_[bar.open, closes])).sum())
    net = direction * (closes[-1] - bar.open)
    bodies = np.asarray([direction * row.ha_body for row in sub], dtype=float)
    h4_fast = h4.fast.records[-1] if h4.fast.records else None
    h4_std = h4.std.records[-1] if h4.std.records else None
    h4_slow = h4.slow.records[-1] if h4.slow.records else None
    minute_of_day = decision.hour * 60 + decision.minute
    minute_of_week = decision.weekday() * 1440 + minute_of_day
    return {
        "h4_fast_align": int(h4_fast is not None and h4_fast.ha_dir == direction),
        "h4_std_align": int(h4_std is not None and h4_std.ha_dir == direction),
        "h4_slow_align": int(h4_slow is not None and h4_slow.ha_dir == direction),
        "h4_fast_run_age_hours": float(h4.run_k * 4 if h4.last_dir else 0),
        "m15_aligned_fraction": float(np.mean(signs > 0)),
        "m15_directional_net_atr": float(net / scale),
        "m15_path_efficiency_signed": float(net / path) if path > 0 else 0.0,
        "m15_transitions": int(np.sum(signs[1:] != signs[:-1])),
        "m15_body_efficiency": float(bodies.sum() / max(np.abs(bodies).sum(), 1e-12)),
        "broker_clock_sin": math.sin(2 * math.pi * minute_of_day / 1440),
        "broker_clock_cos": math.cos(2 * math.pi * minute_of_day / 1440),
        "week_clock_sin": math.sin(2 * math.pi * minute_of_week / 10080),
        "week_clock_cos": math.cos(2 * math.pi * minute_of_week / 10080),
    }


def build_ledgers(m1_path: Path, cutoff: datetime) -> tuple[pd.DataFrame, pd.DataFrame, PrefixAudit]:
    audit = PrefixAudit()
    aggregators = {15: BarAggregator(15), 60: BarAggregator(60), 240: BarAggregator(240)}
    m15 = HAStream(2.0, 0.25)
    h4 = LaneEngine("H4", 240)
    h1 = LaneEngine("H1", 60)
    for row in iter_m1_prefix(m1_path, cutoff, audit=audit):
        done15 = aggregators[15].push(row.timestamp, row.open, row.high, row.low, row.close)
        done60 = aggregators[60].push(row.timestamp, row.open, row.high, row.low, row.close)
        done240 = aggregators[240].push(row.timestamp, row.open, row.high, row.low, row.close)
        if done15 is not None:
            m15.append(done15)
        if done240 is not None:
            h4.on_complete(done240, row.timestamp, row.open, row.high, row.low)
        if done60 is not None:
            # Append H1 temporarily to derive its direction/ATR before freezing features.
            predicted_fast_close = (done60.open + done60.high + done60.low + 2.0 * done60.close) / 5.0
            if h1.fast.records:
                prev = h1.fast.records[-1]
                predicted_open = 0.25 * prev.ha_open + 0.75 * prev.ha_close
            else:
                predicted_open = 0.5 * (done60.open + done60.close)
            direction = 1 if predicted_fast_close >= predicted_open else -1
            previous = h1.bars[-1] if h1.bars else None
            tr = true_range(done60, previous)
            if len(h1.bars) >= 180 and math.isfinite(h1.atr180[-1]):
                next_atr = (h1.atr180[-1] * 179.0 + tr) / 180.0
                scale = h1.atr180[-1]
            else:
                next_atr = math.nan
                scale = math.nan
            features = h1_features(done60, done60.start + timedelta(hours=1), direction, scale, m15, h4) if math.isfinite(scale) else {}
            h1.on_complete(done60, row.timestamp, row.open, row.high, row.low, features)
        h4.check_stops(row.timestamp, row.open, row.high, row.low)
        h1.check_stops(row.timestamp, row.open, row.high, row.low)
    return h4.frame(), h1.frame(), audit


def policy_frames(h4: pd.DataFrame, h1: pd.DataFrame) -> dict[str, pd.DataFrame]:
    start = max(pd.Timestamp(h4["decision"].min()), pd.Timestamp(h1["decision"].min()))
    h4 = h4.loc[pd.to_datetime(h4["decision"]) >= start].copy()
    h1 = h1.loc[pd.to_datetime(h1["decision"]) >= start].copy()
    return {
        "H4_CORE": h4,
        "H1_CORE": h1,
        "H1_H4_FAST_ALIGNED": h1.loc[h1["h4_fast_align"] == 1].copy(),
        "H1_H4_FAST_STD_ALIGNED": h1.loc[(h1["h4_fast_align"] == 1) & (h1["h4_std_align"] == 1)].copy(),
    }


def scorecards(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    scopes = [("POOLED", lambda frame: frame)]
    scopes.extend((str(year), lambda frame, year=year: frame.loc[frame["year"] == year]) for year in range(2022, 2027))
    scopes.extend([
        ("LONG", lambda frame: frame.loc[frame["dir"] == 1]),
        ("SHORT", lambda frame: frame.loc[frame["dir"] == -1]),
    ])
    h4_scope = {}
    for scope, select in scopes:
        local = select(frames["H4_CORE"])
        if not local.empty:
            h4_scope[scope] = scorecard(local)
    for policy, frame in frames.items():
        for scope, select in scopes:
            local = select(frame)
            if local.empty:
                continue
            summary = scorecard(local)
            scale, equal_net = equal_stop_budget(summary, h4_scope[scope])
            summary["equal_stop_budget_scale"] = scale
            summary["equal_stop_budget_net_R_per_h4_unit"] = equal_net
            rows.append({"scope": scope, "policy": policy, **summary})
    return pd.DataFrame(rows)


def feature_auc(h1: pd.DataFrame) -> pd.DataFrame:
    fields = [
        "h4_fast_align", "h4_std_align", "h4_slow_align", "h4_fast_run_age_hours",
        "m15_aligned_fraction", "m15_directional_net_atr", "m15_path_efficiency_signed",
        "m15_transitions", "m15_body_efficiency", "broker_clock_sin", "broker_clock_cos",
        "week_clock_sin", "week_clock_cos",
    ]
    rows = []
    for period, frame in [("POOLED", h1)] + [(str(year), h1.loc[h1["year"] == year]) for year in range(2022, 2027)]:
        for target, values in (("HARD_SL", h1.loc[frame.index, "stop_hit"]),
                               ("RIGHT_TAIL_R_GE_5", (h1.loc[frame.index, "R"] >= 5).astype(int))):
            for field in fields:
                auc = rank_auc(values.to_numpy(int), pd.to_numeric(frame[field], errors="coerce").to_numpy(float))
                rows.append({"period": period, "target": target, "feature": field,
                             "rows": len(frame), "positives": int(values.sum()),
                             "auc_raw": auc, "auc_oriented": max(auc, 1 - auc) if math.isfinite(auc) else math.nan})
    result = pd.DataFrame(rows)
    stable = []
    for (target, field), group in result.loc[result["period"] != "POOLED"].groupby(["target", "feature"]):
        pooled = result.loc[(result["period"] == "POOLED") & (result["target"] == target) & (result["feature"] == field)].iloc[0]
        sides = np.sign(group["auc_raw"].to_numpy(float) - 0.5)
        stable_years = max(int((sides > 0).sum()), int((sides < 0).sum()))
        stable.append({"target": target, "feature": field, "stable_years_same_side": stable_years,
                       "pooled_auc_raw": pooled["auc_raw"], "pooled_auc_oriented": pooled["auc_oriented"],
                       "screen_pass": bool(stable_years >= 4 and pooled["auc_oriented"] >= 0.60)})
    return result, pd.DataFrame(stable)


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=repo / "research/v12/v12_phase1l_contract.json")
    parser.add_argument("--m1", type=Path, default=repo / "data/GOLD#/GOLD#_M1_202201030100_202609222358.csv")
    parser.add_argument("--v10-universe", type=Path, default=repo / "output/v10_ma_band_economic_rebuild_20260921/universe/V10_R3_CAUSAL_M1_UNIVERSE_2022_2026.csv")
    parser.add_argument("--output", type=Path, default=repo / "output/v12_phase1l_h1_main_timeframe_feasibility_20260925_a")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract["contract_version"] != CONTRACT_VERSION:
        raise ValueError("contract/core mismatch")
    safe_output(args.output, args.replace)
    hashes = contract["source_hashes"]
    verify_hash(args.m1, hashes["raw_m1_full_sha256"], "raw M1")
    verify_hash(args.v10_universe, hashes["v10_r3_h4_universe_sha256"], "V10 H4 universe")
    h4, h1, audit = build_ledgers(args.m1, parse_cutoff(contract["mechanism_cutoff"]))
    if audit.prefix_sha256 != hashes["raw_m1_prefix_sha256"]:
        raise ValueError("raw M1 prefix mismatch")
    frames = policy_frames(h4, h1)
    scores = scorecards(frames)
    auc, feature_screen = feature_auc(frames["H1_CORE"])
    pooled = scores.loc[scores["scope"] == "POOLED"].set_index("policy")
    years = scores.loc[scores["scope"].isin([str(y) for y in range(2022, 2027)]) & (scores["policy"] == "H1_CORE")]
    h4s, h1s = pooled.loc["H4_CORE"], pooled.loc["H1_CORE"]
    gates = {
        "POSITIVE_4_OF_5_YEARS": int((years["net_R"] > 0).sum()) >= 4,
        "STOP_DENSITY": h1s["stopped_units_per_100"] <= 1.5 * h4s["stopped_units_per_100"],
        "EQUAL_STOP_BUDGET": h1s["equal_stop_budget_net_R_per_h4_unit"] >= 0.8 * h4s["net_R_per_unit"],
        "PROFIT_FACTOR": h1s["profit_factor_R"] >= 0.9 * h4s["profit_factor_R"],
        "STOP_STREAK": h1s["max_stop_streak"] <= 2 * h4s["max_stop_streak"],
    }
    gate_frame = pd.DataFrame([{"gate": key, "passed": bool(value)} for key, value in gates.items()] + [{"gate": "OVERALL", "passed": bool(all(gates.values()))}])

    old = pd.read_csv(args.v10_universe)
    old["decision"] = pd.to_datetime(old["decision"])
    old["label_available_at"] = pd.to_datetime(old["label_available_at"])
    parity_new = h4.loc[(pd.to_datetime(h4["decision"]) <= OLD_V10_CUTOFF) & (pd.to_datetime(h4["label_available_at"]) <= OLD_V10_CUTOFF)].copy()
    joined = old[["decision", "k", "entry", "stop", "R", "stop_hit"]].merge(
        parity_new[["decision", "k", "entry", "stop", "R", "stop_hit"]], on=["decision", "k"], suffixes=("_old", "_new")
    )
    parity = {
        "old_rows": len(old), "new_rows": len(parity_new), "matched_rows": len(joined),
        "entry_max_abs_diff": float((joined["entry_old"] - joined["entry_new"]).abs().max()) if len(joined) else math.nan,
        "stop_max_abs_diff": float((joined["stop_old"] - joined["stop_new"]).abs().max()) if len(joined) else math.nan,
        "R_max_abs_diff": float((joined["R_old"] - joined["R_new"]).abs().max()) if len(joined) else math.nan,
        "stop_hit_mismatches": int((joined["stop_hit_old"] != joined["stop_hit_new"]).sum()),
    }
    outputs = {
        "V12_PHASE1L_H4_CHILD_LEDGER.csv": frames["H4_CORE"],
        "V12_PHASE1L_H1_CHILD_LEDGER.csv": frames["H1_CORE"],
        "V12_PHASE1L_SCORECARD.csv": scores,
        "V12_PHASE1L_FEATURE_AUC.csv": auc,
        "V12_PHASE1L_FEATURE_SCREEN.csv": feature_screen,
        "V12_PHASE1L_GATES.csv": gate_frame,
    }
    for name, frame in outputs.items():
        write_csv(args.output / name, frame.to_dict("records"), list(frame.columns))
    diagnostics = {
        "contract_version": CONTRACT_VERSION, "h4_rows": len(frames["H4_CORE"]),
        "h1_rows": len(frames["H1_CORE"]), "h1_viability_pass": bool(all(gates.values())),
        "feature_screen_passes": int(feature_screen["screen_pass"].sum()),
        "parity": parity, "post_cutoff_price_rows_parsed": audit.post_cutoff_price_rows_parsed,
        "raw_m1_prefix_sha256": audit.prefix_sha256,
    }
    write_json(args.output / "V12_PHASE1L_DIAGNOSTICS.json", diagnostics)
    members = []
    for path in sorted(args.output.glob(f"{PREFIX}*")):
        if path.name != "V12_PHASE1L_MANIFEST.json":
            members.append({"name": path.name, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    write_json(args.output / "V12_PHASE1L_MANIFEST.json", {"contract_version": CONTRACT_VERSION, "files": members})
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
