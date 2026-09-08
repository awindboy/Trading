#!/usr/bin/env python3
"""Fail-closed hard-stop touch detector for an already-revealed V9 M1 prefix.

This tool never opens the authoritative full source. It only scans the causal
`revealed.tsv` prefix that has already been exposed by v9_causal_m1.py.

For a LONG, the first row whose LOW <= stop is the stop-touch row.
For a SHORT, the first row whose HIGH >= stop is the stop-touch row.

The reported `descriptive_stop_reference` is the precommitted stop price. 2025
M1 cannot establish exact broker fill, spread, slippage, or within-minute path.
"""
from __future__ import annotations
import argparse, csv, json, sys
from datetime import datetime
from pathlib import Path

HEADER = ["<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>", "<TICKVOL>", "<VOL>", "<SPREAD>"]
TS_FMT = "%Y.%m.%d %H:%M:%S"
CLI_FMT = "%Y-%m-%d %H:%M:%S"

class GuardError(RuntimeError): pass

def cli_ts(s: str) -> datetime:
    try: return datetime.strptime(s, CLI_FMT)
    except ValueError as e: raise argparse.ArgumentTypeError(f"timestamp must be YYYY-MM-DD HH:MM:SS: {s}") from e

def scan(path: Path, side: str, stop: float, active_after: datetime, through: datetime|None=None) -> dict:
    if not path.is_file(): raise GuardError(f"revealed file missing: {path}")
    side=side.upper()
    if side not in {"LONG","SHORT"}: raise GuardError("side must be LONG or SHORT")
    last=None
    with path.open('r',encoding='utf-8-sig',newline='') as f:
        r=csv.reader(f,delimiter='	')
        try: header=next(r)
        except StopIteration: raise GuardError('revealed file is empty')
        if header!=HEADER: raise GuardError(f'unexpected header: {header!r}')
        prev=None
        for row in r:
            if len(row)!=len(HEADER): raise GuardError('malformed revealed row')
            ts=datetime.strptime(row[0]+' '+row[1],TS_FMT)
            if prev is not None and ts<=prev: raise GuardError('revealed rows are not strictly chronological')
            prev=ts; last=ts
            if ts<=active_after: continue
            if through is not None and ts>through: break
            o,h,l,c=map(float,row[2:6])
            hit = (l<=stop) if side=='LONG' else (h>=stop)
            if hit:
                return {
                    'stop_touched': True,
                    'side': side,
                    'stop': stop,
                    'active_after': active_after.strftime(CLI_FMT),
                    'through': through.strftime(CLI_FMT) if through else None,
                    'touch_timestamp': ts.strftime(CLI_FMT),
                    'touch_row': {'open':o,'high':h,'low':l,'close':c},
                    'descriptive_stop_reference': stop,
                    'execution_caveat': 'M1 touch is causal price evidence, not exact Bid/Ask/slippage fill authority.'
                }
    if last is None: raise GuardError('revealed file contains no data rows')
    if through is not None and last < through:
        raise GuardError(f'revealed prefix ends at {last.strftime(CLI_FMT)}, before requested through {through.strftime(CLI_FMT)}')
    return {
        'stop_touched': False,'side':side,'stop':stop,
        'active_after':active_after.strftime(CLI_FMT),
        'through':through.strftime(CLI_FMT) if through else None,
        'revealed_last':last.strftime(CLI_FMT),
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True,help='already-revealed M1 TSV prefix only')
    p.add_argument('--side',choices=['LONG','SHORT','long','short'],required=True)
    p.add_argument('--stop',type=float,required=True)
    p.add_argument('--active-after',type=cli_ts,required=True,help='stop becomes active strictly after this decision/entry timestamp')
    p.add_argument('--through',type=cli_ts,help='optional exact review cutoff; must already exist in revealed prefix')
    a=p.parse_args(argv)
    try:
        print(json.dumps(scan(a.input,a.side,a.stop,a.active_after,a.through),indent=2))
        return 0
    except GuardError as e:
        print(f'ERROR: {e}',file=sys.stderr); return 2
if __name__=='__main__': raise SystemExit(main())
