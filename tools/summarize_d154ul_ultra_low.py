#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,json,zipfile
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("master_zip",type=Path)
    a=ap.parse_args()
    with zipfile.ZipFile(a.master_zip) as z:
        names=set(z.namelist())
        target="comparison/standard_vs_ultra_low.csv"
        if target not in names:
            raise SystemExit("comparison CSV missing")
        rows=list(csv.DictReader(io.StringIO(z.read(target).decode("utf-8"))))
    for r in rows:
        print(
            f"{r['symbol']}: fills {r['standard_fills']}->{r['ultra_fills']} | "
            f"actual WR {100*float(r['standard_actual_survival']):.2f}%"
            f"->{100*float(r['ultra_actual_survival']):.2f}% "
            f"({float(r['actual_survival_delta_pp']):+.2f}pp) | "
            f"spread/TR {float(r['standard_spread_over_reaction_tr']):.4f}"
            f"->{float(r['ultra_spread_over_reaction_tr']):.4f} | "
            f"M flips {r['standard_sl_to_shadow_plus1']}->{r['ultra_sl_to_shadow_plus1']}"
        )
    print("\nDo not infer a strategy rule from this environment comparison alone.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
