#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv
from pathlib import Path

def rows(path):
    with Path(path).open("r",encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def canonical(rs):
    return [
        (
            r.get("observed_at",""),r.get("event",""),r.get("timeframe",""),
            r.get("available_at",""),r.get("object_id",""),r.get("detail","")
        )
        for r in rs if not r.get("event","").startswith("D154F_")
    ]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("off_csv")
    ap.add_argument("on_csv")
    a=ap.parse_args()
    off=rows(a.off_csv); on=rows(a.on_csv)

    if any(r.get("event","").startswith("D154F_") for r in off):
        print("FAIL: OFF ledger contains D154F rows")
        return 2
    n=sum(r.get("event","").startswith("D154F_") for r in on)
    if n==0:
        print("FAIL: ON ledger contains no D154F rows")
        return 2

    x=canonical(off); y=canonical(on)
    if x!=y:
        print(f"FAIL: canonical rows OFF={len(x)} ON={len(y)}")
        for i in range(min(len(x),len(y))):
            if x[i]!=y[i]:
                print("first mismatch:",i)
                print("OFF:",x[i])
                print("ON :",y[i])
                break
        return 1

    print(f"D154F NON-INTERFERENCE PARITY: PASS | canonical_rows={len(x)} | d154f_rows={n}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
