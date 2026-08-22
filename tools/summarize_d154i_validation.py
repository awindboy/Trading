#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path


CELLS = ("GOLD24", "GOLD25", "BTC25", "SILVER25", "CADJPY25")


def kv(detail: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in re.finditer(r"(\w+)=([^ ]+)", detail or "")}


def read_csv_from_nested(master: zipfile.ZipFile, cell: str) -> list[dict[str, str]]:
    nested_names = [n for n in master.namelist() if n.startswith(cell + "/") and n.endswith(".zip")]
    if len(nested_names) != 1:
        raise RuntimeError(f"{cell}: expected exactly one nested ZIP, found {len(nested_names)}")
    nested_bytes = master.read(nested_names[0])
    with zipfile.ZipFile(io.BytesIO(nested_bytes)) as z:
        csv_names = [n for n in z.namelist() if n.endswith(".csv")]
        if len(csv_names) != 1:
            raise RuntimeError(f"{cell}: expected exactly one CSV, found {len(csv_names)}")
        text = z.read(csv_names[0]).decode("utf-8-sig", errors="replace")
        return list(csv.DictReader(io.StringIO(text)))


def resolved_rate(a: list[int]) -> str:
    w, l, c = a
    n = w + l
    return f"{w}/{n} = {100.0*w/n:.1f}%" if n else "NA"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("master_zip", type=Path)
    args = ap.parse_args()

    overall = {"EXPOSED": [0, 0, 0], "CLEAN": [0, 0, 0]}
    secondary = {"TRANSITION": [0, 0, 0], "OTHER": [0, 0, 0]}

    with zipfile.ZipFile(args.master_zip) as master:
        for cell in CELLS:
            rows = read_csv_from_nested(master, cell)
            events = []
            stages = defaultdict(dict)
            outcomes = {}
            fills = {}

            for r in rows:
                ev = r.get("event", "")
                d = kv(r.get("detail", ""))

                if ev == "D154H_HTF_EVENT":
                    d["seq_i"] = int(d["seq"])
                    events.append(d)
                elif ev == "D154H_STAGE_SNAPSHOT":
                    sid = d.get("scenario_id", "")
                    stage = d.get("stage", "")
                    if sid and stage:
                        stages[sid][stage] = d
                elif ev == "D154H_FILL_REPLAY_ANCHOR":
                    sid = d.get("scenario_id", "")
                    if sid:
                        fills[sid] = d
                elif ev == "D154H_PRIMARY_OUTCOME":
                    sid = d.get("scenario_id", "")
                    if sid:
                        outcomes[sid] = d.get("outcome", "")

            cell_primary = {"EXPOSED": [0, 0, 0], "CLEAN": [0, 0, 0]}
            cell_secondary = {"TRANSITION": [0, 0, 0], "OTHER": [0, 0, 0]}

            for sid, fill in fills.items():
                if sid not in stages or "ROOT_CONTACT" not in stages[sid] or "CHOCH" not in stages[sid]:
                    raise RuntimeError(f"{cell}: missing ROOT_CONTACT/CHOCH anchor for {sid}")

                direction = fill.get("direction", "")
                s0 = int(stages[sid]["ROOT_CONTACT"]["seq_at_stage"])
                s1 = int(stages[sid]["CHOCH"]["seq_at_stage"])

                exposed = False
                for e in events:
                    if not (s0 < e["seq_i"] <= s1):
                        continue
                    if e.get("event_tf") not in ("H1", "M30"):
                        continue
                    if e.get("event_type") != "BOS":
                        continue
                    if e.get("event_direction") != direction:
                        continue
                    exposed = True
                    break

                outcome = outcomes.get(sid, "RIGHT_CENSORED")
                bucket = "EXPOSED" if exposed else "CLEAN"
                if outcome == "PLUS_1R":
                    cell_primary[bucket][0] += 1
                    overall[bucket][0] += 1
                elif outcome == "SL_FIRST":
                    cell_primary[bucket][1] += 1
                    overall[bucket][1] += 1
                else:
                    cell_primary[bucket][2] += 1
                    overall[bucket][2] += 1

                sweep_rel = stages[sid].get("SWEEP", {}).get("nested_relation_now", "")
                sb = "TRANSITION" if sweep_rel == "H1_PRIMARY_M30_TRANSITION" else "OTHER"
                if outcome == "PLUS_1R":
                    cell_secondary[sb][0] += 1
                    secondary[sb][0] += 1
                elif outcome == "SL_FIRST":
                    cell_secondary[sb][1] += 1
                    secondary[sb][1] += 1
                else:
                    cell_secondary[sb][2] += 1
                    secondary[sb][2] += 1

            print(f"\n[{cell}]")
            print("PRIMARY  POST_CONTACT_SAME_DIR_HTF_BOS:", resolved_rate(cell_primary["EXPOSED"]),
                  "| NO_SUCH_BOS:", resolved_rate(cell_primary["CLEAN"]),
                  f"| censored={cell_primary['EXPOSED'][2]}/{cell_primary['CLEAN'][2]}")
            print("SECONDARY H1_PRIMARY_M30_TRANSITION_AT_SWEEP:", resolved_rate(cell_secondary["TRANSITION"]),
                  "| OTHER:", resolved_rate(cell_secondary["OTHER"]))

    print("\n[POOLED VALIDATION]")
    print("PRIMARY  POST_CONTACT_SAME_DIR_HTF_BOS:", resolved_rate(overall["EXPOSED"]),
          "| NO_SUCH_BOS:", resolved_rate(overall["CLEAN"]),
          f"| censored={overall['EXPOSED'][2]}/{overall['CLEAN'][2]}")
    print("SECONDARY H1_PRIMARY_M30_TRANSITION_AT_SWEEP:", resolved_rate(secondary["TRANSITION"]),
          "| OTHER:", resolved_rate(secondary["OTHER"]))
    print("\nNo threshold fitting, market exceptions, H1/M30 split, or combined-rule rescue is performed by this script.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
