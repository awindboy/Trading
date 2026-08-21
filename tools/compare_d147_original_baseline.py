#!/usr/bin/env python3
"""Compare D-146 baseline ledger to D-147 ORIGINAL after diagnostic-row removal."""
from __future__ import annotations
import csv
import sys
from pathlib import Path

DROP_EXACT = {"EA_START", "D147_EXIT_VARIANT_START", "D147_EXIT_VARIANT_STOP"}


def canonical(path: Path):
    rows=[]
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        r=csv.DictReader(f)
        required={"observed_at","event","timeframe","available_at","object_id","detail"}
        if not required.issubset(set(r.fieldnames or [])):
            raise ValueError(f"{path}: unexpected CSV schema {r.fieldnames}")
        for row in r:
            ev=(row.get("event") or "").strip()
            if ev in DROP_EXACT or ev.startswith("D147_") or ev.startswith("EDGE_AUDIT_"):
                continue
            rows.append(tuple((row.get(k) or "") for k in ["observed_at","event","timeframe","available_at","object_id","detail"]))
    return rows


def main():
    if len(sys.argv)!=3:
        print("usage: compare_d147_original_baseline.py D146.csv D147_ORIGINAL.csv", file=sys.stderr)
        return 2
    a,b=map(Path,sys.argv[1:])
    ra,rb=canonical(a),canonical(b)
    if ra==rb:
        print("D147 ORIGINAL PARITY: PASS")
        print(f"canonical_rows={len(ra)}")
        return 0
    print("D147 ORIGINAL PARITY: FAIL")
    print(f"baseline_rows={len(ra)} d147_original_rows={len(rb)}")
    n=min(len(ra),len(rb))
    idx=next((i for i in range(n) if ra[i]!=rb[i]), n)
    if idx<n:
        print(f"first_difference_index={idx}")
        print("BASELINE:", ra[idx])
        print("D147_ORIGINAL:", rb[idx])
    elif len(ra)!=len(rb):
        print(f"common_prefix_rows={n}; one ledger has additional canonical rows")
        if len(ra)>n: print("BASELINE_NEXT:", ra[n])
        if len(rb)>n: print("D147_NEXT:", rb[n])
    return 1

if __name__=="__main__":
    raise SystemExit(main())
