#!/usr/bin/env python3
"""Render the V9 two-chart research packet from a revealed prefix and selected ICT objects.

The packet has exactly two chart roles:
- MAP: H1 by default, showing AI-selected H4/H1 objects and large route.
- TRIGGER: M5 by default, shown only around an active POI/entry/review event.

The renderer owns coordinates and object lifetimes. AI owns which object IDs are selected
and what concise semantic notes are supplied in the selection JSON.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

TS_FMT = "%Y.%m.%d %H:%M:%S"
CLI_FMT = "%Y-%m-%d %H:%M:%S"
HEADER = [
    "<DATE>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>",
    "<TICKVOL>", "<VOL>", "<SPREAD>",
]


def parse_ts(s: str) -> datetime:
    return datetime.strptime(s, CLI_FMT)


def load_rows(path: Path):
    out=[]
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        r=csv.reader(f,delimiter="\t")
        header=next(r)
        if header!=HEADER: raise RuntimeError(f"unexpected header: {header!r}")
        for row in r:
            ts=datetime.strptime(row[0]+" "+row[1],TS_FMT)
            o,h,l,c=map(float,row[2:6])
            out.append((ts,o,h,l,c))
    if not out: raise RuntimeError("no revealed rows")
    return out, out[-1][0]


def aggregate(rows, minutes, cutoff):
    def bucket(ts):
        if minutes<60:
            return ts.replace(minute=(ts.minute//minutes)*minutes,second=0,microsecond=0)
        if minutes==60:
            return ts.replace(minute=0,second=0,microsecond=0)
        if minutes==240:
            return ts.replace(hour=(ts.hour//4)*4,minute=0,second=0,microsecond=0)
        raise ValueError(minutes)
    out=[]; cur=None
    for ts,o,h,l,c in rows:
        b=bucket(ts)
        if cur is None or cur[0]!=b:
            if cur is not None: out.append(cur)
            cur=[b,o,h,l,c]
        else:
            cur[2]=max(cur[2],h); cur[3]=min(cur[3],l); cur[4]=c
    if cur is not None: out.append(cur)
    # Draw partial last bar too: it is still revealed price, but notes must state if used.
    return out


def load_objects(path: Path):
    with path.open("r",encoding="utf-8",newline="") as f:
        return {row["object_id"]:row for row in csv.DictReader(f)}


def f(v):
    return None if v in (None,"", "None") else float(v)


def dt(v):
    return None if v in (None,"", "None") else parse_ts(v)


def draw_candles(ax,bars,width):
    xs=[mdates.date2num(x[0]) for x in bars]
    ax.vlines(xs,[x[3] for x in bars],[x[2] for x in bars],linewidth=.75)
    for xi,(_,o,h,l,c) in zip(xs,bars):
        low=min(o,c); body=max(abs(c-o),.0001)
        ax.add_patch(Rectangle((xi-width/2,low),width,body,fill=(c<o),linewidth=.68))


def object_end(o, cutoff):
    end=dt(o.get("geometric_end_at"))
    if end is None or end>cutoff: return cutoff
    return end


def draw_object(ax,o,cutoff,label=None):
    born=dt(o["born_at"]); end=object_end(o,cutoff)
    if born is None or end<born: return
    lo=f(o["price_low"]); hi=f(o["price_high"])
    family=o["family"]
    text=label or o["object_id"]
    xs=mdates.date2num(born); xe=mdates.date2num(end)
    if family in {"FVG","OB"}:
        ax.add_patch(Rectangle((xs,lo),xe-xs,hi-lo,fill=False,linewidth=1.35,
                               linestyle="--" if family=="OB" else ":"))
        y=(lo+hi)/2
        if family=="OB":
            source=dt(o.get("source_start"))
            if source is not None:
                ax.scatter([mdates.date2num(source)],[y],s=25)
    elif family=="LIQUIDITY":
        y=lo
        ax.plot([xs,xe],[y,y],linestyle="--",linewidth=1.3)
        source=dt(o.get("source_start"))
        if source is not None: ax.scatter([mdates.date2num(source)],[y],s=22)
    else:
        return
    ax.text(xe,y,"  "+text,va="center",fontsize=8.0,
            bbox={"boxstyle":"round,pad=0.14","alpha":.9})


def draw_notes(ax, notes):
    for n in notes:
        t=parse_ts(n["time"]); p=float(n["price"])
        offset=n.get("offset",[-140,50])
        ax.annotate(n["text"],xy=(mdates.date2num(t),p),xytext=tuple(offset),
                    textcoords="offset points",arrowprops={"arrowstyle":"->"},
                    bbox={"boxstyle":"round,pad=.3","alpha":.94},fontsize=8.2)


def render_role(rows,cutoff,objects,spec,output):
    tf=spec.get("timeframe","H1").upper()
    minutes={"M5":5,"M15":15,"H1":60,"H4":240}[tf]
    days=float(spec.get("lookback_days",15 if tf=="H1" else 1.5))
    bars=aggregate(rows,minutes,cutoff)
    start=cutoff-timedelta(days=days)
    bars=[b for b in bars if b[0]>=start]
    width={"M5":.0028,"M15":.008,"H1":.03,"H4":.13}[tf]
    fig,ax=plt.subplots(figsize=(18,8))
    draw_candles(ax,bars,width)
    for item in spec.get("objects",[]):
        oid=item["id"] if isinstance(item,dict) else item
        if oid not in objects: raise RuntimeError(f"selected object not in ledger: {oid}")
        label=item.get("label") if isinstance(item,dict) else None
        draw_object(ax,objects[oid],cutoff,label)
    for level in spec.get("levels",[]):
        price=float(level["price"]); ax.axhline(price,linestyle=level.get("linestyle","--"),linewidth=1.25)
        ax.text(mdates.date2num(cutoff),price,"  "+level["label"],va="center",fontsize=8.0,
                bbox={"boxstyle":"round,pad=0.14","alpha":.9})
    draw_notes(ax,spec.get("notes",[]))
    ax.set_title(spec.get("title",f"{tf} {spec.get('role','chart')} | {cutoff.strftime(CLI_FMT)}"))
    ax.set_ylabel("GOLD#")
    if tf in {"H1","H4"}:
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=2 if tf=="H1" else 5))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    else:
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    ax.grid(alpha=.22)
    plt.setp(ax.get_xticklabels(),rotation=45,ha="right")
    fig.tight_layout(); fig.savefig(output,dpi=180,bbox_inches="tight"); plt.close(fig)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,required=True,help="already-revealed M1 TSV prefix")
    p.add_argument("--objects",type=Path,required=True,help="ict_candidate_universe.csv")
    p.add_argument("--selection",type=Path,required=True,help="AI-selected packet JSON")
    p.add_argument("--out-dir",type=Path,required=True)
    a=p.parse_args(argv)
    rows,cutoff=load_rows(a.input); objects=load_objects(a.objects)
    spec=json.loads(a.selection.read_text(encoding="utf-8"))
    a.out_dir.mkdir(parents=True,exist_ok=True)
    render_role(rows,cutoff,objects,spec["map"],a.out_dir/"MAP.png")
    render_role(rows,cutoff,objects,spec["trigger"],a.out_dir/"TRIGGER.png")
    manifest={"cutoff":cutoff.strftime(CLI_FMT),"selection":str(a.selection),
              "map":str(a.out_dir/"MAP.png"),"trigger":str(a.out_dir/"TRIGGER.png")}
    (a.out_dir/"chart_packet_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(manifest,indent=2)); return 0


if __name__=="__main__": raise SystemExit(main())
