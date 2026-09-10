#!/usr/bin/env python3
"""Advance a V9 causal replay to the earliest frozen market event.

This is a thin event runner around v9_causal_m1.py state. It scans the authoritative
source sequentially from the stored byte offset, stops at the first configured event,
and then advances the revealed prefix exactly to that M1 timestamp. Intermediate rows
are runtime-only; they are not emitted to AI before the event.

Supported event kinds:
- PRICE_GE / PRICE_LE / ZONE_TOUCH
- HARD_SL / DESTINATION
- M5_CLOSE_GE / M5_CLOSE_LE / M15_CLOSE_GE / M15_CLOSE_LE / H1_CLOSE_GE / H1_CLOSE_LE

If HARD_SL and DESTINATION both touch in the same M1 row, the runner reports
INTRAMINUTE_EXECUTION_AMBIGUOUS and does not invent tick order.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Same-directory import when run from repository scripts/.
import v9_causal_m1 as causal

CLI_FMT="%Y-%m-%d %H:%M:%S"
TS_FMT="%Y.%m.%d %H:%M:%S"


class EventRunnerError(RuntimeError): pass


def parse_plan(path: Path):
    obj=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj.get("events"),list) or not obj["events"]:
        raise EventRunnerError("plan must contain non-empty events[]")
    return obj


def row_values(line: bytes, header: list[str]):
    p=line.decode("ascii").rstrip("\r\n").split("\t")
    idx={v:i for i,v in enumerate(header)}
    ts=datetime.strptime(p[idx["<DATE>"]]+" "+p[idx["<TIME>"]],TS_FMT)
    return ts,float(p[idx["<OPEN>"]]),float(p[idx["<HIGH>"]]),float(p[idx["<LOW>"]]),float(p[idx["<CLOSE>"]])


def minute_bucket(ts: datetime, minutes: int):
    if minutes==60: return ts.replace(minute=0,second=0,microsecond=0)
    return ts.replace(minute=(ts.minute//minutes)*minutes,second=0,microsecond=0)


def threshold_hit(event, high, low):
    k=event["kind"]
    if k=="PRICE_GE": return high>=float(event["price"])
    if k=="PRICE_LE": return low<=float(event["price"])
    if k=="ZONE_TOUCH": return high>=float(event["low"]) and low<=float(event["high"])
    if k=="HARD_SL":
        return low<=float(event["price"]) if event["side"].upper()=="LONG" else high>=float(event["price"])
    if k=="DESTINATION":
        return high>=float(event["price"]) if event["side"].upper()=="LONG" else low<=float(event["price"])
    return False


def run(source: Path,revealed: Path,state_path: Path,plan_path: Path,expected_sha: str):
    state=causal.load_state(state_path)
    causal.verify_source(source,expected_sha)
    if causal.sha256_file(revealed)!=state["revealed_sha256"]:
        raise EventRunnerError("revealed prefix hash differs from state")
    old_cutoff=causal.parse_cli_ts(state["cutoff"])
    plan=parse_plan(plan_path)
    events=plan["events"]
    # Per-event completed-bar accumulator. A close event is evaluated from the
    # previous revealed M1 row when the next bucket timestamp is observed. The
    # next row's OHLC is NOT parsed before that decision.
    acc={}
    found=None
    with source.open("rb") as src:
        header=causal.parse_header(src.readline())
        src.seek(int(state["resume_offset"]))
        while True:
            line=src.readline()
            if not line: break
            ts=causal.parse_row_ts(line)  # timestamp-only chronology check
            if ts<=old_cutoff: raise EventRunnerError("source offset chronology mismatch")

            # A new bucket timestamp proves the previous bucket completed.
            # Evaluate its frozen close condition before exposing current-row OHLC.
            for ev in events:
                k=ev["kind"]
                if "_CLOSE_" not in k: continue
                tf=k.split("_",1)[0]; minutes={"M5":5,"M15":15,"H1":60}.get(tf)
                if minutes is None: raise EventRunnerError(f"unsupported bar-close event: {k}")
                key=ev.get("id",k); b=minute_bucket(ts,minutes)
                prev=acc.get(key)
                if prev is not None and prev["bucket"]!=b:
                    close=prev["close"]; price=float(ev["price"])
                    hit=(k.endswith("GE") and close>=price) or (k.endswith("LE") and close<=price)
                    if hit:
                        found={"event":k,"event_id":ev.get("id"),
                               "timestamp":prev["last_ts"].strftime(CLI_FMT),
                               "completed_bucket_start":prev["bucket"].strftime(CLI_FMT),
                               "completed_close":close}
                        break
            if found: break

            # Only now is current-row OHLC exposed to the runtime event logic.
            ts2,o,h,l,c=row_values(line,header)
            if ts2!=ts: raise EventRunnerError("timestamp parse mismatch")
            instant=[]
            for ev in events:
                if threshold_hit(ev,h,l): instant.append(ev)
            sl=[e for e in instant if e["kind"]=="HARD_SL"]
            tp=[e for e in instant if e["kind"]=="DESTINATION"]
            if sl and tp:
                found={"event":"INTRAMINUTE_EXECUTION_AMBIGUOUS","timestamp":ts.strftime(CLI_FMT),
                       "event_ids":[e.get("id") for e in sl+tp],
                       "row":{"open":o,"high":h,"low":l,"close":c}}
                break
            if instant:
                e=instant[0]
                found={"event":e["kind"],"event_id":e.get("id"),"timestamp":ts.strftime(CLI_FMT),
                       "row":{"open":o,"high":h,"low":l,"close":c}}
                break

            # Update completed-bar accumulators after instant guards.
            for ev in events:
                k=ev["kind"]
                if "_CLOSE_" not in k: continue
                tf=k.split("_",1)[0]; minutes={"M5":5,"M15":15,"H1":60}[tf]
                key=ev.get("id",k); b=minute_bucket(ts,minutes)
                prev=acc.get(key)
                if prev is None or prev["bucket"]!=b:
                    acc[key]={"bucket":b,"close":c,"last_ts":ts}
                else:
                    prev["close"]=c; prev["last_ts"]=ts
    if found is None: raise EventRunnerError("no configured event found before EOF")
    event_ts=datetime.strptime(found["timestamp"],CLI_FMT)
    causal.advance_revealed(source,revealed,state_path,event_ts,expected_sha)
    found["revealed_advanced_to"]=event_ts.strftime(CLI_FMT)
    return found


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--revealed",type=Path,required=True)
    p.add_argument("--state",type=Path,required=True)
    p.add_argument("--plan",type=Path,required=True)
    p.add_argument("--expected-sha256",default=causal.AUTHORITATIVE_SHA256)
    a=p.parse_args(argv)
    try:
        result=run(a.source,a.revealed,a.state,a.plan,a.expected_sha256)
        print(json.dumps(result,indent=2)); return 0
    except Exception as exc:
        print(f"ERROR: {exc}",file=sys.stderr); return 2


if __name__=="__main__": raise SystemExit(main())
