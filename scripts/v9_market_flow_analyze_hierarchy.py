#!/usr/bin/env python3
"""Analyze the continuous H4/H1 hierarchy built by v9_market_flow_build_core.py.

Produces descriptive ledgers for nested H1 auction interruptions, H4 migration
interruptions, directional side-change buffers, state-compression coverage,
difficult-month diagnostics, and AMBIGUOUS/UNRESOLVED resolution.

No output in this script is trading authority. It is consumed-data Atlas research.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd


def h4_phase(s: object) -> str:
    s = str(s)
    if s.startswith("MIG_"):
        return "MIGRATION"
    if s.startswith(("PAUSE_", "REPAIR_", "UNRESOLVED_")):
        return "LOCAL_INTERRUPT"
    if s in ("BALANCE", "AMBIGUOUS"):
        return "NEUTRAL"
    return "UNKNOWN"


def build_h1_cycles(h1: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for block, g in h1.groupby("block"):
        d = g[
            g.macro_state_majority.isin(["UP", "DOWN"])
            & (g.h1_state_consensus != "WARMUP")
        ].copy()
        reset = (
            (d.macro_state_majority != d.macro_state_majority.shift())
            | (d.h1_vs_h4_relation != d.h1_vs_h4_relation.shift())
            | ((d.known_at - d.known_at.shift()) > pd.Timedelta(hours=2))
        )
        rid = reset.cumsum()
        rr = []
        for _, z in d.groupby(rid):
            rr.append(
                {
                    "side": z.macro_state_majority.iloc[0],
                    "relation": z.h1_vs_h4_relation.iloc[0],
                    "start": z.known_at.iloc[0],
                    "end": z.known_at.iloc[-1] + pd.Timedelta(hours=1),
                    "h1_bars": len(z),
                }
            )
        rr = pd.DataFrame(rr)
        n = 0
        for i, row in rr.iterrows():
            if row.relation != "ALIGNED":
                continue
            j = i + 1
            if j >= len(rr) or rr.loc[j, "side"] != row.side:
                continue
            if rr.loc[j, "relation"] not in ("COUNTERFLOW", "LOCAL_BALANCE"):
                continue
            side = row.side
            start = pd.Timestamp(rr.loc[j, "start"])
            path = []
            k = j
            while k < len(rr):
                if rr.loc[k, "side"] != side:
                    outcome = "H4_SIDE_CHANGED"
                    resolution = pd.Timestamp(rr.loc[k, "start"])
                    break
                path.append(rr.loc[k, "relation"])
                if rr.loc[k, "relation"] == "ALIGNED":
                    outcome = "H1_REALIGN"
                    resolution = pd.Timestamp(rr.loc[k, "start"])
                    break
                k += 1
            else:
                continue
            seg = d[(d.known_at >= start) & (d.known_at < resolution)]
            n += 1
            rows.append(
                {
                    "h1_cycle_id": f"{block}-H1C{n:03d}",
                    "block": block,
                    "h4_side": side,
                    "start": start,
                    "resolution": resolution,
                    "hours": (resolution - start).total_seconds() / 3600,
                    "path": " -> ".join(path[:-1]),
                    "outcome": outcome,
                    "h1_bars_to_resolution": len(seg),
                    "month": start.to_period("M").strftime("%Y-%m"),
                }
            )
    return pd.DataFrame(rows)


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
                    "hours": len(z) * 4,
                }
            )
        r = pd.DataFrame(seq)
        r["prev_state"] = r.state.shift(1)
        r["next_state"] = r.state.shift(-1)
        rows.append(r)
    return pd.concat(rows, ignore_index=True)


def build_h4_interruptions(runs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for block, g in runs.groupby("block"):
        g = g.reset_index(drop=True)
        n = 0
        for i, row in g.iterrows():
            st = str(row.state)
            if not st.startswith("MIG_"):
                continue
            side = st.split("_")[1]
            opp = "DOWN" if side == "UP" else "UP"
            j = i + 1
            if j >= len(g):
                continue
            local = {"PAUSE_" + side, "REPAIR_" + side, "UNRESOLVED_" + side}
            if g.loc[j, "state"] not in local:
                continue
            start = pd.Timestamp(g.loc[j, "start"])
            path = []
            k = j
            while k < len(g):
                s = str(g.loc[k, "state"])
                path.append(s)
                if s == "MIG_" + side:
                    outcome = "RESUME_SAME"
                    resolution = pd.Timestamp(g.loc[k, "start"])
                    break
                if s in ("BALANCE", "AMBIGUOUS"):
                    outcome = "NEUTRALIZE"
                    resolution = pd.Timestamp(g.loc[k, "start"])
                    break
                if s.endswith("_" + opp):
                    outcome = "OPPOSITE_TRANSITION"
                    resolution = pd.Timestamp(g.loc[k, "start"])
                    break
                k += 1
            else:
                continue
            n += 1
            rows.append(
                {
                    "interruption_id": f"{block}-INT{n:03d}",
                    "block": block,
                    "side": side,
                    "start": start,
                    "resolution": resolution,
                    "hours": (resolution - start).total_seconds() / 3600,
                    "path": " -> ".join(path[:-1]),
                    "outcome": outcome,
                    "first_interrupt_state": g.loc[j, "state"],
                    "month": start.to_period("M").strftime("%Y-%m"),
                }
            )
    return pd.DataFrame(rows)


def build_transitions(runs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for block, g in runs.groupby("block"):
        g = g.reset_index(drop=True)
        n = 0
        for i, row in g.iterrows():
            st = str(row.state)
            if not st.startswith("MIG_"):
                continue
            old = st.split("_")[1]
            opp = "DOWN" if old == "UP" else "UP"
            j = i + 1
            seq = []
            while j < len(g) and not str(g.loc[j, "state"]).startswith("MIG_"):
                seq.append(str(g.loc[j, "state"]))
                j += 1
            if j >= len(g) or g.loc[j, "state"] != "MIG_" + opp:
                continue
            n += 1
            start = pd.Timestamp(row.end)
            end = pd.Timestamp(g.loc[j, "start"])
            rows.append(
                {
                    "transition_id": f"{block}-TR{n:03d}",
                    "block": block,
                    "from_side": old,
                    "to_side": opp,
                    "start": start,
                    "end": end,
                    "buffer_hours": (end - start).total_seconds() / 3600,
                    "buffer_sequence": " -> ".join(seq),
                    "direct_migration_flip": len(seq) == 0,
                    "used_balance_or_ambiguous": any(s in ("BALANCE", "AMBIGUOUS") for s in seq),
                    "used_old_side_local_state": any(s.endswith("_" + old) for s in seq),
                    "used_new_side_local_state": any(s.endswith("_" + opp) for s in seq),
                    "month": start.to_period("M").strftime("%Y-%m"),
                }
            )
    return pd.DataFrame(rows)


def build_hierarchy(h1: pd.DataFrame) -> pd.DataFrame:
    x = h1.copy()
    x["h4_phase"] = x.flow_state.map(h4_phase)
    x["h4_confidence"] = np.where(
        x.macro_state_majority.isin(["UP", "DOWN"]),
        np.where(x.macro_agree_n >= 3, "STRONG_SIDE", "WEAK_SIDE"),
        "NO_DIRECTIONAL_AUTHORITY",
    )

    def role(r: pd.Series) -> str:
        if r.h4_phase == "NEUTRAL":
            return "NEUTRAL_AUCTION"
        if r.h1_vs_h4_relation == "ALIGNED":
            return "ALIGNED"
        if r.h1_vs_h4_relation in ("COUNTERFLOW", "LOCAL_BALANCE"):
            return "H1_INTERRUPT"
        return "UNRESOLVED"

    x["h1_core_role"] = x.apply(role, axis=1)
    x["hierarchical_state"] = x.h4_phase + "|" + x.h4_confidence + "|" + x.h1_core_role
    return x


def build_uncertainty_studies(runs: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    unresolved_rows = []
    ambiguous_rows = []
    for block, g in runs.groupby("block"):
        g = g.reset_index(drop=True)
        for idx, row in g.iterrows():
            st = str(row.state)
            if st.startswith("UNRESOLVED_"):
                side = st.split("_")[1]
                opp = "DOWN" if side == "UP" else "UP"
                prev = str(row.prev_state)
                if prev == "MIG_" + side:
                    prior = "FROM_MIGRATION"
                elif prev.endswith("_" + side):
                    prior = "FROM_SAME_SIDE_LOCAL"
                elif prev in ("BALANCE", "AMBIGUOUS"):
                    prior = "FROM_NEUTRAL"
                else:
                    prior = "FROM_OTHER"
                outcome = "END"
                resolution = pd.NaT
                for k in range(idx + 1, len(g)):
                    s = str(g.loc[k, "state"])
                    if s == "MIG_" + side:
                        outcome = "SAME_MIGRATION"; resolution = g.loc[k, "start"]; break
                    if s in ("BALANCE", "AMBIGUOUS"):
                        outcome = "NEUTRALIZED"; resolution = g.loc[k, "start"]; break
                    if s == "MIG_" + opp or s.endswith("_" + opp):
                        outcome = "OPPOSITE_SIDE"; resolution = g.loc[k, "start"]; break
                unresolved_rows.append(
                    {
                        "block": block,
                        "side": side,
                        "start": row.start,
                        "prior_category": prior,
                        "outcome": outcome,
                        "hours_to_resolution": (
                            (pd.Timestamp(resolution) - pd.Timestamp(row.start)).total_seconds() / 3600
                            if pd.notna(resolution) else np.nan
                        ),
                    }
                )
            elif st == "AMBIGUOUS":
                prior = None
                for j in range(idx - 1, -1, -1):
                    s = str(g.loc[j, "state"])
                    if s.endswith("_UP"):
                        prior = "UP"; break
                    if s.endswith("_DOWN"):
                        prior = "DOWN"; break
                next_side = None
                next_time = pd.NaT
                for k in range(idx + 1, len(g)):
                    s = str(g.loc[k, "state"])
                    if s == "MIG_UP":
                        next_side = "UP"; next_time = g.loc[k, "start"]; break
                    if s == "MIG_DOWN":
                        next_side = "DOWN"; next_time = g.loc[k, "start"]; break
                if next_side is None:
                    outcome = "END"
                elif prior is None:
                    outcome = "NO_PRIOR_DIRECTION"
                elif next_side == prior:
                    outcome = "SAME_NEXT_MIGRATION"
                else:
                    outcome = "OPPOSITE_NEXT_MIGRATION"
                ambiguous_rows.append(
                    {
                        "block": block,
                        "start": row.start,
                        "prior_directional_side": prior,
                        "next_migration_side": next_side,
                        "outcome": outcome,
                        "hours_to_next_migration": (
                            (pd.Timestamp(next_time) - pd.Timestamp(row.start)).total_seconds() / 3600
                            if pd.notna(next_time) else np.nan
                        ),
                    }
                )
    return pd.DataFrame(unresolved_rows), pd.DataFrame(ambiguous_rows)


def monthly_stress(hier: pd.DataFrame, cycles: pd.DataFrame, intr: pd.DataFrame, trans: pd.DataFrame) -> pd.DataFrame:
    valid = hier[hier.h4_phase.isin(["MIGRATION", "LOCAL_INTERRUPT", "NEUTRAL"])].copy()
    valid["month"] = valid.known_at.dt.to_period("M").astype(str)
    rows = []
    for month, g in valid.groupby("month"):
        d = g[g.macro_state_majority.isin(["UP", "DOWN"])]
        rows.append(
            {
                "month": month,
                "h1_hours": len(g),
                "directional_h4_share": len(d) / len(g),
                "strong_h4_authority_share_within_directional": (d.h4_confidence == "STRONG_SIDE").mean(),
                "weak_h4_authority_share_within_directional": (d.h4_confidence == "WEAK_SIDE").mean(),
                "h4_local_interrupt_share_all_hours": (g.h4_phase == "LOCAL_INTERRUPT").mean(),
                "h4_neutral_share_all_hours": (g.h4_phase == "NEUTRAL").mean(),
                "h1_interrupt_share_within_directional": (d.h1_core_role == "H1_INTERRUPT").mean(),
            }
        )
    out = pd.DataFrame(rows)
    c = cycles.groupby("month").agg(
        h1_cycles=("h1_cycle_id", "size"),
        h1_realign_rate=("outcome", lambda s: (s == "H1_REALIGN").mean()),
        median_h1_bars_to_resolution=("h1_bars_to_resolution", "median"),
    ).reset_index()
    i = intr.groupby("month").agg(
        h4_interruptions=("interruption_id", "size"),
        h4_resume_rate=("outcome", lambda s: (s == "RESUME_SAME").mean()),
        h4_neutralize_rate=("outcome", lambda s: (s == "NEUTRALIZE").mean()),
    ).reset_index()
    t = trans.groupby("month").agg(
        directional_side_changes=("transition_id", "size"),
        median_transition_buffer_hours=("buffer_hours", "median"),
        side_change_via_neutralization_share=("used_balance_or_ambiguous", "mean"),
    ).reset_index()
    return out.merge(c, on="month", how="left").merge(i, on="month", how="left").merge(t, on="month", how="left")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--core-dir", required=True)
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()
    core = Path(args.core_dir)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    h4 = pd.read_csv(core / "CONTINUOUS_H4_FLOW_STATE_LEDGER.csv", parse_dates=["dt", "known_at"])
    h1 = pd.read_csv(core / "CONTINUOUS_H1_NESTED_STATE_LEDGER.csv", parse_dates=["dt", "known_at"])
    runs = build_h4_runs(h4)
    cycles = build_h1_cycles(h1)
    interruptions = build_h4_interruptions(runs)
    transitions = build_transitions(runs)
    hierarchy = build_hierarchy(h1)
    unresolved, ambiguous = build_uncertainty_studies(runs)
    stress = monthly_stress(hierarchy, cycles, interruptions, transitions)

    runs.to_csv(out / "CONTINUOUS_H4_FLOW_RUN_LEDGER.csv", index=False)
    cycles.to_csv(out / "H1_AUCTION_INTERRUPTION_LEDGER.csv", index=False)
    interruptions.to_csv(out / "MIGRATION_INTERRUPTION_LEDGER.csv", index=False)
    transitions.to_csv(out / "DIRECTIONAL_TRANSITION_BUFFER_LEDGER.csv", index=False)
    hierarchy.to_csv(out / "HIERARCHICAL_FLOW_STATE_LEDGER.csv", index=False)
    unresolved.to_csv(out / "H4_UNRESOLVED_RESOLUTION_LEDGER.csv", index=False)
    ambiguous.to_csv(out / "H4_AMBIGUOUS_RESOLUTION_LEDGER.csv", index=False)
    stress.to_csv(out / "H4_H1_MONTHLY_STATE_STRESS_PROFILE.csv", index=False)

    print(f"H1 cycles: {len(cycles)}")
    print(f"H4 interruptions: {len(interruptions)}")
    print(f"Directional side changes: {len(transitions)}")
    print(f"UNRESOLVED episodes: {len(unresolved)}")
    print(f"AMBIGUOUS episodes: {len(ambiguous)}")


if __name__ == "__main__":
    main()
