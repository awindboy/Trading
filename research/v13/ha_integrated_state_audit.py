"""HA-4C: compare completed HA states on the unchanged Standard-H4 Journey.

All compared decisions are already fixed by the HA-0/HA-3 and HA-4 causal
ledgers. This script never creates or changes trades. Future outcomes are
written to a separate local file and are not available to feature creation.
"""

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def number(value):
    return float(value)


def integer(value):
    return int(value)


def boolean(value):
    assert value in ("True", "False"), value
    return value == "True"


def median(values):
    return round(statistics.median(values), 4) if values else None


def rate(rows, key):
    return round(sum(bool(row[key]) for row in rows) / len(rows), 6) if rows else None


def summarize(rows):
    return {
        "decisions": len(rows),
        "journeys": len({row["journey"] for row in rows}),
        "next_flip": rate(rows, "next_flip"),
        "flip_within_3": rate(rows, "flip_within_3"),
        "final_peak_already_past_label": rate(rows, "peak_already"),
        "remaining_favorable_excursion_ranges_median": median(
            [row["remaining_favorable_ranges"] for row in rows if row["remaining_favorable_ranges"] is not None]),
        "giveback_from_future_peak_ranges_median": median(
            [row["giveback_ranges"] for row in rows if row["giveback_ranges"] is not None]),
    }


def categorical(rows, key):
    return {str(value): summarize([row for row in rows if row[key] == value])
            for value in sorted({row[key] for row in rows}, key=str)}


def rank_bins(rows, key, count=3):
    ordered = sorted(rows, key=lambda row: row[key])
    return {id(row): min(count - 1, index * count // len(ordered))
            for index, row in enumerate(ordered)}


def overlap_contrast(rows, field, bin_count=3, min_each=10, extras=()):
    """Descriptive within-H4-geometry contrast; no extrapolation or gate."""
    body = rank_bins(rows, "h4_body_ratio", bin_count)
    close = rank_bins(rows, "h4_raw_close_normalized", bin_count)
    cells = defaultdict(list)
    for row in rows:
        cells[(body[id(row)], close[id(row)], *(row[key] for key in extras))].append(row)
    matched = []
    for key, cell in sorted(cells.items()):
        yes = [row for row in cell if row[field]]
        no = [row for row in cell if not row[field]]
        if len(yes) < min_each or len(no) < min_each:
            continue
        weight = min(len(yes), len(no))
        matched.append({"cell": key, "yes": yes, "no": no, "weight": weight})
    total_weight = sum(cell["weight"] for cell in matched)
    result = {"eligible_cells": len(matched),
              "decisions_in_eligible_cells": sum(len(cell["yes"]) + len(cell["no"]) for cell in matched),
              "total_decisions": len(rows), "min_group_per_cell": min_each,
              "body_and_rawclose_rank_bins": bin_count, "other_h4_fields": list(extras)}
    for outcome in ("next_flip", "flip_within_3", "peak_already"):
        result[f"{outcome}_yes_minus_no"] = round(
            sum(cell["weight"] * (rate(cell["yes"], outcome) - rate(cell["no"], outcome))
                for cell in matched) / total_weight, 6) if total_weight else None
    return result


def ensure_sources(ha3, h1, d1):
    with (ha3 / "ha3_summary.json").open(encoding="utf-8") as handle:
        a = json.load(handle)
    with (h1 / "summary.json").open(encoding="utf-8") as handle:
        b = json.load(handle)
    with (d1 / "summary.json").open(encoding="utf-8") as handle:
        c = json.load(handle)
    m1 = a["source"]["m1_sha256"]
    h4 = a["source"]["h4_sha256"]
    assert m1 == b["source_sha256"]["m1"] == c["source_sha256"]["m1"]
    assert h4 == b["source_sha256"]["h4"] == c["source_sha256"]["h4"]
    for report in (b, c):
        assert report["active_h4_decisions"] == 4108
        assert report["closed_journeys"] == 965
        assert report["closed_child_decisions"] == 3858
        assert all(item["mismatched"] == 0 and item["missing_export"] == 0
                   for item in report["parity"].values())
    return {"m1_sha256": m1, "h4_sha256": h4,
            "h1_sha256": b["source_sha256"]["h1"],
            "d1_sha256": c["source_sha256"]["d1"]}


def build_features(std, fast, pre, post, h1, d1):
    assert len(std) == len(fast) == len(pre) == len(post) == len(h1) == len(d1) == 4108
    output = []
    for i, (s, f, p, q, h, d) in enumerate(zip(std, fast, pre, post, h1, d1)):
        assert s["signal"] == f["signal"] == p["signal"] == q["signal"] == h["signal"] == d["signal"]
        assert integer(s["journey"]) == integer(h["journey"]) == integer(d["journey"])
        assert integer(s["side"]) == integer(h["side"]) == integer(d["side"])
        assert abs(number(s["body_ratio"]) - number(h["h4_body_ratio"])) < 1e-9
        assert integer(p["side"]) == integer(q["side"])
        assert abs(number(p["ha_open"]) - number(q["ha_open"])) < 1e-8
        assert abs(number(p["ha_close"]) - number(q["ha_close"])) < 1e-8
        prior_s = std[i - 1] if i and std[i - 1]["journey"] == s["journey"] else None
        prior_f = fast[i - 1] if i and std[i - 1]["journey"] == s["journey"] else None
        prior_p = pre[i - 1] if i and std[i - 1]["journey"] == s["journey"] else None
        prior_q = post[i - 1] if i and std[i - 1]["journey"] == s["journey"] else None
        row = {
            "signal": s["signal"], "known_at": h["known_at"],
            "journey": integer(s["journey"]), "side": integer(s["side"]),
            "journey_bar": integer(h["journey_bar"]),
            "year": integer(s["signal"][:4]),
            "h4_body_ratio": number(s["body_ratio"]),
            "h4_raw_close_normalized": number(h["h4_raw_close_vs_ha_close_normalized"]),
            "h4_delta_contract": prior_s is not None and abs(number(s["delta"])) < abs(number(prior_s["delta"])),
            "h4_wick_present": number(s["opposite_wick"]) > 1e-9,
            "h4_wick_reappeared": prior_s is not None and number(prior_s["opposite_wick"]) <= 1e-9 and number(s["opposite_wick"]) > 1e-9,
            "fast_opposed": integer(f["side"]) != integer(s["side"]),
            "fast_body_ratio": number(f["body_ratio"]),
            "fast_delta_contract": prior_f is not None and abs(number(f["delta"])) < abs(number(prior_f["delta"])),
            "ema_opposed": integer(p["side"]) != integer(s["side"]),
            "pre_body_ratio": number(p["body_ratio"]),
            "post_body_ratio": number(q["body_ratio"]),
            "pre_wick_present": number(p["opposite_wick"]) > 1e-9,
            "post_wick_present": number(q["opposite_wick"]) > 1e-9,
            "pre_wick_reappeared": prior_p is not None and number(prior_p["opposite_wick"]) <= 1e-9 and number(p["opposite_wick"]) > 1e-9,
            "post_wick_reappeared": prior_q is not None and number(prior_q["opposite_wick"]) <= 1e-9 and number(q["opposite_wick"]) > 1e-9,
            "pre_delta_contract": prior_p is not None and abs(number(p["delta"])) < abs(number(prior_p["delta"])),
            "post_delta_contract": prior_q is not None and abs(number(q["delta"])) < abs(number(prior_q["delta"])),
            "d1_opposed": integer(d["context_color"]) != integer(s["side"]),
            "d1_body_ratio": number(d["context_body_ratio"]),
            "d1_delta_contract": boolean(d["context_delta_contract"]),
            "h1_opposed": integer(h["context_color"]) != integer(s["side"]),
            "h1_body_ratio": number(h["context_body_ratio"]),
            "h1_wick_present": number(h["context_opposite_wick"]) > 1e-9,
            "h1_delta_contract": boolean(h["context_delta_contract"]),
            "h1_opposed_path": h["h1_opposed_path"],
            "h1_path_state": h["h1_path_state"],
            "h1_trailing_opposed": integer(h["h1_trailing_opposed"]),
            "h1_bars_in_h4": integer(h["h1_bars_in_h4"]),
        }
        assert row["h1_opposed"] == (row["h1_trailing_opposed"] > 0)
        assert row["pre_delta_contract"] == row["post_delta_contract"]
        output.append(row)
    return output


def build_labels(std, h1_labels, features):
    label_by_signal = {row["signal"]: row for row in h1_labels}
    assert len(label_by_signal) == 4105
    output = []
    for i, (source, feature) in enumerate(zip(std, features)):
        original = label_by_signal.get(feature["signal"])
        if original is None:
            continue
        assert integer(original["journey"]) == feature["journey"]
        stop = i + 1
        while stop < len(std) and std[stop]["journey"] == source["journey"]:
            stop += 1
        assert stop < len(std), feature["signal"]
        assert integer(std[stop]["side"]) != feature["side"]
        future = std[i + 1:stop + 1]
        entry = number(source["execution_raw_open"])
        exit_price = number(std[stop]["execution_raw_open"])
        extreme = max(number(bar["raw_high"]) for bar in future) if feature["side"] == 1 else min(number(bar["raw_low"]) for bar in future)
        favorable = max(0.0, feature["side"] * (extreme - entry))
        giveback = feature["side"] * (extreme - exit_price)
        scale = statistics.median(number(bar["raw_high"]) - number(bar["raw_low"])
                                  for bar in std[i - 19:i + 1]) if i >= 19 else None
        assert scale is None or scale > 0
        row = {"signal": feature["signal"], "journey": feature["journey"],
               "next_flip": boolean(original["next_flip"]),
               "flip_within_3": boolean(original["flip_within_3"]),
               "peak_already": boolean(original["peak_already"]),
               "journey_closed_bars": integer(original["journey_closed_bars"]),
               "remaining_favorable_ranges": favorable / scale if scale else None,
               "giveback_ranges": giveback / scale if scale else None}
        assert row["next_flip"] == (stop == i + 1)
        output.append(row)
    return output


def analyze(features, labels):
    feature_by_signal = {row["signal"]: row for row in features}
    rows = [{**feature_by_signal[label["signal"]], **label} for label in labels]
    assert len(rows) == 4105
    output = {"all": summarize(rows),
              "h4_delta_contract_x_h1_path": {
                  str(state): categorical([r for r in rows if r["h4_delta_contract"] == state], "h1_path_state")
                  for state in (False, True)},
              "h4_wick_reappearance_x_h1_path": {
                  str(state): categorical([r for r in rows if r["h4_wick_reappeared"] == state], "h1_path_state")
                  for state in (False, True)},
              "h4_delta_contract_x_fast_opposed": {
                  str(state): categorical([r for r in rows if r["h4_delta_contract"] == state], "fast_opposed")
                  for state in (False, True)},
              "h1_path": categorical(rows, "h1_path_state"),
              "h1_trailing_opposed": categorical(rows, "h1_trailing_opposed")}
    for name in ("fast_opposed", "h1_opposed", "d1_opposed", "h4_delta_contract",
                 "h4_wick_reappeared", "fast_delta_contract", "d1_delta_contract", "h1_delta_contract",
                 "ema_opposed", "pre_wick_present", "post_wick_present",
                 "pre_wick_reappeared", "post_wick_reappeared", "pre_delta_contract", "post_delta_contract"):
        output[name] = categorical(rows, name)
    output["ema_pre_post_wick_presence"] = {
        f"pre_{pre}_post_{post}": summarize([r for r in rows if r["pre_wick_present"] == pre and r["post_wick_present"] == post])
        for pre in (False, True) for post in (False, True)}
    output["within_h4_body_x_rawclose_tertiles"] = {
        name: overlap_contrast(rows, name) for name in ("fast_opposed", "h1_opposed", "d1_opposed")}
    output["h1_overlap_sensitivity"] = {
        "quintiles_min20": overlap_contrast(rows, "h1_opposed", 5, 20),
        "tertiles_plus_h4_delta_and_wick": overlap_contrast(
            rows, "h1_opposed", 3, 10, ("h4_delta_contract", "h4_wick_present"))}
    repaired_or_none = [{**r, "h1_repaired": r["h1_path_state"] == "repaired"}
                        for r in rows if r["h1_path_state"] in ("repaired", "no_opposition")]
    output["repaired_vs_no_opposition_within_h4_geometry"] = overlap_contrast(
        repaired_or_none, "h1_repaired", 3, 10)
    output["ema_morphology_within_h4_geometry"] = {
        name: overlap_contrast(rows, name, 3, 10) for name in
        ("ema_opposed", "pre_wick_present", "post_wick_present", "pre_wick_reappeared",
         "post_wick_reappeared", "pre_delta_contract")}
    output["h4_wick_reappearance_x_ema_wick_reappearance"] = {
        name: {str(state): categorical([r for r in rows if r["h4_wick_reappeared"] == state], name)
               for state in (False, True)}
        for name in ("pre_wick_reappeared", "post_wick_reappeared")}
    continuation = [r for r in rows if r["journey_bar"] > 1]
    output["continuation_only"] = {
        "all": summarize(continuation),
        **{name: categorical(continuation, name) for name in
           ("h1_path_state", "fast_opposed", "h1_opposed", "d1_opposed",
            "h4_wick_reappeared", "pre_wick_reappeared", "post_wick_reappeared")},
        "post_wick_reappearance_within_h4_geometry": overlap_contrast(
            continuation, "post_wick_reappeared", 3, 10),
        "h1_opposed_within_h4_geometry": overlap_contrast(
            continuation, "h1_opposed", 3, 10)}
    output["year_side_and_birth"] = {}
    for year in (2024, 2025, 2026):
        for side in (1, -1):
            for birth in (True, False):
                subset = [r for r in rows if r["year"] == year and r["side"] == side and (r["journey_bar"] == 1) == birth]
                output["year_side_and_birth"][f"{year}_{'LONG' if side == 1 else 'SHORT'}_{'birth' if birth else 'continuation'}"] = {
                    "all": summarize(subset),
                    **{name: categorical(subset, name) for name in
                       ("fast_opposed", "h1_opposed", "d1_opposed", "pre_wick_reappeared", "post_wick_reappeared")}}
    tails = [r for r in rows if r["journey_closed_bars"] >= 10]
    tail_ids = {r["journey"] for r in tails}
    assert len(tail_ids) == 88
    output["long_journey_warning_coverage"] = {"journeys": len(tail_ids), "decisions": len(tails)}
    for name in ("fast_opposed", "h1_opposed", "d1_opposed", "h4_delta_contract", "h4_wick_reappeared",
                 "ema_opposed", "pre_wick_reappeared", "post_wick_reappeared"):
        warnings = [r for r in tails if r[name]]
        output["long_journey_warning_coverage"][name] = {
            "journeys_with_any": len({r["journey"] for r in warnings}),
            "warning_decisions": len(warnings),
            "warnings_without_next_flip": sum(not r["next_flip"] for r in warnings),
            "median_remaining_favorable_ranges": median([r["remaining_favorable_ranges"] for r in warnings if r["remaining_favorable_ranges"] is not None])}
    return output


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ha3", type=Path, required=True)
    parser.add_argument("--h1", type=Path, required=True)
    parser.add_argument("--d1", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sources = ensure_sources(args.ha3, args.h1, args.d1)
    representation_rows = read_csv(args.ha3 / "ha3_decision_bars.csv")
    representations = defaultdict(list)
    for row in representation_rows:
        representations[row["representation"]].append(row)
    std, fast = representations["STD"], representations["FAST_R25"]
    pre, post = representations["PRE_EMA2"], representations["POST_EMA2"]
    h1 = read_csv(args.h1 / "decision_features.csv")
    d1 = read_csv(args.d1 / "decision_features.csv")
    assert len(h1) == len(d1) == 4108
    features = build_features(std, fast, pre, post, h1, d1)
    labels = build_labels(std, read_csv(args.h1 / "future_labels.csv"), features)
    report = {"status": "consumed-development-observation-only", "sources": sources,
              "summary": analyze(features, labels)}
    args.output.mkdir(parents=True, exist_ok=True)
    write_csv(args.output / "decision_features.csv", features)
    write_csv(args.output / "future_labels.csv", labels)
    (args.output / "summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"sources": sources, "all": report["summary"]["all"],
                      "overlap": report["summary"]["within_h4_body_x_rawclose_tertiles"]}, indent=2))


if __name__ == "__main__":
    main()
