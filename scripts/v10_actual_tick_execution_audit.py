#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V10 bounded-m3 actual-tick execution audit.

Uses only Python stdlib.
Inputs:
  --events   MT5 EA event CSV
  --report   MT5 Strategy Tester XLSX
  --reference-ledger optional persisted V10 bounded-m3 entry ledger

Outputs:
  JSON summary to stdout or --out.

This audit intentionally separates:
  - raw tester statistics
  - event/execution availability
  - gross concurrent exposure
  - opposite-direction overlap
  - M1-reference economics of actually filled signal IDs (when ledger supplied)

It does NOT infer corrected post-fix PnL. That requires rerunning the EA
with persistent EXIT_PENDING semantics.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--events", required=True)
    p.add_argument("--report", required=True)
    p.add_argument("--reference-ledger")
    p.add_argument("--out")
    return p.parse_args()


def read_event_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_xlsx_rows(path: Path):
    with zipfile.ZipFile(path) as zf:
        shared = []
        ss_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
        for si in ss_root.findall("a:si", NS):
            texts = []
            for t in si.iter("{%s}t" % NS["a"]):
                texts.append(t.text or "")
            shared.append("".join(texts))

        sheet = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))
        rows = {}
        for row in sheet.findall(".//a:sheetData/a:row", NS):
            out = {}
            for c in row.findall("a:c", NS):
                ref = c.attrib["r"]
                col = re.match(r"([A-Z]+)", ref).group(1)
                typ = c.attrib.get("t")
                v = c.find("a:v", NS)
                val = None
                if v is not None:
                    raw = v.text
                    if typ == "s":
                        val = shared[int(raw)]
                    else:
                        try:
                            val = float(raw)
                            if val.is_integer():
                                val = int(val)
                        except Exception:
                            val = raw
                out[col] = val
            rows[int(row.attrib["r"])] = out
        return rows


def parse_tester_summary(rows):
    # MT5 report layout used by the V10 actual-tick tester export.
    def val(row, col):
        return rows.get(row, {}).get(col)

    return {
        "history_quality": val(22, "D"),
        "bars": val(23, "D"),
        "ticks": val(23, "H"),
        "net_profit": val(24, "D"),
        "gross_profit": val(25, "D"),
        "gross_loss": val(26, "D"),
        "profit_factor": val(28, "D"),
        "balance_dd_max": val(25, "H"),
        "equity_dd_max": val(25, "L"),
        "sharpe": val(29, "H"),
        "closed_positions": val(36, "D"),
        "deals_reported": val(37, "D"),
        "short_positions": val(36, "H"),
        "long_positions": val(36, "L"),
        "winning_positions": val(37, "H"),
        "losing_positions": val(37, "L"),
        "largest_win": val(38, "H"),
        "largest_loss": val(38, "L"),
    }


def parse_deals(rows):
    header_row = None
    for rn, d in rows.items():
        if d.get("A") == "시간" and d.get("E") == "방향" and d.get("K") == "수익":
            header_row = rn
            break
    if not header_row:
        raise RuntimeError("Could not locate MT5 deal table")

    deals = []
    for rn in sorted(k for k in rows if k > header_row):
        d = rows[rn]
        if d.get("E") not in ("in", "out"):
            continue
        deals.append({
            "time": d.get("A"),
            "deal": d.get("B"),
            "type": d.get("D"),
            "io": d.get("E"),
            "volume": float(d.get("F") or 0),
            "price": float(d.get("G") or 0),
            "profit": float(d.get("K") or 0),
            "comment": d.get("M"),
        })
    return deals


def exposure_audit(deals, unit_lot=0.01):
    gross = long_v = short_v = 0.0
    max_gross = 0.0
    max_time = None
    overlap_seconds = 0.0
    prev_time = None
    prev_long = prev_short = 0.0

    def dt(s):
        return datetime.strptime(s, "%Y.%m.%d %H:%M:%S")

    for d in deals:
        t = dt(d["time"])
        if prev_time is not None and prev_long > 1e-12 and prev_short > 1e-12:
            overlap_seconds += max(0.0, (t - prev_time).total_seconds())

        v = d["volume"]
        if d["io"] == "in":
            gross += v
            if d["type"] == "buy":
                long_v += v
            else:
                short_v += v
        else:
            gross -= v
            if d["type"] == "sell":
                long_v -= v
            else:
                short_v -= v

        if gross > max_gross + 1e-12:
            max_gross = gross
            max_time = d["time"]

        prev_time = t
        prev_long, prev_short = long_v, short_v

    return {
        "max_gross_lots": round(max_gross, 8),
        "max_gross_units": round(max_gross / unit_lot, 4),
        "max_gross_time": max_time,
        "opposite_direction_overlap_hours": round(overlap_seconds / 3600.0, 4),
    }


def parse_fill_signal_ids(events):
    out = set()
    for r in events:
        if r.get("event") != "ENTRY_FILL":
            continue
        m = re.search(r"\bsignal=(\d+)\b", r.get("detail", ""))
        if m:
            out.add(int(m.group(1)))
    return out


def load_reference(path: Path, fill_ids):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        all_rows = list(csv.DictReader(f))
    selected = [r for r in all_rows if float(r.get("W") or 0) > 0]

    def agg(indexes):
        gp = gl = pnl = rr = units = 0.0
        n = 0
        for i in indexes:
            r = selected[i]
            w = float(r["W"])
            p = float(r["natural_child_pnl_m1"]) * w
            rv = float(r["R_child"]) * w
            n += 1
            units += w
            pnl += p
            rr += rv
            if p > 0:
                gp += p
            elif p < 0:
                gl += p
        return {
            "events": n,
            "units": units,
            "pnl": pnl,
            "gross_profit": gp,
            "gross_loss": gl,
            "pf": (gp / -gl) if gl < 0 else None,
            "structural_r": rr,
        }

    all_ids = set(range(len(selected)))
    missing = all_ids - fill_ids
    return {
        "selected_total": agg(sorted(all_ids)),
        "filled_reference_subset": agg(sorted(fill_ids)),
        "not_filled_reference_subset": agg(sorted(missing)),
        "fill_id_count": len(fill_ids),
        "missing_id_count": len(missing),
    }


def main():
    args = parse_args()
    events = read_event_csv(Path(args.events))
    rows = read_xlsx_rows(Path(args.report))
    deals = parse_deals(rows)

    counts = Counter(r.get("event") for r in events)
    nha_reject_times = {
        r["time"] for r in events
        if r.get("event") == "FAST_NHA_EXIT_REJECT"
    }
    entry_reject_details = Counter(
        r.get("detail") for r in events if r.get("event") == "ENTRY_REJECT"
    )

    result = {
        "event_rows": len(events),
        "event_counts": dict(counts),
        "distinct_fast_nha_exit_reject_timestamps": len(nha_reject_times),
        "entry_reject_details": dict(entry_reject_details),
        "tester": parse_tester_summary(rows),
        "exposure": exposure_audit(deals),
    }

    fill_ids = parse_fill_signal_ids(events)
    result["fill_signal_ids"] = {
        "count": len(fill_ids),
        "min": min(fill_ids) if fill_ids else None,
        "max": max(fill_ids) if fill_ids else None,
    }

    if args.reference_ledger:
        result["reference"] = load_reference(Path(args.reference_ledger), fill_ids)

    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
