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
        for r in rs if not r.get("event","").startswith("D154C_")
    ]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("off_csv")
    ap.add_argument("on_csv")
    a=ap.parse_args()
    off=rows(a.off_csv); on=rows(a.on_csv)

    if any(r.get("event","").startswith("D154C_") for r in off):
        print("FAIL: OFF ledger contains D154C rows")
        return 2
    n=sum(r.get("event","").startswith("D154C_") for r in on)
    if n==0:
        print("FAIL: ON ledger contains no D154C rows")
        return 2

    a0=canonical(off); a1=canonical(on)
    if a0!=a1:
        print(f"FAIL: canonical rows OFF={len(a0)} ON={len(a1)}")
        for i in range(min(len(a0),len(a1))):
            if a0[i]!=a1[i]:
                print("first mismatch:",i)
                print("OFF:",a0[i])
                print("ON :",a1[i])
                break
        return 1

    print(f"D154C NON-INTERFERENCE PARITY: PASS | canonical_rows={len(a0)} | d154c_rows={n}")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
