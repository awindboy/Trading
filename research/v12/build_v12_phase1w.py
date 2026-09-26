"""Frozen failed-seed footprint diagnostic; no action authority."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from build_v12_phase1u import UniverseBuilder, read_m1, EXPECTED_M1
from build_v12_phase1v import REPO, load_sources, sha256_file, verify, save_csv, save_json


class FootprintBuilder(UniverseBuilder):
    def _h4_feature_row(self, bar, decision, entry_time, entry):
        row = super()._h4_feature_row(bar, decision, entry_time, entry)
        if row is not None:
            row.update(signal_low=bar.low, signal_high=bar.high,
                       signal_close=bar.close, signal_open=bar.open,
                       causal_atr180=self.atr180[len(self.h4_bars) - 2])
        return row


def footprint_state(price, low, high, direction):
    if low <= price <= high:
        return "INSIDE"
    favorable = price > high if direction > 0 else price < low
    return "OUTSIDE_FAVORABLE" if favorable else "OUTSIDE_OPPOSED"


def decisions(seeds):
    rows = []
    previous = None
    for row in seeds.sort_values("decision").to_dict("records"):
        d = {key: row[key] for key in (
            "run_id", "decision", "direction", "signal_low",
            "signal_high", "signal_close", "causal_atr180")}
        d.update(reference_run_id=np.nan, reference_exit=pd.NaT, known_prior_loss=0,
                 h4_state="UNAVAILABLE", risk_state="UNAVAILABLE",
                 side_relation="UNAVAILABLE", displacement_atr=np.nan, overlap=np.nan,
                 prior_signal_low=np.nan, prior_signal_high=np.nan,
                 prior_entry=np.nan, prior_stop=np.nan)
        if previous is not None:
            d["reference_run_id"] = previous["run_id"]
            # Equality deliberately unavailable: M1 cannot establish event order.
            known = previous["exit_time"] < row["decision"]
            d["known_prior_loss"] = int(known and previous["R"] < 0)
            if known:
                d.update(reference_exit=previous["exit_time"],
                         prior_signal_low=previous["signal_low"], prior_signal_high=previous["signal_high"],
                         prior_entry=previous["entry"], prior_stop=previous["stop"])
                direction = 1 if row["direction"] == "LONG" else -1
                d["h4_state"] = footprint_state(row["signal_close"], previous["signal_low"], previous["signal_high"], direction)
                d["risk_state"] = footprint_state(row["signal_close"], min(previous["entry"], previous["stop"]), max(previous["entry"], previous["stop"]), direction)
                d["side_relation"] = "SAME" if row["direction"] == previous["direction"] else "OPPOSITE"
                scale = row["causal_atr180"]
                d["displacement_atr"] = direction * (row["signal_close"] - previous["signal_close"]) / scale
                intersection = max(0, min(row["signal_high"], previous["signal_high"]) - max(row["signal_low"], previous["signal_low"]))
                union = max(row["signal_high"], previous["signal_high"]) - min(row["signal_low"], previous["signal_low"])
                d["overlap"] = intersection / union if union else 0
        d["skip_h4"] = int(d["known_prior_loss"] and d["h4_state"] == "INSIDE")
        d["skip_risk"] = int(d["known_prior_loss"] and d["risk_state"] == "INSIDE")
        rows.append(d)
        previous = row
    return pd.DataFrame(rows)


def stats(episodes, children):
    c = children.loc[children.run_id.isin(episodes.run_id)]
    terminal = c.groupby("exit_time")["combined_R_units"].sum().sort_index()
    equity = np.r_[0., terminal.cumsum().to_numpy()]
    negatives = episodes.net_R_units < 0
    positives = episodes.net_R_units > 0
    best = streak = repeat = 0
    for loss in negatives:
        if loss:
            repeat += int(streak > 0)
            streak += 1
        else:
            streak = 0
        best = max(best, streak)
    gross_loss = -float(episodes.loc[negatives, "net_R_units"].sum())
    gross_win = float(episodes.loc[positives, "net_R_units"].sum())
    return dict(episodes=len(episodes), positive=int(positives.sum()), negative=int(negatives.sum()),
                win_rate=float(positives.mean()) if len(episodes) else None,
                first_stops=int(episodes.first_child_hard_sl.sum()),
                repeated_negative=repeat, max_negative_streak=best,
                weighted_R=float(episodes.net_R_units.sum()),
                seed_unweighted_R=float(episodes.seed_R.sum()),
                seed_wins=int((episodes.seed_R > 0).sum()),
                tail_weighted_5=int((episodes.tail_units > 0).sum()),
                tail_unweighted_5=int(episodes.true_tail.sum()),
                funded_units=float(c.funded_units.sum()),
                stopped_units=float(c.stopped_loss_units.sum()),
                realized_R_drawdown=float(np.max(np.maximum.accumulate(equity) - equity)),
                episode_profit_factor=gross_win/gross_loss if gross_loss else None,
                weighted_R_per_unit=float(c.combined_R_units.sum()/c.funded_units.sum()) if len(c) else None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.out_dir.resolve()
    assert (REPO / "output").resolve() in out.parents
    out.mkdir(parents=True, exist_ok=False)
    contract = json.loads((REPO / "research/v12/v12_phase1v_contract.json").read_text())
    rp = REPO / "output/v12_phase1i_run_episode_reverse_engineering_20260924_a/V12_PHASE1I_RUN_EPISODES.csv"
    cp = REPO / "output/v12_phase1k_staged_funding_counterfactual_20260924_a/V12_PHASE1K_CHILD_POLICY_LEDGER.csv"
    op = REPO / "output/v12_phase1u_multispeed_ha_ownership_20260926_a/V12_PHASE1U_CHILD_LEDGER.csv"
    for p, k in ((rp, "phase1i_run_episodes_sha256"), (cp, "phase1k_child_policy_ledger_sha256"), (op, "phase1u_child_ledger_sha256")):
        verify(p, contract["source_hashes"][k], k)
    episodes, children, quality = load_sources(rp, cp, op, pd.Timestamp(contract["common_window_end_inclusive"]))
    gp = REPO / "output/v12_phase1g_continuous_intraday_path_20260924_a/V12_PHASE1G_V10_CHILD_PATH_CONTEXT.csv"
    verify(gp, "ec480d372adb76c3f9ee452430bd4fb4d15444f7e3ffae8a555249697a8f05bd", "phase1g")
    context = pd.read_csv(gp, usecols=["signal_id", "event", "R", "exit_time", "combined_R_units"])
    quality["selected_signal_status"] = context.event.value_counts().to_dict()
    quality["selected_status_weighted_R"] = context.groupby("event").combined_R_units.sum().to_dict()
    assert set(children.signal_id) == set(context.loc[context.event == "ENTRY", "signal_id"])
    context["exit_time"] = pd.to_datetime(context.exit_time)
    children = children.merge(context[["signal_id", "R", "exit_time"]], on="signal_id", validate="one_to_one")
    m1 = REPO / "GOLD#_M1_202201030100_202608282357.csv"
    verify(m1, EXPECTED_M1, "raw_m1")
    builder = FootprintBuilder()
    read_m1(m1, builder)
    universe = builder.frame()
    universe["decision"] = pd.to_datetime(universe.decision)
    universe["exit_time"] = pd.to_datetime(universe.exit_time)
    seeds = episodes[["run_id", "first_child_signal_id", "direction"]].merge(
        universe, left_on="first_child_signal_id", right_on="signal_id", validate="one_to_one")
    assert len(seeds) == len(episodes) == 679
    # Exact source population and outcome parity; never substitute hypothetical failures.
    parity = children.merge(universe[["signal_id", "R"]], on="signal_id", suffixes=("", "_oracle"), validate="one_to_one")
    quality["max_R_parity_error"] = float((parity.R - parity.R_oracle).abs().max())
    assert quality["max_R_parity_error"] < 1e-8
    decision = decisions(seeds)
    save_csv(decision, out / "DECISIONS.csv")
    episodes = episodes.merge(decision, on=["run_id", "direction", "decision"], validate="one_to_one")
    episodes = episodes.merge(seeds[["run_id", "R"]].rename(columns={"R": "seed_R"}), on="run_id", validate="one_to_one")
    true_tail = children.groupby("run_id").R.max().ge(5)
    episodes["true_tail"] = episodes.run_id.map(true_tail).astype(int)
    save_csv(episodes, out / "OUTCOMES.csv")
    records = []
    for name, mask in (("BASELINE", np.ones(len(episodes), bool)), ("H4_FOOTPRINT", episodes.skip_h4 == 0), ("RISK_FOOTPRINT", episodes.skip_risk == 0)):
        selected = episodes.loc[mask].sort_values("run_start")
        records.append(dict(policy=name, segment="ALL", **stats(selected, children)))
        for field in ("year", "direction"):
            for value, group in selected.groupby(field):
                records.append(dict(policy=name, segment=f"{field}:{value}", **stats(group, children)))
        c = children.loc[children.run_id.isin(selected.run_id)]
        curve = c.groupby("exit_time", as_index=False).combined_R_units.sum().sort_values("exit_time")
        curve["cumulative_realized_R"] = curve.combined_R_units.cumsum()
        save_csv(curve, out / f"REALIZED_{name}.csv")
    save_csv(pd.DataFrame(records), out / "SCORECARDS.csv")
    groups = []
    for field in ("h4_state", "risk_state"):
        for (state, side), group in episodes.loc[episodes.known_prior_loss == 1].groupby([field, "side_relation"]):
            groups.append(dict(footprint=field, state=state, side=side, **stats(group, children)))
    save_csv(pd.DataFrame(groups), out / "COHORTS.csv")
    quality["known_prior_loss_episodes"] = int(episodes.known_prior_loss.sum())
    quality["no_first_stop_negative"] = int(((episodes.first_child_hard_sl == 0) & (episodes.net_R_units < 0)).sum())
    quality["positive_seed_late_damage_subset"] = int(((episodes.seed_R > 0) & (episodes.net_R_units < 0)).sum())
    quality["unavailable_references"] = int((episodes.h4_state == "UNAVAILABLE").sum())
    quality["rebuild_universe_rows"] = len(universe)
    save_json(quality, out / "QUALITY.json")
    receipt = dict(action_authority=False, independent_validation=False,
                   source_hashes={p.name: sha256_file(p) for p in (rp, cp, op, gp, m1)},
                   source_code_sha256=sha256_file(Path(__file__)),
                   contract_sha256=sha256_file(REPO / "docs/ea/v12/V12_PHASE1W_RETRY_LOCATION_CONTRACT_20260926.md"),
                   files={p.name: sha256_file(p) for p in sorted(out.iterdir())})
    save_json(receipt, out / "MANIFEST.json")
    print(pd.DataFrame(records).query("segment == 'ALL'").to_string(index=False))
    print(json.dumps(quality, indent=2))


if __name__ == "__main__":
    main()
