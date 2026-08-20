#!/usr/bin/env python3
"""Compare two D-143 unified ledgers after removing EDGE_AUDIT_* rows."""
from __future__ import annotations
import csv
import hashlib
from pathlib import Path
import sys


def read_rows(path: Path):
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.reader(f))


def strategy_rows(rows):
    if not rows:
        return []
    out=[rows[0]]
    for row in rows[1:]:
        if len(row)>1 and row[1].startswith('EDGE_AUDIT_'):
            continue
        out.append(row)
    return out


def digest(rows):
    b='\n'.join(','.join(row) for row in rows).encode('utf-8')
    return hashlib.sha256(b).hexdigest()


def main():
    if len(sys.argv)!=3:
        print('Usage: compare_unified_audit_parity.py AUDIT_OFF.csv AUDIT_ON.csv')
        return 2
    a,b=map(Path,sys.argv[1:])
    ra,rb=read_rows(a),read_rows(b)
    sa,sb=strategy_rows(ra),strategy_rows(rb)
    print(f'OFF total rows={len(ra):,} strategy rows={len(sa):,}')
    print(f'ON  total rows={len(rb):,} strategy rows={len(sb):,} audit rows={len(rb)-len(sb):,}')
    print(f'OFF strategy SHA256={digest(sa)}')
    print(f'ON  strategy SHA256={digest(sb)}')
    if sa==sb:
        print(f'PARITY PASS: {len(sa):,} non-audit CSV rows are row-for-row identical.')
        return 0
    print('PARITY FAIL')
    n=min(len(sa),len(sb))
    shown=0
    for i in range(n):
        if sa[i]!=sb[i]:
            print(f'first difference at filtered row {i+1}:')
            print('OFF:',sa[i])
            print('ON :',sb[i])
            shown=1
            break
    if not shown and len(sa)!=len(sb):
        print(f'filtered row count differs: OFF={len(sa)} ON={len(sb)}')
    return 1

if __name__=='__main__':
    raise SystemExit(main())
