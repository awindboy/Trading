"""V13 HA-4 observation-only D1 or H1 standard-HA audit from streamed GOLD# M1.

Run D1 and H1 separately. No MTF field changes Baseline-0 orders. Source
exports are consulted for parity only; all decision fields derive from M1 bars
closed before the H4 decision's first next-bar M1 print.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


START = datetime(2024, 1, 1)
LAST_DECISION = datetime(2026, 8, 28, 20)


def stamp(row):
    return datetime.strptime(row["<DATE>"] + " " + row["<TIME>"], "%Y.%m.%d %H:%M:%S")


def bucket(t, tf):
    if tf == "H1":
        return t.replace(minute=0, second=0)
    if tf == "H4":
        return t.replace(hour=4 * (t.hour // 4), minute=0, second=0)
    return t.replace(hour=0, minute=0, second=0)


def ratio(n, d):
    return round(n / d, 6) if d else None


def median(values):
    return round(statistics.median(values), 4) if values else None


def rank_correlation(xs, ys):
    def ranks(values):
        pairs = sorted(enumerate(values), key=lambda item: item[1])
        ranked = [0.0] * len(values)
        start = 0
        while start < len(pairs):
            end = start + 1
            while end < len(pairs) and pairs[end][1] == pairs[start][1]:
                end += 1
            midrank = (start + end + 1) / 2
            for original, _ in pairs[start:end]:
                ranked[original] = midrank
            start = end
        return ranked
    return round(statistics.correlation(ranks(xs), ranks(ys)), 6)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


@dataclass
class Bar:
    time: datetime
    open: float
    high: float
    low: float
    close: float

    def add(self, high, low, close):
        self.high = max(self.high, high)
        self.low = min(self.low, low)
        self.close = close


@dataclass
class Journey:
    id: int
    side: int
    start_signal: datetime
    entry: datetime
    bars: int = 0
    exit: datetime | None = None
    exit_price: float | None = None
    extreme: float | None = None
    extreme_time: datetime | None = None


class StandardHA:
    def __init__(self):
        self.open = None
        self.close = None
        self.color = 0
        self.streak = 0

    def update(self, b):
        old_color = self.color
        hc = (b.open + b.high + b.low + b.close) / 4
        ho = (b.open + b.close) / 2 if self.open is None else (self.open + self.close) / 2
        self.open, self.close = ho, hc
        self.color = 1 if hc > ho else -1 if hc < ho else self.color
        self.streak = self.streak + 1 if self.color == old_color else 1
        hh, hl = max(b.high, ho, hc), min(b.low, ho, hc)
        opposite = min(ho, hc) - hl if self.color == 1 else hh - max(ho, hc)
        return {"color": self.color, "prior_color": old_color, "streak": self.streak,
                "ha_open": ho, "ha_close": hc, "ha_high": hh, "ha_low": hl,
                "body_ratio": abs(hc-ho)/(hh-hl) if hh > hl else 0.0,
                "opposite_wick": opposite, "abs_delta": abs(hc-ho)}


def references(paths):
    out = {}
    for tf, path in paths.items():
        ref = {}
        with path.open(newline="", encoding="utf-8-sig") as stream:
            for row in csv.DictReader(stream, delimiter="\t"):
                t = datetime.strptime(row["<DATE>"], "%Y.%m.%d") if tf == "D1" else stamp(row)
                ref[t] = tuple(float(row[k]) for k in ("<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>"))
        out[tf] = ref
    return out


def run(m1, exports, stage):
    context_tf = "D1" if stage == "d1" else "H1"
    refs = references({"H4": exports["H4"], context_tf: exports[context_tf]})
    aggs = {tf: None for tf in ("H4", context_tf)}
    states = {tf: StandardHA() for tf in aggs}
    parity = {tf: {"checked": 0, "mismatched": 0, "missing_export": 0} for tf in aggs}
    context = None
    context_events = []
    h4 = []
    journeys = []
    active = None
    raw_decisions = 0
    source_m1_rows = 0

    def complete(tf, b, known_at, next_raw_open):
        nonlocal context, active, raw_decisions
        reference = refs[tf].get(b.time)
        if reference is None:
            parity[tf]["missing_export"] += 1
        else:
            parity[tf]["checked"] += 1
            if any(abs(a - c) > .011 for a, c in zip((b.open, b.high, b.low, b.close), reference)):
                parity[tf]["mismatched"] += 1
        prior = states[tf].color
        feature = states[tf].update(b)
        if tf == context_tf:
            context = {"signal": b.time, "known_at": known_at, **feature}
            if stage == "h1":
                context_events.append(context)
            return
        if b.time < START or known_at > LAST_DECISION:
            return
        raw_decisions += 1
        side = feature["color"]
        if active is not None and side != active.side:
            active.exit, active.exit_price = known_at, next_raw_open
            active = None
        if active is None and prior != 0 and side != prior:
            active = Journey(len(journeys) + 1, side, b.time, known_at)
            journeys.append(active)
        if active is None:
            return
        active.bars += 1
        assert context is not None and context["known_at"] <= known_at
        raw_range = b.high - b.low
        prior_h4 = h4[-1] if h4 and h4[-1]["journey"] == active.id else None
        obs = {"signal": b.time, "known_at": known_at, "side": side,
               "journey": active.id, "journey_bar": active.bars,
               "child": active.bars if active.bars <= 10 else None,
               "h4_body_ratio": feature["body_ratio"],
               "h4_opposite_wick": feature["opposite_wick"],
               "h4_streak": feature["streak"],
               "h4_abs_delta": feature["abs_delta"],
               "h4_delta_contract": prior_h4 is not None and feature["abs_delta"] < prior_h4["h4_abs_delta"],
               "h4_raw_close_vs_ha_close_normalized": side * (b.close - feature["ha_close"]) / raw_range if raw_range else 0.0,
               "h4_raw_close_vs_ha_open_normalized": side * (b.close - feature["ha_open"]) / raw_range if raw_range else 0.0,
               "h4_raw_body_signed_normalized": side * (b.close - b.open) / raw_range if raw_range else 0.0,
               "context_signal": context["signal"],
               "context_known_at": context["known_at"],
               "context_color": context["color"],
               "context_body_ratio": context["body_ratio"],
               "context_opposite_wick": context["opposite_wick"],
               "context_streak": context["streak"],
               "aligned": context["color"] == side}
        if stage == "h1":
            inside = [e for e in context_events if b.time <= e["signal"] < known_at]
            obs["h1_bars_in_h4"] = len(inside)
            obs["h1_flips_in_h4"] = sum(e["color"] != e["prior_color"] for e in inside)
            obs["h1_opposed_bars_in_h4"] = sum(e["color"] != side for e in inside)
            # Retain only the next H4 bar's possible H1 events.
            context_events[:] = [e for e in context_events if e["signal"] >= b.time]
        h4.append(obs)

    with m1.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            t = stamp(row)
            if t > LAST_DECISION:
                break
            o, hi, lo, cl = (float(row[k]) for k in ("<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>"))
            source_m1_rows += 1
            # The same tick closes H1/D1 first, then H4. That completed
            # context is causally available to the H4 decision at this tick.
            for tf in (context_tf, "H4"):
                key = bucket(t, tf)
                agg = aggs[tf]
                if agg is None:
                    aggs[tf] = Bar(key, o, hi, lo, cl)
                elif agg.time != key:
                    complete(tf, agg, t, o)
                    aggs[tf] = Bar(key, o, hi, lo, cl)
                else:
                    agg.add(hi, lo, cl)
            # Raw M1 outcomes are accumulated only after old-Journey exit and
            # new-Journey entry have been handled at this print.
            if active is not None:
                favorable = hi if active.side == 1 else lo
                if active.extreme is None or (favorable > active.extreme if active.side == 1 else favorable < active.extreme):
                    active.extreme, active.extreme_time = favorable, t
    return {"decisions": h4, "journeys": journeys, "parity": parity,
            "completed_h4_decisions": raw_decisions, "m1_rows": source_m1_rows}


def analyze(result, stage):
    decisions = result["decisions"]
    journeys = result["journeys"]
    by_id = {j.id: j for j in journeys}
    valid = []
    for i, d in enumerate(decisions):
        j = by_id[d["journey"]]
        if j.exit is None or i + 3 >= len(decisions):
            continue
        labels = {"next_flip": decisions[i+1]["side"] != d["side"],
                  "flip_within_2": any(decisions[k]["side"] != d["side"] for k in range(i+1, i+3)),
                  "flip_within_3": any(decisions[k]["side"] != d["side"] for k in range(i+1, i+4)),
                  "peak_already": j.extreme_time is not None and j.extreme_time < d["known_at"],
                  "journey_closed_bars": j.bars}
        valid.append({**d, **labels})

    def group(rows):
        return {"h4_decisions": len(rows), "distinct_journeys": len({r["journey"] for r in rows}),
                "next_flip": ratio(sum(r["next_flip"] for r in rows), len(rows)),
                "flip_within_2": ratio(sum(r["flip_within_2"] for r in rows), len(rows)),
                "flip_within_3": ratio(sum(r["flip_within_3"] for r in rows), len(rows)),
                "raw_extreme_already_occurred": ratio(sum(r["peak_already"] for r in rows), len(rows))}

    summary = {"all": group(valid),
               "aligned": group([r for r in valid if r["aligned"]]),
               "opposed": group([r for r in valid if not r["aligned"]])}
    clustered = defaultdict(list)
    for r in valid:
        clustered[r["journey"]].append(r)
    cluster_rows = list(clustered.values())
    rng = random.Random(13)
    draws = {key: [] for key in ("next_flip", "flip_within_3", "peak_already")}
    for _ in range(1000):
        picked = [cluster_rows[rng.randrange(len(cluster_rows))] for _ in cluster_rows]
        for key in draws:
            counts = {True: [0, 0], False: [0, 0]}
            for journey_rows in picked:
                for r in journey_rows:
                    slot = counts[r["aligned"]]
                    slot[0] += int(r[key])
                    slot[1] += 1
            if counts[True][1] and counts[False][1]:
                draws[key].append(counts[False][0]/counts[False][1] - counts[True][0]/counts[True][1])
    summary["cluster_bootstrap_opposed_minus_aligned"] = {
        key: {"difference": round(summary["opposed"]["next_flip" if key == "next_flip" else "flip_within_3" if key == "flip_within_3" else "raw_extreme_already_occurred"] - summary["aligned"]["next_flip" if key == "next_flip" else "flip_within_3" if key == "flip_within_3" else "raw_extreme_already_occurred"], 6),
              "percentile_95_interval": [round(sorted(values)[24], 6), round(sorted(values)[974], 6)]}
        for key, values in draws.items()}
    # Rank quintiles are descriptive bins only; no numerical boundary is
    # allowed to become an action rule from this analysis.
    ordered = sorted(valid, key=lambda r: r["h4_body_ratio"])
    for q in range(5):
        subset = ordered[q*len(ordered)//5:(q+1)*len(ordered)//5]
        summary[f"h4_body_quintile_{q+1}"] = {
            "aligned": group([r for r in subset if r["aligned"]]),
            "opposed": group([r for r in subset if not r["aligned"]])}
    close_ordered = sorted(valid, key=lambda r: r["h4_raw_close_vs_ha_close_normalized"])
    for q in range(5):
        subset = close_ordered[q*len(valid)//5:(q+1)*len(valid)//5]
        summary[f"h4_raw_close_quintile_{q+1}"] = {
            "aligned": group([r for r in subset if r["aligned"]]),
            "opposed": group([r for r in subset if not r["aligned"]])}
    body_bin = {id(r): min(5, 1 + 5*i//len(valid)) for i, r in enumerate(ordered)}
    close_bin = {id(r): min(5, 1 + 5*i//len(valid)) for i, r in enumerate(close_ordered)}
    summary["h4_body_x_rawclose"] = {}
    for bq in range(1, 6):
        for cq in range(1, 6):
            subset = [r for r in valid if body_bin[id(r)] == bq and close_bin[id(r)] == cq]
            summary["h4_body_x_rawclose"][f"body{bq}_close{cq}"] = {
                "aligned": group([r for r in subset if r["aligned"]]),
                "opposed": group([r for r in subset if not r["aligned"]])}
    overlap = [v for v in summary["h4_body_x_rawclose"].values()
               if v["aligned"]["h4_decisions"] >= 20 and v["opposed"]["h4_decisions"] >= 20]
    weights = [min(v["aligned"]["h4_decisions"], v["opposed"]["h4_decisions"]) for v in overlap]
    summary["h4_body_x_rawclose_overlap"] = {
        "cells_with_at_least_20_per_group": len(overlap),
        "decisions_in_cells": sum(v["aligned"]["h4_decisions"] + v["opposed"]["h4_decisions"] for v in overlap),
        "min_group_weighted_next_flip_difference": round(sum(w*(v["opposed"]["next_flip"]-v["aligned"]["next_flip"]) for w, v in zip(weights, overlap))/sum(weights), 6) if weights else None}
    for contraction in (True, False):
        subset = [r for r in valid if r["h4_delta_contract"] == contraction]
        summary[f"h4_delta_contract_{str(contraction).lower()}"] = {
            "aligned": group([r for r in subset if r["aligned"]]),
            "opposed": group([r for r in subset if not r["aligned"]])}
    context_ordered = sorted(valid, key=lambda r: r["context_body_ratio"])
    for q in range(5):
        summary[f"context_body_quintile_{q+1}"] = group(context_ordered[q*len(valid)//5:(q+1)*len(valid)//5])
    summary["context_wick"] = {
        "no_opposite": group([r for r in valid if r["context_opposite_wick"] < 1e-9]),
        "opposite_present": group([r for r in valid if r["context_opposite_wick"] >= 1e-9])}
    summary["rank_association"] = {
        "context_body_vs_h4_body": rank_correlation([r["context_body_ratio"] for r in valid], [r["h4_body_ratio"] for r in valid]),
        "context_body_vs_next_h4_flip": rank_correlation([r["context_body_ratio"] for r in valid], [int(r["next_flip"]) for r in valid]),
        "context_streak_vs_next_h4_flip": rank_correlation([r["context_streak"] for r in valid], [int(r["next_flip"]) for r in valid])}
    for year in (2024, 2025, 2026):
        for side, label in ((1, "LONG"), (-1, "SHORT")):
            subset = [r for r in valid if r["signal"].year == year and r["side"] == side]
            summary[f"{year}_{label}"] = {"aligned": group([r for r in subset if r["aligned"]]),
                                         "opposed": group([r for r in subset if not r["aligned"]])}
    if stage == "h1":
        counts = sorted({r["h1_flips_in_h4"] for r in valid})
        summary["h1_flip_count"] = {str(n): group([r for r in valid if r["h1_flips_in_h4"] == n]) for n in counts}
        # A last-H1 disagreement is a warning only in retrospect. Include all
        # warnings, especially those not followed by an H4 flip.
        warnings = [r for r in valid if not r["aligned"]]
        summary["h1_warning_next_h4_not_flip"] = sum(not r["next_flip"] for r in warnings)
        summary["h1_warning_no_flip_within_3"] = sum(not r["flip_within_3"] for r in warnings)
        summary["h1_warning_share_of_next_h4_flips"] = ratio(sum(r["next_flip"] for r in warnings), sum(r["next_flip"] for r in valid))
        for birth, label in ((True, "journey_birth"), (False, "journey_continuation")):
            subset = [r for r in valid if (r["journey_bar"] == 1) == birth]
            summary[label] = {"aligned": group([r for r in subset if r["aligned"]]),
                              "opposed": group([r for r in subset if not r["aligned"]])}
        tail_warnings = [r for r in warnings if r["journey_closed_bars"] >= 10]
        summary["long_journey_warnings"] = {
            "warning_decisions": len(tail_warnings),
            "distinct_long_journeys": len({r["journey"] for r in tail_warnings}),
            "not_next_h4_flip": sum(not r["next_flip"] for r in tail_warnings)}

    closed = [j for j in journeys if j.exit is not None]
    return {"stage": stage, "completed_h4_decisions": result["completed_h4_decisions"],
            "active_h4_decisions": len(decisions), "closed_journeys": len(closed),
            "closed_child_decisions": sum(r["child"] is not None and by_id[r["journey"]].exit is not None for r in decisions),
            "m1_rows_consumed": result["m1_rows"], "parity": result["parity"],
            "median_raw_extreme_to_exit_h": median([(j.exit-j.extreme_time).total_seconds()/3600 for j in closed if j.extreme_time]),
            "median_raw_extreme_giveback": median([j.side*(j.extreme-j.exit_price) for j in closed if j.extreme is not None]),
            "context": summary}, valid


def write_rows(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", choices=("d1", "h1"), required=True)
    p.add_argument("--m1", type=Path, required=True)
    p.add_argument("--h4", type=Path, required=True)
    p.add_argument("--d1", type=Path)
    p.add_argument("--h1", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    context_tf = "D1" if a.stage == "d1" else "H1"
    export = a.d1 if a.stage == "d1" else a.h1
    assert export is not None
    result = run(a.m1, {"H4": a.h4, context_tf: export}, a.stage)
    report, valid = analyze(result, a.stage)
    report["source_sha256"] = {"m1": digest(a.m1), "h4": digest(a.h4), context_tf.lower(): digest(export)}
    assert report["completed_h4_decisions"] == 4108
    assert report["active_h4_decisions"] == 4108
    assert report["closed_journeys"] == 965
    assert report["closed_child_decisions"] == 3858
    assert all(v["mismatched"] == 0 and v["missing_export"] == 0 for v in report["parity"].values())
    a.output.mkdir(parents=True, exist_ok=True)
    # Features and outcomes are physically separate artifacts.
    write_rows(a.output / "decision_features.csv", result["decisions"])
    label_keys = ("signal", "journey", "next_flip", "flip_within_2", "flip_within_3", "peak_already", "journey_closed_bars")
    write_rows(a.output / "future_labels.csv", [{k: r[k] for k in label_keys} for r in valid])
    (a.output / "summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "context"}, indent=2))
    print(json.dumps({k: v for k, v in report["context"].items() if k in ("all", "aligned", "opposed", "h1_flip_count", "h1_warning_next_h4_not_flip")}, indent=2))


if __name__ == "__main__":
    main()
