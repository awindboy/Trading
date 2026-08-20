#!/usr/bin/env python3
"""Compare D-142A audit-OFF and audit-ON *main* event CSVs.

The edge-audit CSV is intentionally not compared here. For the first parity
fixture the main strategy event ledger should be row-for-row identical.

Usage:
    python tools/compare_edge_audit_parity.py off_main.csv on_main.csv
"""
from __future__ import annotations
import csv
import hashlib
from pathlib import Path
import sys


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def rows(path: Path):
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        yield from csv.reader(f)


def main() -> int:
    if len(sys.argv)!=3:
        print('Usage: compare_edge_audit_parity.py OFF_MAIN.csv ON_MAIN.csv', file=sys.stderr)
        return 2
    a,b=map(Path,sys.argv[1:])
    for p in (a,b):
        if not p.exists():
            print(f'ERROR: not found: {p}', file=sys.stderr)
            return 2

    print(f'OFF SHA-256: {sha256(a)}')
    print(f'ON  SHA-256: {sha256(b)}')

    ita,itb=rows(a),rows(b)
    line=0
    diffs=0
    first=[]
    count_a=count_b=0
    while True:
        try:
            ra=next(ita); enda=False; count_a+=1
        except StopIteration:
            ra=None; enda=True
        try:
            rb=next(itb); endb=False; count_b+=1
        except StopIteration:
            rb=None; endb=True
        if enda and endb:
            break
        line+=1
        if ra!=rb:
            diffs+=1
            if len(first)<20:
                first.append((line,ra,rb))
        if enda or endb:
            # Drain only to get final row count.
            if enda and not endb:
                for _ in itb: count_b+=1
            if endb and not enda:
                for _ in ita: count_a+=1
            break

    if diffs==0 and count_a==count_b:
        print(f'PARITY PASS: {count_a} CSV rows are row-for-row identical.')
        return 0

    print(f'PARITY FAIL: OFF rows={count_a}, ON rows={count_b}, differing positions={diffs}')
    for n,ra,rb in first:
        print(f'\n--- first difference at CSV row position {n} ---')
        print('OFF:', ra)
        print('ON :', rb)
    return 1

if __name__=='__main__':
    raise SystemExit(main())
