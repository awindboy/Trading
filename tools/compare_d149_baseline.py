#!/usr/bin/env python3
"""Compare D-148 ORIGINAL baseline with D-149 ORIGINAL + EM_OFF control."""
from __future__ import annotations
import csv
import re
import sys
from pathlib import Path

# Research identity/action rows are diagnostic. Two legacy stop summaries include
# CSV emitted/suppressed counters, which necessarily change when D149 diagnostics
# become compact-visible; they are excluded from behavior parity.
DROP_EXACT = {
    "EA_START",
    "REGIME_RESEARCH_STOP_SUMMARY",
    "D135_STOP_SUMMARY",
}


def canonical(path: Path):
    rows=[]
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f)
        required={"observed_at","event","timeframe","available_at","object_id","detail"}
        if not required.issubset(set(r.fieldnames or [])):
            raise ValueError(f"{path}: unexpected CSV schema {r.fieldnames}")
        for row in r:
            ev=(row.get("event") or "").strip()
            if (ev in DROP_EXACT or ev.startswith("D147_") or
                ev.startswith("D149_") or ev.startswith("EDGE_AUDIT_")):
                continue
            rows.append(tuple((row.get(k) or "") for k in
                              ["observed_at","event","timeframe","available_at","object_id","detail"]))
    return rows


def main():
    if len(sys.argv)!=3:
        print("usage: compare_d149_baseline.py D148_ORIGINAL.csv D149_ORIGINAL_EM_OFF.csv",file=sys.stderr)
        return 2
    a,b=map(Path,sys.argv[1:])
    ra,rb=canonical(a),canonical(b)
    if ra==rb:
        print("D149 BASELINE CONTROL PARITY: PASS")
        print(f"canonical_rows={len(ra)}")
        return 0
    print("D149 BASELINE CONTROL PARITY: FAIL")
    print(f"d148_rows={len(ra)} d149_control_rows={len(rb)}")
    n=min(len(ra),len(rb))
    idx=next((i for i in range(n) if ra[i]!=rb[i]),n)
    if idx<n:
        print(f"first_difference_index={idx}")
        print("D148:",ra[idx])
        print("D149:",rb[idx])
    else:
        print(f"common_prefix_rows={n}")
        if len(ra)>n: print("D148_NEXT:",ra[n])
        if len(rb)>n: print("D149_NEXT:",rb[n])
    return 1

if __name__=="__main__":
    raise SystemExit(main())
