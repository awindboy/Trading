from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler


CUTOFF = pd.Timestamp("2026-08-28 20:00:00")


def load_mt5(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path, sep="\t")
    d["ts"] = pd.to_datetime(
        d["<DATE>"] + " " + d["<TIME>"], format="%Y.%m.%d %H:%M:%S"
    )
    return d.rename(
        columns={
            "<OPEN>": "open",
            "<HIGH>": "high",
            "<LOW>": "low",
            "<CLOSE>": "close",
            "<TICKVOL>": "tickvol",
            "<SPREAD>": "spread",
        }
    )[["ts", "open", "high", "low", "close", "tickvol", "spread"]]


def pivot_mask(d: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    h, l = d.high.to_numpy(), d.low.to_numpy()
    hi = np.zeros(len(d), dtype=bool)
    lo = np.zeros(len(d), dtype=bool)
    for i in range(2, len(d) - 2):
        hi[i] = h[i] > max(h[i - 2], h[i - 1]) and h[i] >= max(h[i + 1], h[i + 2])
        lo[i] = l[i] < min(l[i - 2], l[i - 1]) and l[i] <= min(l[i + 1], l[i + 2])
    return hi, lo


def build_destinations(d: pd.DataFrame, minutes: int, source: str) -> pd.DataFrame:
    hi, lo = pivot_mask(d)
    rows: list[dict] = []
    for kind, mask, values, touch_values in (
        (1, hi, d.high.to_numpy(), d.high.to_numpy()),
        (-1, lo, d.low.to_numpy(), d.low.to_numpy()),
    ):
        for i in np.flatnonzero(mask):
            confirm_i = i + 3
            if confirm_i >= len(d):
                continue
            level = float(values[i])
            if kind > 0:
                hit = np.flatnonzero(touch_values[confirm_i:] >= level - 1e-12)
            else:
                hit = np.flatnonzero(touch_values[confirm_i:] <= level + 1e-12)
            first_touch = pd.NaT if len(hit) == 0 else pd.Timestamp(d.ts.iloc[confirm_i + int(hit[0])])
            rows.append(
                {
                    "dest_kind": kind,
                    "dest_level": level,
                    "dest_pivot_time": pd.Timestamp(d.ts.iloc[i]),
                    "dest_known_time": pd.Timestamp(d.ts.iloc[confirm_i]),
                    "dest_consumed_time": first_touch,
                    "dest_source": source,
                }
            )
    return pd.DataFrame(rows).sort_values(["dest_known_time", "dest_level"]).reset_index(drop=True)


def attach_route_features(events: pd.DataFrame, destinations: pd.DataFrame) -> pd.DataFrame:
    out: list[dict] = []
    for r in events.itertuples(index=False):
        known = destinations[
            (destinations.dest_known_time <= r.event_ts)
            & (destinations.dest_kind == r.direction)
            & (destinations.dest_consumed_time.isna() | (destinations.dest_consumed_time > r.event_ts))
        ].copy()
        if r.direction > 0:
            known = known[known.dest_level > r.entry + 1e-12]
            known["distance"] = known.dest_level - r.entry
        else:
            known = known[known.dest_level < r.entry - 1e-12]
            known["distance"] = r.entry - known.dest_level
        known = known.sort_values(["distance", "dest_known_time", "dest_source"])
        rec: dict = {
            "event_ts": r.event_ts,
            "h4_run_id": r.h4_run_id,
            "direction": r.direction,
            "route_available": int(len(known) > 0),
            "route_count": len(known),
        }
        for rank in (1, 2, 3):
            if len(known) >= rank:
                z = known.iloc[rank - 1]
                rec[f"dest{rank}_level"] = float(z.dest_level)
                rec[f"dest{rank}_distance_atr"] = float(z.distance / r.atr)
                rec[f"dest{rank}_age_h"] = float((r.event_ts - z.dest_known_time).total_seconds() / 3600.0)
                rec[f"dest{rank}_is_h1"] = int(z.dest_source == "H1")
                # Exact level clustering is a causal hierarchy/confluence descriptor.
                rec[f"dest{rank}_multiplicity"] = int(
                    np.isclose(known.dest_level.to_numpy(), float(z.dest_level), atol=0.005).sum()
                )
            else:
                rec[f"dest{rank}_level"] = np.nan
                rec[f"dest{rank}_distance_atr"] = np.nan
                rec[f"dest{rank}_age_h"] = np.nan
                rec[f"dest{rank}_is_h1"] = 0
                rec[f"dest{rank}_multiplicity"] = 0
        rec["dest12_gap_atr"] = rec["dest2_distance_atr"] - rec["dest1_distance_atr"]
        rec["dest23_gap_atr"] = rec["dest3_distance_atr"] - rec["dest2_distance_atr"]
        out.append(rec)
    return events.merge(pd.DataFrame(out), on=["event_ts", "h4_run_id", "direction"], how="left")


def label_delivery(events: pd.DataFrame, m1: pd.DataFrame) -> pd.DataFrame:
    times = m1.ts.to_numpy(dtype="datetime64[ns]")
    highs, lows = m1.high.to_numpy(), m1.low.to_numpy()
    delivered, delivered_at = [], []
    for r in events.itertuples(index=False):
        if not r.route_available:
            delivered.append(0)
            delivered_at.append(pd.NaT)
            continue
        a = int(np.searchsorted(times, np.datetime64(r.event_ts), side="left"))
        b = int(np.searchsorted(times, np.datetime64(r.exit_time_fb), side="left"))
        if b <= a:
            delivered.append(0)
            delivered_at.append(pd.NaT)
            continue
        mask = highs[a:b] >= r.dest1_level - 1e-12 if r.direction > 0 else lows[a:b] <= r.dest1_level + 1e-12
        idx = np.flatnonzero(mask)
        if len(idx):
            j = a + int(idx[0])
            delivered.append(1)
            delivered_at.append(pd.Timestamp(times[j]))
        else:
            delivered.append(0)
            delivered_at.append(pd.NaT)
    z = events.copy()
    z["destination_delivered"] = delivered
    z["destination_delivery_time"] = delivered_at
    return z


BASE_FEATURES = [
    "depth", "depth_atr", "depth_max", "depth_atr_max", "impulse_atr",
    "pullback_h", "h4_run_age", "prior_env", "env_ratio", "env_ratio_max",
    "prior_success_n", "env_available", "env_breach", "env_breach_any",
    "poi_width_atr", "poi_age_h", "pen_wick", "pen_close", "rej_atr", "acc_atr",
    "m15_body_atr", "m15_range_atr", "m15_close_loc", "m15_opp_wick_atr",
    "m15_tv_rel", "m15_path_eff", "m15_aligned_frac", "m15_path_body_atr",
    "depth_slope3", "h1_align", "h1_body_atr", "h1_rng_atr", "h4_ha_body_atr",
    "h4_ha_rng_atr", "h4_raw_close_vs_ha", "has_fvg", "has_ob", "is_reject",
    "is_inside", "is_accept", "object_n",
]

ROUTE_FEATURES = [
    "route_count", "dest1_distance_atr", "dest1_age_h", "dest1_is_h1",
    "dest1_multiplicity", "dest2_distance_atr", "dest2_age_h", "dest2_is_h1",
    "dest2_multiplicity", "dest3_distance_atr", "dest3_age_h", "dest3_is_h1",
    "dest3_multiplicity", "dest12_gap_atr", "dest23_gap_atr",
]


def model(features: list[str]) -> Pipeline:
    return Pipeline(
        [
            (
                "prep",
                ColumnTransformer(
                    [
                        (
                            "n",
                            Pipeline(
                                [
                                    ("impute", SimpleImputer(strategy="median")),
                                    ("scale", RobustScaler(quantile_range=(10, 90))),
                                ]
                            ),
                            features,
                        )
                    ]
                ),
            ),
            ("model", LogisticRegression(C=0.5, max_iter=2500)),
        ]
    )


def build_oof(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, metrics = [], []
    feature_sets = {"STATE": BASE_FEATURES, "STATE_ROUTE": BASE_FEATURES + ROUTE_FEATURES}
    for year in (2023, 2024, 2025, 2026):
        train = d[(d.year < year) & (d.exit_time_fb < pd.Timestamp(f"{year}-01-01")) & d.route_available.eq(1)]
        test = d[(d.year == year) & d.route_available.eq(1)].copy()
        if len(train) < 100 or test.empty:
            continue
        predictions: dict[str, np.ndarray] = {}
        for name, features in feature_sets.items():
            m = model(features)
            m.fit(train[features], train.destination_delivered)
            p = m.predict_proba(test[features])[:, 1]
            predictions[name] = p
            metrics.append(
                {
                    "year": year,
                    "model": name,
                    "train_n": len(train),
                    "test_n": len(test),
                    "auc": roc_auc_score(test.destination_delivered, p),
                }
            )
        z = test[[
            "event_ts", "h4_run_id", "direction", "year", "entry", "atr",
            "exit_time_fb", "exit_px_fb", "pnl_usd_1u_fb", "pnl_atr_fb",
            "dest1_level", "dest1_distance_atr", "destination_delivered",
            "destination_delivery_time",
        ]].copy()
        z["p_delivery_state"] = predictions["STATE"]
        z["p_delivery_route"] = predictions["STATE_ROUTE"]
        no_delivery = train[train.destination_delivered.eq(0)]
        fail_loss_atr = float((-no_delivery.pnl_atr_fb.clip(upper=0)).mean())
        z["prior_failure_loss_atr"] = fail_loss_atr
        z["hurdle_ev"] = z.p_delivery_route * z.dest1_distance_atr - (1 - z.p_delivery_route) * fail_loss_atr
        rows.append(z)
    return pd.concat(rows, ignore_index=True), pd.DataFrame(metrics)


def apply_q75(oof: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    selected, thresholds = [], []
    for year in (2024, 2025, 2026):
        prior = oof[oof.year < year].hurdle_ev.dropna()
        test = oof[oof.year.eq(year)].copy()
        if prior.empty or test.empty:
            continue
        threshold = float(prior.quantile(0.75))
        test["q75_threshold"] = threshold
        test["q75_admitted"] = test.hurdle_ev >= threshold
        selected.append(test)
        thresholds.append({"year": year, "prior_oof_n": len(prior), "q75_threshold": threshold})
    return pd.concat(selected, ignore_index=True), pd.DataFrame(thresholds)


def repair_oof(route: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Score one additional correction cycle only at a known envelope breach.

    The target is that breach event's own first-future-breach/H4-flip P/L in
    ATR units. Thus a high score authorizes exactly one existing K0 cycle; it
    does not manufacture a new exit horizon or inspect a later path at action
    time.
    """
    features = BASE_FEATURES + ROUTE_FEATURES
    breach = route[route.env_breach_any.eq(1) & route.route_available.eq(1)].copy()
    rows: list[pd.DataFrame] = []
    diagnostics: list[dict] = []
    for year in (2023, 2024, 2025, 2026):
        train = breach[(breach.year < year) & (breach.exit_time_fb < pd.Timestamp(f"{year}-01-01"))]
        test = breach[breach.year.eq(year)].copy()
        if len(train) < 100 or test.empty:
            continue
        reg = Pipeline(
            [
                (
                    "prep",
                    ColumnTransformer(
                        [
                            (
                                "n",
                                Pipeline(
                                    [
                                        ("impute", SimpleImputer(strategy="median")),
                                        ("scale", RobustScaler(quantile_range=(10, 90))),
                                    ]
                                ),
                                features,
                            )
                        ]
                    ),
                ),
                ("model", Ridge(alpha=10.0)),
            ]
        )
        lo, hi = train.pnl_atr_fb.quantile([0.01, 0.99])
        reg.fit(train[features], train.pnl_atr_fb.clip(lo, hi))
        test["repair_score"] = reg.predict(test[features])
        diagnostics.append(
            {
                "year": year,
                "train_n": len(train),
                "test_n": len(test),
                "score_outcome_corr": float(test.repair_score.corr(test.pnl_atr_fb, method="spearman")),
            }
        )
        rows.append(
            test[[
                "event_ts", "h4_run_id", "direction", "year", "entry", "atr",
                "exit_time_fb", "exit_px_fb", "pnl_usd_1u_fb", "pnl_atr_fb",
                "repair_score",
            ]]
        )
    return pd.concat(rows, ignore_index=True), pd.DataFrame(diagnostics)


def apply_q50_repair(
    admitted: pd.DataFrame, repair: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    thresholds: list[dict] = []
    by_year: dict[int, float] = {}
    for year in (2024, 2025, 2026):
        prior = repair[repair.year < year].repair_score.dropna()
        if prior.empty:
            continue
        by_year[year] = float(prior.quantile(0.50))
        thresholds.append({"year": year, "prior_oof_n": len(prior), "q50_threshold": by_year[year]})

    key = repair.set_index(["event_ts", "h4_run_id", "direction"])
    rows: list[dict] = []
    for r in admitted.itertuples(index=False):
        rec = r._asdict()
        rec["policy_exit_time"] = r.exit_time_fb
        rec["policy_exit_price"] = r.exit_px_fb
        rec["policy_exit_reason"] = "K0_FIRST_BREACH_OR_H4_FLIP"
        rec["repair_score"] = np.nan
        rec["q50_threshold"] = by_year.get(int(r.year), np.nan)
        rec["repair_allowed"] = 0
        if int(r.destination_delivered) == 1 and r.exit_time_fb < CUTOFF:
            k = (pd.Timestamp(r.exit_time_fb), int(r.h4_run_id), int(r.direction))
            if k in key.index:
                b = key.loc[k]
                if isinstance(b, pd.DataFrame):
                    b = b.iloc[0]
                rec["repair_score"] = float(b.repair_score)
                if float(b.repair_score) >= rec["q50_threshold"]:
                    rec["repair_allowed"] = 1
                    rec["policy_exit_time"] = pd.Timestamp(b.exit_time_fb)
                    rec["policy_exit_price"] = float(b.exit_px_fb)
                    rec["policy_exit_reason"] = "Q50_ONE_REPAIR_CYCLE"
        rec["policy_pnl_usd"] = float(r.direction * (rec["policy_exit_price"] - r.entry))
        rows.append(rec)
    return pd.DataFrame(rows), pd.DataFrame(thresholds)


def build_policy_ledger(policy: pd.DataFrame) -> pd.DataFrame:
    records: list[dict] = []
    for seq, r in enumerate(policy.sort_values(["event_ts", "h4_run_id"]).itertuples(index=False), start=1):
        event_id = f"LTF{seq:06d}"
        side = "LONG" if r.direction > 0 else "SHORT"
        records.append(
            {
                "event_id": event_id,
                "action_time": pd.Timestamp(r.event_ts),
                "action_order": 1,
                "action": "ENTRY",
                "direction": side,
                "volume": "0.01",
                "policy_lane": "LTF_Q75",
                "reason": "HURDLE_EV_Q75",
                "expected_price": f"{r.entry:.5f}",
            }
        )
        records.append(
            {
                "event_id": event_id,
                "action_time": pd.Timestamp(r.policy_exit_time),
                "action_order": 0,
                "action": "EXIT",
                "direction": side,
                "volume": "0.01",
                "policy_lane": "LTF_Q75",
                "reason": r.policy_exit_reason,
                "expected_price": f"{r.policy_exit_price:.5f}",
            }
        )
    ledger = pd.DataFrame(records)
    return ledger.sort_values(["action_time", "action_order", "event_id"]).reset_index(drop=True)


def load_sa1_child1(report: Path) -> pd.DataFrame:
    raw = pd.read_excel(report, sheet_name=0, header=None, dtype=object)
    deals = raw.loc[raw[4].isin(["in", "out"]), list(range(13))].copy()
    deals.columns = [
        "time", "deal", "symbol", "type", "direction", "volume", "price",
        "order", "commission", "swap", "profit", "balance", "comment",
    ]
    deals["time"] = pd.to_datetime(deals.time, format="%Y.%m.%d %H:%M:%S")
    for col in ["deal", "volume", "price", "order", "commission", "swap", "profit", "balance"]:
        deals[col] = pd.to_numeric(deals[col], errors="coerce")
    cre = re.compile(r"^V13SA1\|J(?P<journey>\d{6})\|C(?P<child>\d{2})\|(?P<side>[LS])$")
    opened: list[dict] = []
    closed: list[dict] = []
    for r in deals.sort_values(["time", "deal"]).itertuples(index=False):
        if r.direction == "in":
            match = cre.match(str(r.comment).strip()) if pd.notna(r.comment) else None
            if match:
                opened.append(
                    {
                        "journey": int(match.group("journey")),
                        "child": int(match.group("child")),
                        "side": 1 if match.group("side") == "L" else -1,
                        "entry_time": r.time,
                        "entry_price": float(r.price),
                        "volume": float(r.volume),
                        "entry_deal": int(r.deal),
                    }
                )
            continue
        close_side = 1 if r.type == "sell" else -1
        candidates = []
        for i, position in enumerate(opened):
            if position["side"] == close_side and abs(position["volume"] - float(r.volume)) < 1e-12:
                pnl_error = abs(position["side"] * (float(r.price) - position["entry_price"]) - float(r.profit))
                candidates.append((pnl_error, position["entry_time"], i, position))
        if not candidates:
            continue
        _, _, i, position = min(candidates, key=lambda x: (x[0], x[1], x[2]))
        opened.pop(i)
        closed.append(
            {
                **position,
                "exit_time": r.time,
                "exit_price": float(r.price),
                "profit": float(r.profit),
                "exit_deal": int(r.deal),
            }
        )
    c1 = pd.DataFrame(closed)
    return c1[
        c1.child.eq(1)
        & c1.entry_time.ge(pd.Timestamp("2024-01-01"))
        & c1.exit_time.le(CUTOFF)
    ].copy()


def build_combined_ledger(c1: pd.DataFrame, ltf_policy: pd.DataFrame) -> pd.DataFrame:
    records: list[dict] = []
    for seq, r in enumerate(c1.sort_values(["entry_time", "journey"]).itertuples(index=False), start=1):
        event_id = f"C1{seq:06d}"
        side = "LONG" if r.side > 0 else "SHORT"
        records.extend(
            [
                {
                    "event_id": event_id, "action_time": r.entry_time, "action_order": 1,
                    "action": "ENTRY", "direction": side, "volume": "0.01",
                    "policy_lane": "C1_BASELINE0", "reason": "H4_HA_JOURNEY_BIRTH",
                    "expected_price": f"{r.entry_price:.5f}",
                },
                {
                    "event_id": event_id, "action_time": r.exit_time, "action_order": 0,
                    "action": "EXIT", "direction": side, "volume": "0.01",
                    "policy_lane": "C1_BASELINE0", "reason": "OPPOSITE_H4_HA",
                    "expected_price": f"{r.exit_price:.5f}",
                },
            ]
        )
    ltf = build_policy_ledger(ltf_policy)
    records.extend(ltf.to_dict(orient="records"))
    return pd.DataFrame(records).sort_values(["action_time", "action_order", "event_id"]).reset_index(drop=True)


def combined_metrics(c1: pd.DataFrame, ltf: pd.DataFrame) -> dict:
    a = c1[["entry_time", "exit_time", "profit"]].copy()
    a["tie"] = c1.exit_deal.to_numpy()
    b = pd.DataFrame(
        {
            "entry_time": ltf.event_ts,
            "exit_time": ltf.policy_exit_time,
            "profit": ltf.policy_pnl_usd,
            "tie": np.arange(len(ltf)) + 10_000_000,
        }
    )
    x = pd.concat([a, b], ignore_index=True).sort_values(["exit_time", "tie"])
    x = x.rename(columns={"exit_time": "exit_time_fb"})
    x["event_ts"] = x.entry_time
    return metrics(x, "profit")


def metrics(d: pd.DataFrame, pnl_col: str) -> dict:
    x = d.sort_values(["exit_time_fb", "event_ts"])[pnl_col].to_numpy(float)
    w, l = x[x > 0], x[x < 0]
    eq = np.cumsum(x)
    peak = np.maximum.accumulate(np.r_[0.0, eq])
    dd = float(np.max(peak[1:] - eq)) if len(eq) else 0.0
    streak = cur = 0
    for value in x:
        if value < 0:
            cur += 1
            streak = max(streak, cur)
        else:
            cur = 0
    return {
        "n": len(x), "wins": int((x > 0).sum()), "losses": int((x < 0).sum()),
        "flats": int((x == 0).sum()), "win_rate": float((x > 0).sum() / max(1, (x != 0).sum())),
        "net": float(x.sum()), "pf": float(w.sum() / -l.sum()) if len(l) else None,
        "avg_win": float(w.mean()) if len(w) else None, "avg_loss": float(l.mean()) if len(l) else None,
        "payoff": float(w.mean() / -l.mean()) if len(w) and len(l) else None,
        "expectancy": float(x.mean()) if len(x) else None, "realized_dd": dd, "max_loss_streak": streak,
    }


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--clusters", type=Path, required=True)
    p.add_argument("--m1", type=Path, required=True)
    p.add_argument("--m30", type=Path, required=True)
    p.add_argument("--h1", type=Path, required=True)
    p.add_argument("--sa1-report", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    events = pd.read_csv(args.clusters, parse_dates=["event_ts", "flip_time", "exit_time_fb"])
    events = events[events.event_ts <= CUTOFF].copy()
    m30, h1, m1 = load_mt5(args.m30), load_mt5(args.h1), load_mt5(args.m1)
    destinations = pd.concat(
        [build_destinations(m30, 30, "M30"), build_destinations(h1, 60, "H1")], ignore_index=True
    )
    route = attach_route_features(events, destinations)
    route = label_delivery(route, m1)
    oof, auc = build_oof(route)
    policy, thresholds = apply_q75(oof)
    admitted = policy[policy.q75_admitted].copy()
    repair, repair_diag = repair_oof(route)
    final_policy, repair_thresholds = apply_q50_repair(admitted, repair)
    ledger = build_policy_ledger(final_policy)
    c1 = load_sa1_child1(args.sa1_report)
    combined_ledger = build_combined_ledger(c1, final_policy)

    files = {
        "destinations": args.output / "v13_route_destinations.csv",
        "route_dataset": args.output / "v13_route_dataset.csv",
        "oof": args.output / "v13_route_delivery_oof.csv",
        "auc": args.output / "v13_route_auc.csv",
        "thresholds": args.output / "v13_route_q75_thresholds.csv",
        "admitted": args.output / "v13_route_q75_admitted.csv",
        "repair_oof": args.output / "v13_route_q50_repair_oof.csv",
        "repair_diagnostics": args.output / "v13_route_q50_repair_diagnostics.csv",
        "repair_thresholds": args.output / "v13_route_q50_thresholds.csv",
        "final_policy": args.output / "v13_route_q75_q50_policy.csv",
        "policy_ledger": args.output / "v13_ltf_route_q75_q50_policy_ledger.csv",
        "c1": args.output / "v13_child1_actual_reference.csv",
        "combined_policy_ledger": args.output / "v13_c1_ltf_route_q75_q50_policy_ledger.csv",
    }
    destinations.to_csv(files["destinations"], index=False)
    route.to_csv(files["route_dataset"], index=False)
    oof.to_csv(files["oof"], index=False)
    auc.to_csv(files["auc"], index=False)
    thresholds.to_csv(files["thresholds"], index=False)
    admitted.to_csv(files["admitted"], index=False)
    repair.to_csv(files["repair_oof"], index=False)
    repair_diag.to_csv(files["repair_diagnostics"], index=False)
    repair_thresholds.to_csv(files["repair_thresholds"], index=False)
    final_policy.to_csv(files["final_policy"], index=False)
    ledger.to_csv(files["policy_ledger"], index=False, date_format="%Y-%m-%d %H:%M:%S")
    c1.to_csv(files["c1"], index=False, date_format="%Y-%m-%d %H:%M:%S")
    combined_ledger.to_csv(files["combined_policy_ledger"], index=False, date_format="%Y-%m-%d %H:%M:%S")
    summary = {
        "contract": "V13_LTF_ROUTE_Q75_Q50_ACTION_CONTRACT_20260929",
        "cutoff": str(CUTOFF),
        "route_events": len(route),
        "route_available": int(route.route_available.sum()),
        "destination_delivery": int(route.destination_delivered.sum()),
        "auc": auc.to_dict(orient="records"),
        "thresholds": thresholds.to_dict(orient="records"),
        "q75_k0": metrics(admitted, "pnl_usd_1u_fb"),
        "repair_diagnostics": repair_diag.to_dict(orient="records"),
        "repair_thresholds": repair_thresholds.to_dict(orient="records"),
        "q75_q50": metrics(final_policy.assign(exit_time_fb=final_policy.policy_exit_time), "policy_pnl_usd"),
        "repair_allowed": int(final_policy.repair_allowed.sum()),
        "ledger_rows": len(ledger),
        "child1_n": len(c1),
        "combined": combined_metrics(c1, final_policy),
        "combined_ledger_rows": len(combined_ledger),
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    manifest = {name: {"path": path.name, "sha256": sha256(path), "bytes": path.stat().st_size} for name, path in files.items()}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
