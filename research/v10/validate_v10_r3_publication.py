"""Validate the compact V10 R3 publication and optional local model bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import joblib
import pandas as pd


STAMP = "20260917"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--local-output", type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    result_dir = repo / "docs" / "ea" / "v10" / "results" / "r3_k1stop_20260917"
    research_dir = repo / "research" / "v10"
    receipt_path = result_dir / f"V10_R3_REPRODUCIBILITY_RECEIPT_{STAMP}.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    problems: list[str] = []

    for name, expected in receipt["published_sha256"].items():
        path = result_dir / name
        if not path.exists() or sha256(path) != expected:
            problems.append(f"published hash mismatch: {name}")
    for name, expected in receipt["script_sha256"].items():
        path = research_dir / name
        if not path.exists() or sha256(path) != expected:
            problems.append(f"script hash mismatch: {name}")

    for name in (
        f"V10_R3_CAUSAL_UNIVERSE_MANIFEST_{STAMP}.json",
        f"V10_R3_K1STOP_TUNED_VALIDATION_{STAMP}.json",
        f"V10_R3_K1STOP_STABLE_FRONTIER_VALIDATION_{STAMP}.json",
        f"V10_R3_K1STOP_FUTURE_SHADOW_MANIFEST_{STAMP}.json",
    ):
        value = json.loads((result_dir / name).read_text(encoding="utf-8"))
        if not value.get("ok"):
            problems.append(f"validation receipt is not ok: {name}")

    frontier = pd.read_csv(result_dir / f"V10_R3_K1STOP_POLICY_FRONTIER_{STAMP}.csv")
    expected_policies = {
        "R2_DEFAULT", "META_K1STOP_K1_Q0975", "ROBUST_C05",
        "SHALLOW_HISTGB", "STABLE_INTERSECTION", "STABLE_UNION",
    }
    if set(frontier["policy"]) != expected_policies:
        problems.append("policy frontier membership mismatch")
    primary = frontier[frontier["policy"].eq("ROBUST_C05")]
    if len(primary) != 1 or float(primary.iloc[0]["delta_R_vs_r2"]) <= 0.0:
        problems.append("primary shadow candidate does not improve pooled R")

    metrics = pd.read_csv(
        result_dir / f"V10_R3_K1STOP_STABLE_FRONTIER_METRICS_{STAMP}.csv"
    )
    conservative = metrics[metrics["outcome_convention"].eq("conservative_stop")]
    for year in ("2024", "2025", "2026"):
        rows = conservative[conservative["period"].astype(str).eq(year)].set_index("policy")
        if float(rows.loc["ROBUST_C05", "R"]) <= float(rows.loc["R2_DEFAULT", "R"]):
            problems.append(f"ROBUST_C05 does not improve R in {year}")
    bootstrap = pd.read_csv(
        result_dir / f"V10_R3_K1STOP_STABLE_FRONTIER_BOOTSTRAP_{STAMP}.csv"
    )
    pooled = bootstrap[
        bootstrap["policy"].eq("ROBUST_C05")
        & bootstrap["period"].eq("POOLED_STRATIFIED_2024_2026")
    ]
    if len(pooled) != 1 or float(pooled.iloc[0]["q025_delta_R"]) <= 0.0:
        problems.append("ROBUST_C05 pooled bootstrap lower bound is not positive")

    local_bundle_checked = False
    if args.local_output is not None:
        local = args.local_output.resolve()
        bundle_path = local / "k1stop_future_shadow" / "V10_R3_K1STOP_FUTURE_SHADOW_BUNDLE.joblib"
        if not bundle_path.exists():
            problems.append("local future shadow bundle is missing")
        else:
            sys.path.insert(0, str(research_dir))
            bundle = joblib.load(bundle_path)
            local_bundle_checked = True
            if bundle.get("primary_action_member") != "robust_c05":
                problems.append("local bundle primary member mismatch")
            if len(bundle.get("features", [])) != 21:
                problems.append("local bundle feature count mismatch")
            if set(bundle.get("members", {})) != {"robust_c05", "shallow_histgb"}:
                problems.append("local bundle member set mismatch")

    result = {
        "ok": not problems,
        "problems": problems,
        "published_files_checked": len(receipt["published_sha256"]),
        "scripts_checked": len(receipt["script_sha256"]),
        "local_bundle_checked": local_bundle_checked,
        "authority": receipt["authority"],
        "primary_shadow_candidate": receipt["primary_shadow_candidate"],
    }
    print(json.dumps(result, indent=2))
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
