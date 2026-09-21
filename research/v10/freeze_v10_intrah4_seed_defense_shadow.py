"""Freeze the deterministic V10 +60m provisional-HA seed-defense shadow.

Development-only hypothesis:

* population: existing R7G-selected 1-unit newest Child;
* checkpoint: exact forming-H4 +60 minute boundary;
* state: Child must still be alive;
* warning: direction-aligned provisional FAST-HA margin, normalized by the
  previous completed H4 Wilder ATR180, is at or below the prior causal q10;
* shadow action: hypothetically exit that newest Child only.

The rule has no EA or trade authority.  Historical results are consumed and
the q10 choice is post-hoc development evidence.  The output freezes the final
all-history q10 only for genuinely future-only shadow observation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


TEST_YEARS = (2024, 2025, 2026)


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix-ledger", required=True, type=Path)
    parser.add_argument("--population", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def max_true_streak(values: pd.Series) -> int:
    best = current = 0
    for value in values.astype(bool):
        if value:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def metrics(frame: pd.DataFrame, period: object) -> dict[str, object]:
    data = frame.sort_values("decision").copy()
    action = data["seed_defense_action"].astype(bool)
    data["policy_R"] = np.where(action, data["early_exit_R"], data["R"])
    data["policy_stop"] = data["stop_hit"].astype(bool) & ~action
    weight = data["r7g_weight"].astype(float)
    good = action & (data["delta_weighted_R"] > 0.0)
    bad = action & (data["delta_weighted_R"] <= 0.0)
    baseline = float((data["R"] * weight).sum())
    policy = float((data["policy_R"] * weight).sum())
    baseline_weighted = data["R"] * weight
    policy_weighted = data["policy_R"] * weight
    long_tail = (data["L"] >= 6) & (baseline_weighted > 0.0)
    long_tail_baseline = float(baseline_weighted[long_tail].sum())
    long_tail_policy = float(policy_weighted[long_tail].sum())
    return {
        "period": period,
        "children": int(len(data)),
        "q10_threshold": float(data["prior_q10"].iloc[0]) if data["prior_q10"].nunique() == 1 else np.nan,
        "actions": int(action.sum()),
        "actual_nha": int((action & (data["nha"] == 1)).sum()),
        "actual_pha": int((action & (data["nha"] == 0)).sum()),
        "good_actions": int(good.sum()),
        "bad_actions": int(bad.sum()),
        "gain_from_good_actions_R": float(data.loc[good, "delta_weighted_R"].sum()),
        "regret_from_bad_actions_R": float(data.loc[bad, "delta_weighted_R"].sum()),
        "baseline_hard_stops": int(data["stop_hit"].sum()),
        "policy_hard_stops": int(data["policy_stop"].sum()),
        "hard_stops_prevented": int((action & data["stop_hit"].astype(bool)).sum()),
        "baseline_max_stop_streak": max_true_streak(data["stop_hit"]),
        "policy_max_stop_streak": max_true_streak(data["policy_stop"]),
        "baseline_weighted_R": baseline,
        "policy_weighted_R": policy,
        "delta_weighted_R": policy - baseline,
        "L6plus_positive_R_retention": (
            long_tail_policy / long_tail_baseline
            if long_tail_baseline > 0.0
            else np.nan
        ),
    }


def bootstrap(frame: pd.DataFrame, draws: int = 20000) -> pd.DataFrame:
    data = frame.copy()
    data["policy_delta"] = np.where(
        data["seed_defense_action"], data["delta_weighted_R"], 0.0
    )
    blocks = data.groupby("rid", sort=False)["policy_delta"].sum().to_numpy(dtype=float)
    rng = np.random.default_rng(20260921)
    values = np.empty(draws, dtype=float)
    for i in range(draws):
        values[i] = rng.choice(blocks, size=len(blocks), replace=True).sum()
    return pd.DataFrame(
        [
            {
                "blocks": int(len(blocks)),
                "draws": draws,
                "observed_delta_R": float(blocks.sum()),
                "bootstrap_mean_R": float(values.mean()),
                "q025_R": float(np.quantile(values, 0.025)),
                "q50_R": float(np.quantile(values, 0.50)),
                "q975_R": float(np.quantile(values, 0.975)),
                "p_delta_gt_0": float(np.mean(values > 0.0)),
            }
        ]
    )


def main() -> None:
    args = cli()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    prefix = pd.read_csv(
        args.prefix_ledger,
        parse_dates=["decision", "label_available_at"],
    )
    prefix = prefix[prefix["checkpoint_min"] == 60].copy()
    population = pd.read_csv(
        args.population,
        parse_dates=["decision", "exit_time"],
    )

    scored_parts: list[pd.DataFrame] = []
    metric_rows: list[dict[str, object]] = []
    for year in TEST_YEARS:
        boundary = pd.Timestamp(f"{year}-01-01")
        prior = prefix[
            (prefix["decision"] < boundary)
            & (prefix["label_available_at"] < boundary)
        ]
        q10 = float(prior["ha_margin_atr"].quantile(0.10))
        test = population[population["year"] == year].copy()
        test["prior_q10"] = q10
        test["seed_defense_action"] = (
            (test["r7g_weight"] == 1) & (test["ha_margin_atr"] <= q10)
        )
        scored_parts.append(test)
        metric_rows.append(metrics(test, year))

    scored = pd.concat(scored_parts, ignore_index=True).sort_values("decision")
    pooled = metrics(scored.assign(prior_q10=np.nan), "POOLED")
    pooled["q10_threshold"] = np.nan
    metric_rows.append(pooled)
    summary = pd.DataFrame(metric_rows)
    boot = bootstrap(scored)

    final_q10 = float(prefix["ha_margin_atr"].quantile(0.10))
    final_cutoff = prefix["decision"].max()
    shadow_manifest = {
        "status": "FUTURE_ONLY_SHADOW_INSTRUMENTATION / NO TRADE AUTHORITY",
        "hypothesis_name": "V10_INTRAH4_SEED1_Q10_DEFENSE",
        "training_cutoff_decision": final_cutoff.isoformat(sep=" "),
        "source_prefix_ledger": str(args.prefix_ledger.resolve()),
        "source_prefix_ledger_sha256": sha256_file(args.prefix_ledger),
        "source_population": str(args.population.resolve()),
        "source_population_sha256": sha256_file(args.population),
        "checkpoint_minutes": 60,
        "population": "existing R7G-selected newest Child with r7g_weight == 1 and still alive",
        "coordinate": "direction * (provisional_FAST_HA_close - fixed_FAST_HA_open) / prior_completed_H4_ATR180",
        "reference_population": "all causal resolved +60m opportunity prefixes through cutoff",
        "reference_quantile": 0.10,
        "frozen_q10": final_q10,
        "shadow_action": "hypothetical exit newest 1-unit Child only",
        "catch_up": "none",
        "three_unit_child_action": "none",
        "threshold_scan": False,
        "promotion_authority": "none",
    }

    scored_path = args.out_dir / "V10_INTRAH4_SEED_DEFENSE_OUTER_SCORED.csv"
    summary_path = args.out_dir / "V10_INTRAH4_SEED_DEFENSE_OUTER_SUMMARY.csv"
    bootstrap_path = args.out_dir / "V10_INTRAH4_SEED_DEFENSE_BOOTSTRAP.csv"
    manifest_path = args.out_dir / "V10_INTRAH4_SEED_DEFENSE_FUTURE_SHADOW_MANIFEST.json"
    scored.to_csv(scored_path, index=False, date_format="%Y-%m-%d %H:%M:%S")
    summary.to_csv(summary_path, index=False)
    boot.to_csv(bootstrap_path, index=False)
    manifest_path.write_text(json.dumps(shadow_manifest, indent=2), encoding="utf-8")

    print(json.dumps(shadow_manifest, indent=2))
    print("\nOUTER_SUMMARY")
    print(summary.to_string(index=False))
    print("\nBOOTSTRAP")
    print(boot.to_string(index=False))


if __name__ == "__main__":
    main()
