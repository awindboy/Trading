#!/usr/bin/env python3
"""Generate the current V9 continuous-hierarchy research tables.

Consumes the strict core and hierarchy ledgers. All statistics are descriptive
Atlas evidence on already-consumed data. They are NOT strategy performance.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd


def macro_from_h4_state(s: object) -> str:
    s = str(s)
    if s.endswith("_UP"):
        return "UP"
    if s.endswith("_DOWN"):
        return "DOWN"
    if s == "BALANCE":
        return "BALANCE"
    return "OTHER"


def h4_phase(s: object) -> str:
    s = str(s)
    if s.startswith("MIG_"):
        return "MIGRATION"
    if s.startswith(("PAUSE_", "REPAIR_", "UNRESOLVED_")):
        return "LOCAL_INTERRUPT"
    if s in ("BALANCE", "AMBIGUOUS"):
        return "NEUTRAL"
    return "UNKNOWN"


def cross_view_cycles(h1: pd.DataFrame, h4: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for hv in ["state_A", "state_B", "state_C"]:
        for lv in ["state_ema20", "state_net_mid", "state_ema_stack"]:
            for block, g in h1.groupby("block"):
                x = g[g[lv] != "WARMUP"].sort_values("known_at").copy()
                hh = h4[(h4.block == block) & (h4[hv] != "WARMUP")].sort_values("known_at")[["known_at", hv]]
                x = pd.merge_asof(x, hh, on="known_at", direction="backward")
                x["h4_macro_test"] = x[hv].map(macro_from_h4_state)
                x = x[x.h4_macro_test.isin(["UP", "DOWN"])].copy()

                def rel(r: pd.Series) -> str:
                    if r[lv] == r.h4_macro_test:
                        return "ALIGNED"
                    if r[lv] in ("UP", "DOWN"):
                        return "COUNTERFLOW"
                    return "LOCAL_BALANCE"

                x["relation_test"] = x.apply(rel, axis=1)
                reset = (
                    (x.h4_macro_test != x.h4_macro_test.shift())
                    | (x.relation_test != x.relation_test.shift())
                    | ((x.known_at - x.known_at.shift()) > pd.Timedelta(hours=2))
                )
                rid = reset.cumsum()
                run = []
                for _, z in x.groupby(rid):
                    run.append(
                        {
                            "side": z.h4_macro_test.iloc[0],
                            "relation": z.relation_test.iloc[0],
                            "start": z.known_at.iloc[0],
                        }
                    )
                rr = pd.DataFrame(run)
                outcomes = []
                for i, r in rr.iterrows():
                    if r.relation != "ALIGNED":
                        continue
                    j = i + 1
                    if j >= len(rr) or rr.loc[j, "side"] != r.side:
                        continue
                    if rr.loc[j, "relation"] not in ("COUNTERFLOW", "LOCAL_BALANCE"):
                        continue
                    k = j
                    while k < len(rr):
                        if rr.loc[k, "side"] != r.side:
                            outcomes.append("H4_SIDE_CHANGED")
                            break
                        if rr.loc[k, "relation"] == "ALIGNED":
                            outcomes.append("H1_REALIGN")
                            break
                        k += 1
                s = pd.Series(outcomes, dtype="object")
                rows.append(
                    {
                        "h4_state_view": hv,
                        "h1_state_view": lv,
                        "block": block,
                        "cycles": len(s),
                        "h1_realign_rate": (s == "H1_REALIGN").mean() if len(s) else np.nan,
                        "h4_side_change_rate": (s == "H4_SIDE_CHANGED").mean() if len(s) else np.nan,
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    args = ap.parse_args()
    root = Path(args.dir)

    h4 = pd.read_csv(root / "CONTINUOUS_H4_FLOW_STATE_LEDGER.csv", parse_dates=["known_at", "dt"])
    h1 = pd.read_csv(root / "CONTINUOUS_H1_NESTED_STATE_LEDGER.csv", parse_dates=["known_at", "dt"])
    cycles = pd.read_csv(root / "H1_AUCTION_INTERRUPTION_LEDGER.csv", parse_dates=["start", "resolution"])
    intr = pd.read_csv(root / "MIGRATION_INTERRUPTION_LEDGER.csv", parse_dates=["start", "resolution"])
    trans = pd.read_csv(root / "DIRECTIONAL_TRANSITION_BUFFER_LEDGER.csv", parse_dates=["start", "end"])
    hier = pd.read_csv(root / "HIERARCHICAL_FLOW_STATE_LEDGER.csv", parse_dates=["known_at"])
    unresolved = pd.read_csv(root / "H4_UNRESOLVED_RESOLUTION_LEDGER.csv")
    ambiguous = pd.read_csv(root / "H4_AMBIGUOUS_RESOLUTION_LEDGER.csv")
    stress = pd.read_csv(root / "H4_H1_MONTHLY_STATE_STRESS_PROFILE.csv")

    # H1 monthly cycle stability.
    cycles["month"] = cycles.start.dt.to_period("M").astype(str)
    monthly = cycles.groupby("month").outcome.value_counts().unstack(fill_value=0).reset_index()
    for c in ["H1_REALIGN", "H4_SIDE_CHANGED"]:
        if c not in monthly:
            monthly[c] = 0
    monthly["n"] = monthly.H1_REALIGN + monthly.H4_SIDE_CHANGED
    monthly["h1_realign_rate"] = monthly.H1_REALIGN / monthly.n
    monthly.to_csv(root / "H1_AUCTION_MONTHLY_STABILITY.csv", index=False)

    # Confidence at cycle start.
    conf_rows = []
    for _, r in cycles.iterrows():
        H = h4[(h4.block == r.block) & (h4.known_at <= r.start) & (h4.flow_state != "WARMUP")]
        if H.empty:
            continue
        hb = H.iloc[-1]
        conf_rows.append(
            {
                "h1_cycle_id": r.h1_cycle_id,
                "block": r.block,
                "month": r.start.to_period("M").strftime("%Y-%m"),
                "outcome": r.outcome,
                "h4_macro_agree_n": int(hb.macro_agree_n),
                "h4_role_agree_n": int(hb.role_agree_n),
            }
        )
    conf = pd.DataFrame(conf_rows)
    conf.to_csv(root / "H1_CYCLE_STATE_CONFIDENCE_STUDY.csv", index=False)
    conf_monthly = conf.groupby(["month", "h4_macro_agree_n"]).outcome.agg(
        n="size",
        h4_side_change_rate=lambda s: (s == "H4_SIDE_CHANGED").mean(),
        h1_realign_rate=lambda s: (s == "H1_REALIGN").mean(),
    ).reset_index()
    conf_monthly.to_csv(root / "H1_CYCLE_STATE_CONFIDENCE_MONTHLY.csv", index=False)

    # Hierarchical time compression.
    valid = hier[hier.h4_phase.isin(["MIGRATION", "LOCAL_INTERRUPT", "NEUTRAL"])].copy()
    share = valid.groupby(["block", "h4_phase", "h4_confidence", "h1_core_role"]).size().rename("h1_hours").reset_index()
    share["block_hours"] = share.groupby("block").h1_hours.transform("sum")
    share["time_share"] = share.h1_hours / share.block_hours
    share = share.sort_values(["block", "time_share"], ascending=[True, False])
    share.to_csv(root / "HIERARCHICAL_FLOW_STATE_TIME_SHARE.csv", index=False)
    cov_rows = []
    for block, g in share.groupby("block"):
        z = g.sort_values("time_share", ascending=False).copy()
        z["rank"] = np.arange(1, len(z) + 1)
        z["cumulative_share"] = z.time_share.cumsum()
        for _, r in z.iterrows():
            cov_rows.append(
                {
                    "block": block,
                    "rank": int(r["rank"]),
                    "state": f"{r.h4_phase}|{r.h4_confidence}|{r.h1_core_role}",
                    "state_share": r.time_share,
                    "cumulative_share": r.cumulative_share,
                }
            )
    coverage = pd.DataFrame(cov_rows)
    coverage.to_csv(root / "HIERARCHICAL_STATE_COMPRESSION_COVERAGE.csv", index=False)

    # Transition anatomy.
    def tclass(r: pd.Series) -> str:
        if bool(r.direct_migration_flip):
            return "DIRECT_FLIP"
        if bool(r.used_balance_or_ambiguous):
            return "VIA_NEUTRALIZATION"
        if bool(r.used_new_side_local_state):
            return "VIA_NEW_SIDE_PREPARATION"
        if bool(r.used_old_side_local_state):
            return "VIA_OLD_SIDE_EROSION"
        return "OTHER"

    trans["transition_class"] = trans.apply(tclass, axis=1)
    ts = trans.groupby(["block", "transition_class"]).agg(
        n=("transition_id", "size"), median_hours=("buffer_hours", "median")
    ).reset_index()
    ts["block_total"] = ts.groupby("block").n.transform("sum")
    ts["share"] = ts.n / ts.block_total
    ts.to_csv(root / "DIRECTIONAL_TRANSITION_ANATOMY.csv", index=False)

    # Strict 2025-May comparison.
    may = stress[stress.month == "2025-05"].iloc[0]
    rest = stress[stress.month.str.startswith("2025-") & (stress.month != "2025-05")]
    cols = [
        "strong_h4_authority_share_within_directional",
        "weak_h4_authority_share_within_directional",
        "h4_local_interrupt_share_all_hours",
        "h4_neutral_share_all_hours",
        "h1_interrupt_share_within_directional",
        "h1_realign_rate",
        "median_h1_bars_to_resolution",
        "h4_resume_rate",
        "h4_neutralize_rate",
        "directional_side_changes",
        "median_transition_buffer_hours",
    ]
    comp = pd.DataFrame(
        [
            {
                "metric": c,
                "2025_05": may[c],
                "other_2025_months_mean": rest[c].mean(),
                "other_2025_months_median": rest[c].median(),
                "may_minus_other_mean": may[c] - rest[c].mean(),
            }
            for c in cols
        ]
    )
    comp.to_csv(root / "DIFFICULT_MONTH_2025_05_COMPARISON.csv", index=False)

    # Uncertainty summaries.
    urs = unresolved.groupby(["block", "prior_category", "outcome"]).size().rename("n").reset_index()
    urs["prior_total"] = urs.groupby(["block", "prior_category"]).n.transform("sum")
    urs["share"] = urs.n / urs.prior_total
    urs.to_csv(root / "H4_UNRESOLVED_RESOLUTION_SUMMARY.csv", index=False)

    ams = ambiguous.groupby(["block", "outcome"]).agg(
        n=("outcome", "size"),
        median_hours_to_next_migration=("hours_to_next_migration", "median"),
    ).reset_index()
    ams["block_total"] = ams.groupby("block").n.transform("sum")
    ams["share"] = ams.n / ams.block_total
    ams.to_csv(root / "H4_AMBIGUOUS_RESOLUTION_SUMMARY.csv", index=False)

    # Cross-view topology robustness.
    cv = cross_view_cycles(h1, h4)
    cv.to_csv(root / "H4_H1_CROSS_VIEW_NESTED_CYCLE_ROBUSTNESS.csv", index=False)

    print("Research tables generated")
    print("cross-view realign range:")
    print(cv.groupby("block").h1_realign_rate.agg(["min", "max", "mean"]))


if __name__ == "__main__":
    main()
