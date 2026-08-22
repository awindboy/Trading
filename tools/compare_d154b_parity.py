#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv
from pathlib import Path

def read_rows(path):
    with Path(path).open("r",encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def canonical(rows):
    return [
        (
            r.get("observed_at",""),r.get("event",""),r.get("timeframe",""),
            r.get("available_at",""),r.get("object_id",""),r.get("detail","")
        )
        for r in rows
        if not r.get("event","").startswith("D154B_")
    ]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("off_csv")
    ap.add_argument("on_csv")
    a=ap.parse_args()

    off=read_rows(a.off_csv)
    on=read_rows(a.on_csv)
    if any(r.get("event","").startswith("D154B_") for r in off):
        print("FAIL: OFF ledger contains D154B rows")
        return 2
    on_n=sum(r.get("event","").startswith("D154B_") for r in on)
    if on_n==0:
        print("FAIL: ON ledger contains no D154B rows")
        return 2

    c0=canonical(off); c1=canonical(on)
    if c0!=c1:
        print(f"FAIL: canonical rows OFF={len(c0)} ON={len(c1)}")
        for i in range(min(len(c0),len(c1))):
            if c0[i]!=c1[i]:
                print("first mismatch index:",i)
                print("OFF:",c0[i])
                print("ON :",c1[i])
                break
        return 1

    print(f"D154B NON-INTERFERENCE PARITY: PASS | canonical_rows={len(c0)} | d154b_rows={on_n}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
