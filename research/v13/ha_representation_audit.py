"""Observation-only V13 HA-0..HA-3 audit. Never generates trading signals.

H4 rows are consumed in time order after the following H4 open confirms their
completion. M1 is streamed separately for retrospective raw-extreme labels and
H4 source parity; no future M1 data is available to a representation decision.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


START = datetime(2024, 1, 1)
END = datetime(2026, 8, 28, 20)  # Last in-window execution open.
ALPHA = 2 / 3  # EMA period 2.


def dt(row: dict[str, str]) -> datetime:
    return datetime.strptime(row["<DATE>"] + " " + row["<TIME>"], "%Y.%m.%d %H:%M:%S")


def median(values):
    return round(statistics.median(values), 4) if values else None


def ratio(n, d):
    return round(n / d, 6) if d else None


@dataclass
class Bar:
    time: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass
class Journey:
    number: int
    side: int
    signal_start: datetime
    entry: datetime
    signal_flip: datetime | None = None
    exit: datetime | None = None
    exit_price: float | None = None
    bars: int = 0
    extreme: float | None = None
    extreme_time: datetime | None = None
    adverse: float | None = None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_bars(path: Path) -> list[Bar]:
    out = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            out.append(Bar(dt(row), *(float(row[k]) for k in ("<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>"))))
    assert all(a.time < b.time for a, b in zip(out, out[1:])), "H4 source not chronological"
    return out


class HA:
    def __init__(self, name: str):
        self.name = name
        self.open = None
        self.close = None
        self.color = 0
        self.pre = None
        self.post_open = None
        self.post_close = None

    def update(self, b: Bar) -> tuple[float, float, int, float, float]:
        if self.name == "PRE_EMA2":
            raw = (b.open, b.high, b.low, b.close)
            self.pre = raw if self.pre is None else tuple(ALPHA * x + (1 - ALPHA) * old for x, old in zip(raw, self.pre))
            o, h, l, c = self.pre
        else:
            o, h, l, c = b.open, b.high, b.low, b.close
        hc = (o + h + l + c) / 4
        if self.open is None:
            ho = (o + c) / 2
        elif self.name == "FAST_R25":
            ho = .25 * self.open + .75 * self.close
        else:
            ho = (self.open + self.close) / 2
        self.open, self.close = ho, hc
        if self.name == "POST_EMA2":
            self.post_open = ho if self.post_open is None else ALPHA * ho + (1 - ALPHA) * self.post_open
            self.post_close = hc if self.post_close is None else ALPHA * hc + (1 - ALPHA) * self.post_close
            ho, hc = self.post_open, self.post_close
        color = 1 if hc > ho else -1 if hc < ho else self.color
        self.color = color
        return ho, hc, color, max(h, ho, hc), min(l, ho, hc)


def make_representations(bars: list[Bar]):
    names = ("STD", "FAST_R25", "PRE_EMA2", "POST_EMA2")
    states = {name: HA(name) for name in names}
    observations = {name: [] for name in names}
    journeys = {name: [] for name in names}
    active = {name: None for name in names}
    count = 0
    bar_indexes = {b.time: i for i, b in enumerate(bars)}
    for b, nxt in zip(bars, bars[1:]):
        # The signal bar is not known until the next H4 begins.
        previous = {name: state.color for name, state in states.items()}
        current = {name: state.update(b) for name, state in states.items()}
        if b.time < START or nxt.time > END:
            continue
        count += 1
        for name, (ho, hc, side, hh, hl) in current.items():
            prior = previous[name]
            j = active[name]
            if j is not None and side != j.side:
                j.signal_flip, j.exit, j.exit_price = b.time, nxt.time, nxt.open
                j = None
            if j is None and prior != 0 and side != prior:
                j = Journey(len(journeys[name]) + 1, side, b.time, nxt.time)
                journeys[name].append(j)
            active[name] = j
            if j is not None:
                j.bars += 1
            upper, lower = hh-max(ho, hc), min(ho, hc)-hl
            hrange = hh-hl
            previous_bar = observations[name][-1] if observations[name] else None
            observations[name].append({
                "signal": b.time, "known_at": nxt.time, "side": side,
                "raw_open": b.open, "raw_high": b.high, "raw_low": b.low, "raw_close": b.close,
                "execution_raw_open": nxt.open,
                "ha_open": ho, "ha_high": hh, "ha_low": hl, "ha_close": hc,
                "body": abs(hc-ho), "delta": hc-ho,
                "range": hrange,
                "body_ratio": abs(hc-ho)/hrange if hrange else 0,
                "upper_wick": upper, "lower_wick": lower,
                "opposite_wick": lower if side == 1 else upper,
                "directional_wick": upper if side == 1 else lower,
                "no_opposite_wick": (lower if side == 1 else upper) < 1e-9,
                "delta_change": (hc-ho)-previous_bar["delta"] if previous_bar else None,
                "body_change": abs(hc-ho)-previous_bar["body"] if previous_bar else None,
                "raw_body_ratio": abs(b.close-b.open)/(b.high-b.low) if b.high>b.low else 0,
                "raw_close_minus_ha_close": b.close-hc,
                "raw_close_minus_ha_open": b.close-ho,
                "journey": j.number if j else None,
                "streak": j.bars if j else 0,
                "child": j.bars if j is not None and j.bars <= 10 else None,
                "signal_index": bar_indexes[b.time],
            })
    return observations, journeys, count


def annotate_m1(path: Path, h4: list[Bar], journeys: dict[str, list[Journey]]):
    # Independently reproduce exported H4 OHLC from chronological M1.
    h4map = {b.time: b for b in h4 if START <= b.time <= END}
    m1bar = None
    parity = Counter()
    indexes = {name: 0 for name in journeys}
    closed = {name: [j for j in js if j.exit is not None] for name, js in journeys.items()}

    def flush(agg):
        if agg is None or agg.time not in h4map:
            return
        reference = h4map[agg.time]
        parity["bars"] += 1
        if any(abs(getattr(agg, key) - getattr(reference, key)) > 0.011 for key in ("open", "high", "low", "close")):
            parity["mismatches"] += 1

    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            stamp = dt(row)
            if stamp >= END:
                break
            o, h, l, c = (float(row[k]) for k in ("<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>"))
            bucket = stamp.replace(hour=(stamp.hour // 4) * 4, minute=0, second=0)
            if m1bar is None or bucket != m1bar.time:
                flush(m1bar)
                m1bar = Bar(bucket, o, h, l, c)
            else:
                m1bar.high = max(m1bar.high, h)
                m1bar.low = min(m1bar.low, l)
                m1bar.close = c
            for name, js in closed.items():
                index = indexes[name]
                while index < len(js) and stamp >= js[index].exit:
                    index += 1
                indexes[name] = index
                if index == len(js):
                    continue
                j = js[index]
                if stamp < j.entry:
                    continue
                candidate = h if j.side == 1 else l
                if j.extreme is None or (candidate > j.extreme if j.side == 1 else candidate < j.extreme):
                    j.extreme, j.extreme_time = candidate, stamp
                adverse = l if j.side == 1 else h
                if j.adverse is None or (adverse < j.adverse if j.side == 1 else adverse > j.adverse):
                    j.adverse = adverse
    flush(m1bar)
    return dict(parity)


def describe(observations, journeys, h4_indexes):
    out = {}
    for name, obs in observations.items():
        all_js = journeys[name]
        js = [j for j in all_js if j.exit is not None]
        lengths = [j.bars for j in js]
        lag = [(j.exit-j.extreme_time).total_seconds()/3600 for j in js if j.extreme_time]
        giveback = [j.side*(j.extreme-j.exit_price) for j in js if j.extreme is not None]
        slices = {}
        for year in (2024, 2025, 2026):
            for side in (1, -1):
                subset = [j for j in js if j.signal_start.year == year and j.side == side]
                slices[f"{year}_{'LONG' if side == 1 else 'SHORT'}"] = {
                    "closed_journeys": len(subset),
                    "median_lag_h": median([(j.exit-j.extreme_time).total_seconds()/3600 for j in subset if j.extreme_time]),
                    "median_giveback_price": median([j.side*(j.extreme-j.exit_price) for j in subset if j.extreme is not None]),
                }
        out[name] = {
            "decision_bars": len(obs), "closed_journeys": len(js), "open_journeys": len(all_js)-len(js),
            "closed_child_decisions": sum(b["child"] is not None and b["journey"] is not None and b["journey"] <= len(js) for b in obs),
            "one_bar_journeys": sum(n == 1 for n in lengths), "ten_plus_journeys": sum(n >= 10 for n in lengths),
            "median_length_bars": median(lengths),
            "survival_after_flip_1_2_3": [ratio(sum(n >= k+1 for n in lengths), len(lengths)) for k in (1, 2, 3)],
            "median_extreme_to_flip_hours": median(lag),
            "median_giveback_gold_price": median(giveback),
            "giveback_p90_gold_price": round(sorted(giveback)[int(.9*(len(giveback)-1))], 4) if giveback else None,
            "sum_giveback_gold_price": round(sum(giveback), 4),
            "extreme_in_flip_or_prior_two_bars_share": ratio(sum(j.extreme_time is not None and h4_indexes.get(j.extreme_time.replace(hour=(j.extreme_time.hour // 4) * 4, minute=0, second=0), -999999) >= h4_indexes[j.signal_flip] - 2 for j in js), len(js)),
            "slices": slices,
        }
    std = observations["STD"]
    for name, obs in observations.items():
        out[name]["color_disagreement_with_std"] = ratio(sum(a["side"] != b["side"] for a, b in zip(obs, std)), len(std))
        std_flips = [i for i in range(1, len(std)) if std[i]["side"] != std[i-1]["side"]]
        own_flips = [i for i in range(1, len(obs)) if obs[i]["side"] != obs[i-1]["side"]]
        out[name]["flip_count"] = len(own_flips)
        out[name]["same_bar_flip_overlap_with_std"] = ratio(len(set(std_flips) & set(own_flips)), len(std_flips))
    return out


def morphology(obs):
    # Outcome is deliberately computed from the *next* completed bar and not
    # inserted into the decision ledger.
    usable = [i for i in range(len(obs)-1) if obs[i]["journey"] is not None]
    def flip(i):
        return obs[i+1]["side"] != obs[i]["side"]
    def summary(indices):
        return {"n": len(indices), "next_flip_share": ratio(sum(flip(i) for i in indices), len(indices))}
    no_wick = [i for i in usable if obs[i]["opposite_wick"] < 1e-9]
    has_wick = [i for i in usable if obs[i]["opposite_wick"] >= 1e-9]
    q = sorted(usable, key=lambda i: obs[i]["body"] / obs[i]["range"] if obs[i]["range"] else 0)
    quintiles = [summary(q[k*len(q)//5:(k+1)*len(q)//5]) for k in range(5)]
    reappear = [i for i in usable if i > 0 and obs[i-1]["journey"] == obs[i]["journey"] and obs[i-1]["opposite_wick"] < 1e-9 and obs[i]["opposite_wick"] >= 1e-9]
    first_reappear = []
    seen_journeys = set()
    for i in reappear:
        if obs[i]["journey"] not in seen_journeys:
            seen_journeys.add(obs[i]["journey"])
            first_reappear.append(i)
    first_survival = {f"flip_within_{k}_bars": ratio(sum(any(obs[t]["side"] != obs[i]["side"] for t in range(i+1, min(len(obs), i+k+1))) for i in first_reappear), len(first_reappear)) for k in (1, 2, 3)}
    contraction = [i for i in usable if i > 0 and obs[i-1]["journey"] == obs[i]["journey"] and obs[i]["body"] < obs[i-1]["body"] and obs[i]["body"] / obs[i]["range"] < obs[i-1]["body"] / obs[i-1]["range"]]
    return {"opposite_wick_absent": summary(no_wick), "opposite_wick_present": summary(has_wick), "body_ratio_quintiles_low_to_high": quintiles, "wick_reappearance_all_events": summary(reappear), "first_wick_reappearance_per_journey": {"n": len(first_reappear), **first_survival}, "body_and_delta_contraction": summary(contraction)}


def write_ledgers(dest: Path, observations, journeys):
    dest.mkdir(parents=True, exist_ok=True)
    with (dest / "ha3_decision_bars.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["representation", *observations["STD"][0].keys()]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for name, obs in observations.items():
            for b in obs:
                writer.writerow({"representation": name, **b})
    with (dest / "ha3_future_journey_labels.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("representation", "journey", "side", "signal_start", "entry", "flip_signal", "exit", "bars", "raw_extreme", "raw_extreme_time", "raw_adverse", "exit_open", "giveback_price", "lag_hours"))
        for name, js in journeys.items():
            for j in js:
                writer.writerow((name, j.number, j.side, j.signal_start, j.entry, j.signal_flip, j.exit, j.bars, j.extreme, j.extreme_time, j.adverse, j.exit_price, j.side*(j.extreme-j.exit_price) if j.extreme is not None else None, (j.exit-j.extreme_time).total_seconds()/3600 if j.extreme_time else None))
    with (dest / "ha0_future_child_labels.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("representation", "journey", "child", "signal", "entry", "entry_raw_open", "exit", "exit_raw_open", "gross_price_points_no_cost"))
        for name, obs in observations.items():
            by_id = {j.number: j for j in journeys[name] if j.exit is not None}
            for b in obs:
                j = by_id.get(b["journey"])
                if j is not None and b["child"] is not None:
                    writer.writerow((name, j.number, b["child"], b["signal"], b["known_at"], b["execution_raw_open"], j.exit, j.exit_price, j.side*(j.exit_price-b["execution_raw_open"])))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--h4", type=Path, required=True)
    parser.add_argument("--m1", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    bars = read_bars(args.h4)
    obs, journeys, count = make_representations(bars)
    parity = annotate_m1(args.m1, bars, journeys)
    h4_indexes = {b.time: i for i, b in enumerate(bars)}
    report = {"source": {"h4": str(args.h4), "h4_sha256": sha256(args.h4), "m1": str(args.m1), "m1_sha256": sha256(args.m1)}, "window": {"evaluation_start": START.isoformat(), "last_execution_open": END.isoformat(), "completed_decision_bars": count}, "m1_to_h4_parity": parity, "representations": describe(obs, journeys, h4_indexes), "std_morphology": morphology(obs["STD"])}
    report["pre_post_color_difference_bars"] = sum(a["side"] != b["side"] for a, b in zip(obs["PRE_EMA2"], obs["POST_EMA2"]))
    assert parity.get("bars") == count and parity.get("mismatches", 0) == 0, "M1/H4 source parity failed"
    assert report["representations"]["STD"]["closed_journeys"] == 965
    assert report["representations"]["STD"]["closed_child_decisions"] == 3858
    assert report["pre_post_color_difference_bars"] == 0
    write_ledgers(args.output, obs, journeys)
    (args.output / "ha3_summary.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
