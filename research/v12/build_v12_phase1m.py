#!/usr/bin/env python3
"""Build frozen V12 Phase-1M H1 transition-Child diagnostics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from build_v12_phase0 import parse_cutoff
from build_v12_phase1d import write_csv, write_json
from build_v12_phase1l import build_ledgers, policy_frames, scorecards
from v12_phase0_core import sha256_file


CONTRACT_VERSION = "v12-phase1m-h1-transition-child-v1"
PREFIX = "V12_PHASE1M_"


def safe_output(path: Path, replace: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not replace:
            raise FileExistsError(path)
        for child in path.iterdir():
            if not child.is_file() or not child.name.startswith(PREFIX):
                raise ValueError(f"refusing to replace unexpected output: {child}")
            child.unlink()
    path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=repo / "research/v12/v12_phase1m_contract.json")
    parser.add_argument("--m1", type=Path, default=repo / "data/GOLD#/GOLD#_M1_202201030100_202609222358.csv")
    parser.add_argument("--output", type=Path, default=repo / "output/v12_phase1m_h1_transition_child_20260925_a")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract["contract_version"] != CONTRACT_VERSION:
        raise ValueError("contract mismatch")
    if sha256_file(args.m1) != contract["source_hashes"]["raw_m1_full_sha256"]:
        raise ValueError("raw M1 full hash mismatch")

    safe_output(args.output, args.replace)
    h4, h1, audit = build_ledgers(args.m1, parse_cutoff(contract["mechanism_cutoff"]))
    if audit.prefix_sha256 != contract["source_hashes"]["raw_m1_prefix_sha256"]:
        raise ValueError("raw M1 prefix mismatch")
    base = policy_frames(h4, h1)
    k1 = base["H1_CORE"].loc[base["H1_CORE"]["k"] == 1].copy()
    frames = {
        "H4_CORE": base["H4_CORE"],
        "H1_K1": k1,
        "H1_K1_H4_FAST_ALIGNED": k1.loc[k1["h4_fast_align"] == 1].copy(),
        "H1_K1_H4_FAST_STD_ALIGNED": k1.loc[(k1["h4_fast_align"] == 1) & (k1["h4_std_align"] == 1)].copy(),
    }
    scores = scorecards(frames)
    pooled = scores.loc[scores["scope"] == "POOLED"].set_index("policy")
    h4s = pooled.loc["H4_CORE"]
    candidates = []
    for policy in frames:
        if policy == "H4_CORE":
            continue
        summary = pooled.loc[policy]
        years = scores.loc[(scores["policy"] == policy) & scores["scope"].isin([str(y) for y in range(2022, 2027)])]
        gates = {
            "POSITIVE_4_OF_5_YEARS": int((years["net_R"] > 0).sum()) >= 4,
            "TOTAL_STOPS": summary["stopped_units"] <= h4s["stopped_units"],
            "EQUAL_TOTAL_STOP_BUDGET": summary["equal_stop_budget_net_R_per_h4_unit"] >= 0.8 * h4s["net_R_per_unit"],
            "PROFIT_FACTOR": summary["profit_factor_R"] >= 0.9 * h4s["profit_factor_R"],
            "STOP_STREAK": summary["max_stop_streak"] <= 1.5 * h4s["max_stop_streak"],
            "RIGHT_TAIL": summary["tail_ge_5_R_per_100"] >= 0.7 * h4s["tail_ge_5_R_per_100"],
        }
        candidates.append({"policy": policy, **gates, "OVERALL": all(gates.values())})
    gates = pd.DataFrame(candidates)

    write_csv(args.output / f"{PREFIX}SCORECARD.csv", scores.to_dict("records"), list(scores.columns))
    write_csv(args.output / f"{PREFIX}GATES.csv", gates.to_dict("records"), list(gates.columns))
    for policy, frame in frames.items():
        if policy != "H4_CORE":
            write_csv(args.output / f"{PREFIX}{policy}_LEDGER.csv", frame.to_dict("records"), list(frame.columns))
    diagnostics = {
        "contract_version": CONTRACT_VERSION,
        "raw_m1_prefix_sha256": audit.prefix_sha256,
        "post_cutoff_price_rows_parsed": audit.post_cutoff_price_rows_parsed,
        "rows": {key: len(value) for key, value in frames.items()},
        "overall_passes": int(gates["OVERALL"].sum()),
    }
    write_json(args.output / f"{PREFIX}DIAGNOSTICS.json", diagnostics)
    members = []
    for path in sorted(args.output.glob(f"{PREFIX}*")):
        if path.name != f"{PREFIX}MANIFEST.json":
            members.append({"name": path.name, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    manifest = {
        "contract_version": CONTRACT_VERSION,
        "contract_sha256": sha256_file(args.contract),
        "input_full_sha256": sha256_file(args.m1),
        "files": members,
    }
    write_json(args.output / f"{PREFIX}MANIFEST.json", manifest)
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
