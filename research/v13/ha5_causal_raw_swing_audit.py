"""V13 HA-5: causal raw H4 swing observation rebuilt from streamed GOLD# M1.

The H4 export is used only for parity. No source bar is classified against a
pivot confirmed by that same bar. No feature changes Baseline-0 trading.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ha_integrated_state_audit import (
    boolean, categorical, integer, median, number, overlap_contrast, read_csv,
    summarize, write_csv,
)


START = datetime(2024, 1, 1)
LAST_DECISION = datetime(2026, 8, 28, 20)
EPS = 1e-9


def stamp(row):
    return datetime.strptime(row["<DATE>"] + " " + row["<TIME>"], "%Y.%m.%d %H:%M:%S")


def h4_bucket(t):
    return t.replace(hour=4 * (t.hour // 4), minute=0, second=0)


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


@dataclass
class Bar:
    time: datetime
    first_print: datetime
    open: float
    high: float
    low: float
    close: float

    def add(self, high, low, close):
        self.high = max(self.high, high)
        self.low = min(self.low, low)
        self.close = close


@dataclass(frozen=True)
class Pivot:
    price: float
    origin: datetime
    confirmed_at: datetime
    confirmation_index: int


def read_h4_reference(path):
    # Reference-only future export: never supplies a decision-time feature.
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return {stamp(row): tuple(float(row[key]) for key in
                ("<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>"))
                for row in csv.DictReader(stream, delimiter="\t")}


def interaction(bar, level, orientation, prior_close, previous_used_origin):
    if level is None:
        return "no_level", False
    extreme = bar.high if orientation == 1 else bar.low
    exceeded = orientation * (extreme - level.price) > EPS
    close_beyond = orientation * (bar.close - level.price) > EPS
    same_level = level.origin == previous_used_origin
    previous_beyond = (same_level and prior_close is not None and
                       orientation * (prior_close - level.price) > EPS)
    if previous_beyond and not close_beyond:
        return "return_inside", exceeded
    if close_beyond and previous_beyond:
        return "held_close_beyond", exceeded
    if close_beyond:
        return "fresh_close_beyond", exceeded
    if exceeded:
        return "probe_rejected", exceeded
    return "no_break", exceeded


def construct_features(m1_path, h4_path, integrated_features_path):
    reference = read_h4_reference(h4_path)
    source = {row["signal"]: row for row in read_csv(integrated_features_path)}
    assert len(source) == 4108
    five = deque(maxlen=5)
    recent_ranges = deque(maxlen=20)
    last_high = last_low = None
    prior_close = None
    previous_high_origin = previous_low_origin = None
    current = None
    completed_count = checked = mismatched = 0
    output = []
    m1_rows = 0

    def complete(bar, known_at):
        nonlocal completed_count, checked, mismatched, last_high, last_low
        nonlocal prior_close, previous_high_origin, previous_low_origin
        completed_count += 1
        ref = reference.get(bar.time)
        assert ref is not None, f"H4 export missing {bar.time}"
        checked += 1
        if any(abs(value - expected) > 0.011 for value, expected in
               zip((bar.open, bar.high, bar.low, bar.close), ref)):
            mismatched += 1
        recent_ranges.append(bar.high - bar.low)
        if START <= bar.time and known_at <= LAST_DECISION:
            key = bar.time.strftime("%Y-%m-%d %H:%M:%S")
            existing = source[key]
            assert existing["known_at"] == known_at.strftime("%Y-%m-%d %H:%M:%S")
            assert number(existing["h4_body_ratio"]) >= 0
            side = integer(existing["side"])
            progress_level = last_high if side == 1 else last_low
            adverse_level = last_low if side == 1 else last_high
            progress_prior_origin = previous_high_origin if side == 1 else previous_low_origin
            adverse_prior_origin = previous_low_origin if side == 1 else previous_high_origin
            progress_state, progress_extreme = interaction(
                bar, progress_level, side, prior_close, progress_prior_origin)
            adverse_state, adverse_extreme = interaction(
                bar, adverse_level, -side, prior_close, adverse_prior_origin)
            scale = statistics.median(recent_ranges) if len(recent_ranges) == 20 else None
            row = {
                "signal": key,
                "known_at": existing["known_at"],
                "journey": integer(existing["journey"]),
                "side": side,
                "raw_open": bar.open, "raw_high": bar.high,
                "raw_low": bar.low, "raw_close": bar.close,
                "progress_state": progress_state,
                "adverse_state": adverse_state,
                "progress_level": progress_level.price if progress_level else None,
                "adverse_level": adverse_level.price if adverse_level else None,
                "progress_level_origin": progress_level.origin.isoformat() if progress_level else None,
                "adverse_level_origin": adverse_level.origin.isoformat() if adverse_level else None,
                "progress_confirmed_at": progress_level.confirmed_at.isoformat() if progress_level else None,
                "adverse_confirmed_at": adverse_level.confirmed_at.isoformat() if adverse_level else None,
                "progress_level_age_h4": completed_count - progress_level.confirmation_index if progress_level else None,
                "adverse_level_age_h4": completed_count - adverse_level.confirmation_index if adverse_level else None,
                "progress_close_distance_ranges": side * (bar.close - progress_level.price) / scale if progress_level and scale else None,
                "adverse_close_distance_ranges": -side * (bar.close - adverse_level.price) / scale if adverse_level and scale else None,
                "both_boundaries_exceeded": progress_extreme and adverse_extreme,
                "inverted_pivot_prices": last_high is not None and last_low is not None and last_high.price <= last_low.price,
                "progress_rejection_or_return": progress_state in ("probe_rejected", "return_inside"),
                "progress_fresh_close_beyond": progress_state == "fresh_close_beyond",
                "progress_held_close_beyond": progress_state == "held_close_beyond",
                "progress_return_inside": progress_state == "return_inside",
                "progress_probe_rejected": progress_state == "probe_rejected",
                "adverse_close_beyond": adverse_state in ("fresh_close_beyond", "held_close_beyond"),
            }
            assert progress_level is None or progress_level.confirmed_at <= bar.first_print
            assert adverse_level is None or adverse_level.confirmed_at <= bar.first_print
            output.append(row)
        # The active levels *used* for this completed bar precede any pivot
        # confirmed by this bar. New pivots are for future H4 bars only.
        previous_high_origin = last_high.origin if last_high else None
        previous_low_origin = last_low.origin if last_low else None
        prior_close = bar.close
        five.append(bar)
        if len(five) == 5:
            candidate = five[2]
            others = [five[index] for index in (0, 1, 3, 4)]
            if all(candidate.high > other.high for other in others):
                last_high = Pivot(candidate.high, candidate.time, known_at, completed_count)
            if all(candidate.low < other.low for other in others):
                last_low = Pivot(candidate.low, candidate.time, known_at, completed_count)

    with m1_path.open(newline="", encoding="utf-8-sig") as stream:
        for raw in csv.DictReader(stream, delimiter="\t"):
            t = stamp(raw)
            if t > LAST_DECISION:
                break
            m1_rows += 1
            o, hi, lo, cl = (float(raw[key]) for key in ("<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>"))
            bucket = h4_bucket(t)
            if current is None:
                current = Bar(bucket, t, o, hi, lo, cl)
            elif current.time != bucket:
                complete(current, t)
                current = Bar(bucket, t, o, hi, lo, cl)
            else:
                current.add(hi, lo, cl)
    assert mismatched == 0 and checked == 7198, (checked, mismatched)
    assert len(output) == 4108
    return output, {"m1_rows": m1_rows, "h4_checked": checked, "h4_mismatched": mismatched}


def make_rows(raw_features, existing_features_path, future_labels_path):
    existing = {row["signal"]: row for row in read_csv(existing_features_path)}
    labels = {row["signal"]: row for row in read_csv(future_labels_path)}
    assert len(existing) == 4108 and len(labels) == 4105
    comparison = []
    for raw in raw_features:
        old = existing[raw["signal"]]
        assert raw["journey"] == integer(old["journey"])
        assert raw["side"] == integer(old["side"])
        label = labels.get(raw["signal"])
        if label is None:
            continue
        assert raw["journey"] == integer(label["journey"])
        comparison.append({**raw,
            "h4_body_ratio": number(old["h4_body_ratio"]),
            "h4_raw_close_normalized": number(old["h4_raw_close_normalized"]),
            "h4_delta_contract": boolean(old["h4_delta_contract"]),
            "h4_wick_present": boolean(old["h4_wick_present"]),
            "h1_path_state": old["h1_path_state"],
            "h1_opposed": boolean(old["h1_opposed"]),
            "journey_bar": integer(old["journey_bar"]),
            "year": integer(old["year"]),
            "next_flip": boolean(label["next_flip"]),
            "flip_within_3": boolean(label["flip_within_3"]),
            "peak_already": boolean(label["peak_already"]),
            "journey_closed_bars": integer(label["journey_closed_bars"]),
            "remaining_favorable_ranges": number(label["remaining_favorable_ranges"]) if label["remaining_favorable_ranges"] else None,
            "giveback_ranges": number(label["giveback_ranges"]) if label["giveback_ranges"] else None,
        })
    assert len(comparison) == 4105
    return comparison


def journey_bootstrap_difference(rows, field):
    """Descriptive dependent-row interval, not out-of-sample validation."""
    clusters = defaultdict(list)
    for row in rows:
        clusters[row["journey"]].append(row)
    groups = list(clusters.values())
    rng = random.Random(13)
    observed = {name: None for name in ("next_flip", "flip_within_3")}
    draws = {name: [] for name in observed}
    for attempt in range(1001):
        sample = rows if attempt == 0 else [row for _ in groups for row in groups[rng.randrange(len(groups))]]
        yes = [row for row in sample if row[field]]
        no = [row for row in sample if not row[field]]
        if not yes or not no:
            continue
        for name in observed:
            difference = sum(row[name] for row in yes) / len(yes) - sum(row[name] for row in no) / len(no)
            if attempt == 0:
                observed[name] = round(difference, 6)
            else:
                draws[name].append(difference)
    return {name: {"difference": observed[name],
                   "journey_cluster_percentile_95": [round(sorted(values)[24], 6), round(sorted(values)[974], 6)]
                   if len(values) == 1000 else None}
            for name, values in draws.items()}


def analyze(rows):
    output = {"all": summarize(rows),
              "progress_state": categorical(rows, "progress_state"),
              "adverse_state": categorical(rows, "adverse_state")}
    for name in ("progress_rejection_or_return", "adverse_close_beyond",
                 "both_boundaries_exceeded", "inverted_pivot_prices"):
        output[name] = categorical(rows, name)
    output["missing_level"] = {
        "progress": sum(r["progress_state"] == "no_level" for r in rows),
        "adverse": sum(r["adverse_state"] == "no_level" for r in rows)}
    output["level_age_h4_median"] = {
        name: median([r[f"{name}_level_age_h4"] for r in rows
                      if r[f"{name}_level_age_h4"] is not None])
        for name in ("progress", "adverse")}
    continuation = [r for r in rows if r["journey_bar"] > 1]
    output["continuation_only"] = {"all": summarize(continuation),
                                   "progress_state": categorical(continuation, "progress_state"),
                                   "adverse_state": categorical(continuation, "adverse_state")}
    output["h1_paths"] = {}
    for path in sorted({r["h1_path_state"] for r in rows}):
        subset = [r for r in rows if r["h1_path_state"] == path]
        output["h1_paths"][path] = {
            "all": summarize(subset),
            "progress_rejection_or_return": categorical(subset, "progress_rejection_or_return"),
            "adverse_close_beyond": categorical(subset, "adverse_close_beyond"),
            "within_h4_body_rawclose_tertiles": {
                name: overlap_contrast(subset, name, 3, 10)
                for name in ("progress_rejection_or_return", "adverse_close_beyond")}}
    warnings = [r for r in rows if r["h1_opposed"]]
    output["h1_ending_opposition"] = {
        "all": summarize(warnings),
        "progress_rejection_or_return": categorical(warnings, "progress_rejection_or_return"),
        "adverse_close_beyond": categorical(warnings, "adverse_close_beyond"),
        "adverse_state": categorical(warnings, "adverse_state"),
        "progress_state": categorical(warnings, "progress_state"),
        "progress_rejection_or_return_bootstrap": journey_bootstrap_difference(
            warnings, "progress_rejection_or_return"),
        "within_h4_body_rawclose_tertiles": {
            name: overlap_contrast(warnings, name, 3, 10)
            for name in ("progress_rejection_or_return", "adverse_close_beyond")},
        "within_h4_body_rawclose_quintiles": {
            name: overlap_contrast(warnings, name, 5, 20)
            for name in ("progress_rejection_or_return", "adverse_close_beyond")},
        "tertiles_plus_h4_delta_wick": {
            name: overlap_contrast(warnings, name, 3, 10,
                                   ("h4_delta_contract", "h4_wick_present"))
            for name in ("progress_rejection_or_return", "adverse_close_beyond")}}
    no_opposition = [r for r in rows if r["h1_path_state"] == "no_opposition"]
    output["no_h1_opposition_adverse_break_bootstrap"] = journey_bootstrap_difference(
        no_opposition, "adverse_close_beyond")
    output["continuation_h4_overlap"] = {
        name: overlap_contrast(continuation, name, 3, 10)
        for name in ("progress_rejection_or_return", "progress_fresh_close_beyond",
                     "progress_held_close_beyond", "progress_return_inside",
                     "progress_probe_rejected", "adverse_close_beyond")}
    output["year_side_all"] = {}
    output["year_side"] = {}
    output["year_side_no_h1_opposition"] = {}
    for year in (2024, 2025, 2026):
        for side in (1, -1):
            all_subset = [r for r in rows if r["year"] == year and r["side"] == side]
            subset = [r for r in warnings if r["year"] == year and r["side"] == side]
            no_h1 = [r for r in rows if r["year"] == year and r["side"] == side
                     and r["h1_path_state"] == "no_opposition"]
            output["year_side_all"][f"{year}_{'LONG' if side == 1 else 'SHORT'}"] = {
                "all": summarize(all_subset),
                "progress_state": categorical(all_subset, "progress_state"),
                "adverse_state": categorical(all_subset, "adverse_state")}
            output["year_side"][f"{year}_{'LONG' if side == 1 else 'SHORT'}"] = {
                "all_h1_opposed": summarize(subset),
                "progress_rejection_or_return": categorical(subset, "progress_rejection_or_return"),
                "adverse_close_beyond": categorical(subset, "adverse_close_beyond")}
            output["year_side_no_h1_opposition"][f"{year}_{'LONG' if side == 1 else 'SHORT'}"] = {
                "all_no_h1_opposition": summarize(no_h1),
                "adverse_close_beyond": categorical(no_h1, "adverse_close_beyond")}
    tails = [r for r in rows if r["journey_closed_bars"] >= 10]
    assert len({r["journey"] for r in tails}) == 88
    output["long_journeys"] = {"journeys": 88, "decisions": len(tails)}
    for name in ("progress_rejection_or_return", "adverse_close_beyond"):
        chosen = [r for r in tails if r[name]]
        h1_chosen = [r for r in chosen if r["h1_opposed"]]
        output["long_journeys"][name] = {
            "journeys_with_event": len({r["journey"] for r in chosen}),
            "event_decisions": len(chosen),
            "event_not_next_flip": sum(not r["next_flip"] for r in chosen),
            "h1_opposed_event_decisions": len(h1_chosen),
            "h1_opposed_event_not_next_flip": sum(not r["next_flip"] for r in h1_chosen),
            "h1_opposed_event_remaining_favorable_ranges_median": median(
                [r["remaining_favorable_ranges"] for r in h1_chosen
                 if r["remaining_favorable_ranges"] is not None])}
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--m1", type=Path, required=True)
    parser.add_argument("--h4", type=Path, required=True)
    parser.add_argument("--integrated", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with (args.integrated / "summary.json").open(encoding="utf-8") as stream:
        upstream = json.load(stream)
    source_hashes = {"m1": digest(args.m1), "h4": digest(args.h4)}
    assert source_hashes["m1"] == upstream["sources"]["m1_sha256"]
    assert source_hashes["h4"] == upstream["sources"]["h4_sha256"]
    input_features = args.integrated / "decision_features.csv"
    input_labels = args.integrated / "future_labels.csv"
    raw_features, parity = construct_features(args.m1, args.h4, input_features)
    joined = make_rows(raw_features, input_features, input_labels)
    report = {"status": "consumed-development-observation-only",
              "source_sha256": source_hashes, "m1_h4_parity": parity,
              "summary": analyze(joined)}
    args.output.mkdir(parents=True, exist_ok=True)
    write_csv(args.output / "decision_features.csv", raw_features)
    # Preserve physical separation: this is the *unchanged* HA-4C/D label set.
    write_csv(args.output / "future_labels.csv", read_csv(input_labels))
    (args.output / "summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"source_sha256": source_hashes, "parity": parity,
                      "all": report["summary"]["all"],
                      "missing_level": report["summary"]["missing_level"]}, indent=2))


if __name__ == "__main__":
    main()
