#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv
from pathlib import Path

def rows(path):
    with Path(path).open("r",encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))
def canonical(rs):
    return [(r.get("observed_at",""),r.get("event",""),r.get("timeframe",""),r.get("available_at",""),r.get("object_id",""),r.get("detail",""))
            for r in rs if not r.get("event","").startswith("D154A_")]
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("off_csv"); ap.add_argument("on_csv"); a=ap.parse_args()
    off=rows(a.off_csv); on=rows(a.on_csv)
    if any(r.get("event","").startswith("D154A_") for r in off):
        print("FAIL: OFF ledger contains D154A rows"); return 2
    on_count=sum(r.get("event","").startswith("D154A_") for r in on)
    if not on_count:
        print("FAIL: ON ledger contains no D154A rows"); return 2
    c0=canonical(off); c1=canonical(on)
    if c0!=c1:
        print(f"FAIL: canonical rows OFF={len(c0)} ON={len(c1)}")
        for i,(x,y) in enumerate(zip(c0,c1)):
            if x!=y:
                print("First mismatch:",i); print("OFF:",x); print("ON :",y); break
        return 1
    print(f"D154A NON-INTERFERENCE PARITY: PASS | canonical_rows={len(c0)} | d154a_rows={on_count}")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
