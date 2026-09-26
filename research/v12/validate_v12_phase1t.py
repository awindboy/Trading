"""Validate the retained Phase-1T diagnostic pack without promoting it."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


PREFIX = "V12_PHASE1T_"
EXPECTED_VARIANTS = {
    "V10_CONTROL",
    "V10_WEEK_CLOCK",
    "V10_WEEK_PRICE",
    "V10_WEEK_PRICE_EVENT",
    "V10_WEEK_PRICE_R4_ONLY",
    "V10_WEEK_PRICE_STOP_ONLY",
    "V10_WEEK_PRICE_R5_BOTH",
    "V10_WEEK_PRICE_EVENT_STOP_ONLY",
}
XGB_STOP_GROUPS = {("k1", "LONG"), ("k1", "SHORT"), ("k3p", "SHORT")}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pack",
        type=Path,
        default=repo / "output/v12_phase1t_v10_direct_feature_retrain_20260926_b",
    )
    args = parser.parse_args()

    manifest_path = args.pack / f"{PREFIX}RELEASE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, expected in manifest.items():
        path = args.pack / name
        require(path.is_file(), f"missing manifest member: {name}")
        require(sha256_file(path) == expected, f"manifest hash mismatch: {name}")

    quality = json.loads((args.pack / f"{PREFIX}DATA_QUALITY.json").read_text(encoding="utf-8"))
    summary = json.loads((args.pack / f"{PREFIX}SUMMARY.json").read_text(encoding="utf-8"))
    ledger = pd.read_csv(args.pack / f"{PREFIX}EVENT_LEDGER.csv", parse_dates=["decision", "entry_time", "exit_time"])
    parity = pd.read_csv(args.pack / f"{PREFIX}CONTROL_PARITY.csv")
    cards = pd.read_csv(args.pack / f"{PREFIX}POLICY_SCORECARDS.csv").set_index("variant")
    gates = pd.read_csv(args.pack / f"{PREFIX}GATES.csv").set_index("gate")

    require(quality["universe_rows"] == 6770, "unexpected V10 universe size")
    require(quality["weekly_feature_rows"] == 6770, "weekly feature coverage mismatch")
    require(quality["strict_weekly_snapshots"] == 6770, "non-causal weekly snapshot found")
    require(quality["raw_m1_prefix_sha256"] == quality["weekly_prefix_sha256"], "prefix scans disagree")
    require(set(ledger["variant"].unique()) == EXPECTED_VARIANTS, "variant inventory mismatch")
    per_variant = ledger.groupby("variant")["signal_id"].nunique()
    require(per_variant.nunique() == 1 and int(per_variant.iloc[0]) == 5450,
            "scored event-ledger coverage mismatch")
    require(not ledger.duplicated(["variant", "signal_id"]).any(), "duplicate variant/signal row")

    require(summary["status"] == "CONTROL_PARITY_FAILED", "parity limitation must remain explicit")
    require(summary["parity"]["r4_action_match_rate"] == 1.0, "R4 control parity failed")
    require(summary["parity"]["r5_ev_sign_match_rate"] < 1.0, "expected XGBoost platform limitation disappeared; re-audit")
    bad_ev = parity.loc[~parity["r5_ev_sign_match"].astype(bool), ["stage", "direction"]]
    require(set(map(tuple, bad_ev.drop_duplicates().to_numpy())) <= XGB_STOP_GROUPS,
            "EV-sign mismatches escaped the three XGBoost STOP heads")

    control = ledger.loc[ledger["variant"].eq("V10_CONTROL")].set_index("signal_id")
    stop_only = ledger.loc[ledger["variant"].eq("V10_WEEK_PRICE_STOP_ONLY")].set_index("signal_id")
    require(control["r4_weight"].equals(stop_only["r4_weight"]), "STOP-only ablation altered R4")
    require(control["mu_nonstop"].equals(stop_only["mu_nonstop"]), "STOP-only ablation altered conditional-R")
    require((cards.loc["V10_WEEK_PRICE", "net_R"] < cards.loc["V10_CONTROL", "net_R"]),
            "frozen primary failure changed")
    require((cards.loc["V10_WEEK_PRICE", "right_tail_ge5_R"]
             < cards.loc["V10_CONTROL", "right_tail_ge5_R"]), "primary tail failure changed")
    require(not bool(gates.loc["NET_R_RETENTION", "passed"]), "primary net-R gate unexpectedly passed")
    require(not bool(gates.loc["TAIL_RETENTION", "passed"]), "primary tail gate unexpectedly passed")

    receipt = {
        "status": "PASS_ARTIFACT_INTEGRITY_WITH_DECLARED_CONTROL_PARITY_LIMITATION",
        "pack": str(args.pack.resolve()),
        "manifest_members_verified": len(manifest),
        "rows": len(ledger),
        "variants": sorted(EXPECTED_VARIANTS),
        "r4_action_match_rate": summary["parity"]["r4_action_match_rate"],
        "r5_ev_sign_match_rate": summary["parity"]["r5_ev_sign_match_rate"],
        "r7g_weight_match_rate": summary["parity"]["r7g_weight_match_rate"],
        "primary_pass": False,
        "action_authority": False,
    }
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
