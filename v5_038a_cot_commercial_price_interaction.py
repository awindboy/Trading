#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import re
import statistics
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

CFTC_DATASET = "6dca-aqww"          # official CFTC Legacy - Futures Only
CFTC_GOLD_CODE = "088691"           # GOLD - COMMODITY EXCHANGE INC.
API_BASE = f"https://publicreporting.cftc.gov/resource/{CFTC_DATASET}.json"
ARCHIVE_BASE = "https://www.cftc.gov/files/dea/cotarchives"
USER_AGENT = "awindboy-Trading-V5-research/1.0 (CFTC public-data research)"

DISCOVERY_START = date(2023, 1, 1)
DISCOVERY_END = date(2023, 12, 31)

# Outcome-independent operational freshness rule.
# Normal COT: Tuesday report -> Friday publication (3 calendar days);
# federal holidays can delay by 1-2 business days. A lag >6 calendar days
# is therefore treated as extraordinary operational delay/staleness.
MAX_PRIMARY_RELEASE_LAG_DAYS = 6

# A broker day is "complete" if its first-to-last minute span is at least this.
# GOLD# full days in the frozen development data span ~1437m normally and
# ~1377m across DST/server-session shifts. This threshold was frozen in prior
# V5-037A scratch and is not fit to COT outcomes.
FULL_DAY_MIN_SPAN_MINUTES = 1377

@dataclass
class CotRow:
    report_date: date
    market_name: str
    comm_long: int
    comm_short: int
    comm_net: int
    release_date: date | None = None
    release_lag_days: int | None = None
    archive_url: str = ""

@dataclass
class DayBar:
    d: date
    o: float
    h: float
    l: float
    c: float
    first_ts: datetime
    last_ts: datetime
    n: int
    complete: bool

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def fetch_text(url: str, timeout: int = 45, retries: int = 4) -> str:
    last = None
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json,text/html,*/*"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
            return raw.decode("utf-8", errors="replace")
        except Exception as e:
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"fetch failed after {retries} attempts: {url}\n{last}")

def parse_date_any(s: str) -> date:
    s = s.strip()
    if "T" in s:
        s = s.split("T", 1)[0]
    for fmt in ("%Y-%m-%d", "%Y.%m.%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"unsupported date: {s}")

def get_cot_rows(cache_path: Path | None = None) -> tuple[list[CotRow], str]:
    if cache_path and cache_path.exists():
        text = cache_path.read_text(encoding="utf-8")
        source = str(cache_path)
    else:
        where = (
            f"cftc_contract_market_code='{CFTC_GOLD_CODE}' "
            "AND report_date_as_yyyy_mm_dd >= '2022-12-01T00:00:00' "
            "AND report_date_as_yyyy_mm_dd <= '2024-01-15T00:00:00'"
        )
        q = {
            "$select": ",".join([
                "market_and_exchange_names",
                "report_date_as_yyyy_mm_dd",
                "cftc_contract_market_code",
                "comm_positions_long_all",
                "comm_positions_short_all",
            ]),
            "$where": where,
            "$order": "report_date_as_yyyy_mm_dd ASC",
            "$limit": "200",
        }
        url = API_BASE + "?" + urllib.parse.urlencode(q)
        text = fetch_text(url)
        source = url
        if cache_path:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(text, encoding="utf-8")
    raw = json.loads(text)
    by_date: dict[date, CotRow] = {}
    for r in raw:
        d = parse_date_any(r["report_date_as_yyyy_mm_dd"])
        row = CotRow(
            report_date=d,
            market_name=str(r.get("market_and_exchange_names", "")),
            comm_long=int(float(r["comm_positions_long_all"])),
            comm_short=int(float(r["comm_positions_short_all"])),
            comm_net=int(float(r["comm_positions_long_all"])) - int(float(r["comm_positions_short_all"])),
        )
        # Dataset occasionally has duplicate rows. Fail if duplicates disagree.
        if d in by_date:
            old = by_date[d]
            if (old.comm_long, old.comm_short) != (row.comm_long, row.comm_short):
                raise RuntimeError(f"conflicting CFTC duplicate on {d}: {old} vs {row}")
        else:
            by_date[d] = row
    rows = sorted(by_date.values(), key=lambda x: x.report_date)
    if len(rows) < 45:
        raise RuntimeError(f"unexpectedly few CFTC GOLD rows: {len(rows)}")
    return rows, source

MONTHS = {
    "January":1, "February":2, "March":3, "April":4, "May":5, "June":6,
    "July":7, "August":8, "September":9, "October":10, "November":11, "December":12
}

def archive_url_for(d: date) -> str:
    return f"{ARCHIVE_BASE}/{d.year}/futures/deacmxlf{d:%m%d%y}.htm"

def parse_updated_date(page: str) -> date:
    txt = html.unescape(re.sub(r"<[^>]+>", " ", page))
    txt = re.sub(r"\s+", " ", txt)
    m = re.search(
        r"Updated\s+(January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+(\d{1,2}),\s+(\d{4})",
        txt,
        flags=re.I,
    )
    if not m:
        raise ValueError("Updated date not found")
    month_name = m.group(1).capitalize()
    return date(int(m.group(3)), MONTHS[month_name], int(m.group(2)))

def attach_release_dates(rows: list[CotRow], release_cache: Path) -> None:
    cache: dict[str, str] = {}
    if release_cache.exists():
        cache = json.loads(release_cache.read_text(encoding="utf-8"))
    changed = False
    for row in rows:
        key = row.report_date.isoformat()
        row.archive_url = archive_url_for(row.report_date)
        if key in cache:
            row.release_date = date.fromisoformat(cache[key])
        else:
            page = fetch_text(row.archive_url)
            rd = parse_updated_date(page)
            cache[key] = rd.isoformat()
            row.release_date = rd
            changed = True
            time.sleep(0.15)
        row.release_lag_days = (row.release_date - row.report_date).days
        if row.release_lag_days < 0:
            raise RuntimeError(f"release before report date: {row}")
    if changed or not release_cache.exists():
        release_cache.parent.mkdir(parents=True, exist_ok=True)
        release_cache.write_text(json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8")

def load_gold_days(path: Path) -> tuple[list[DayBar], dict[date, DayBar]]:
    agg: dict[date, dict] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        required = {"<DATE>","<TIME>","<OPEN>","<HIGH>","<LOW>","<CLOSE>"}
        if not required.issubset(reader.fieldnames or []):
            raise RuntimeError(f"GOLD file missing columns: {required - set(reader.fieldnames or [])}")
        for r in reader:
            d = datetime.strptime(r["<DATE>"], "%Y.%m.%d").date()
            ts = datetime.strptime(r["<DATE>"]+" "+r["<TIME>"], "%Y.%m.%d %H:%M:%S")
            o,h,l,c = (float(r["<OPEN>"]),float(r["<HIGH>"]),float(r["<LOW>"]),float(r["<CLOSE>"]))
            if d not in agg:
                agg[d] = dict(o=o,h=h,l=l,c=c,first=ts,last=ts,n=1)
            else:
                a=agg[d]
                a["h"]=max(a["h"],h); a["l"]=min(a["l"],l); a["c"]=c
                a["last"]=ts; a["n"]+=1
    days=[]
    for d,a in sorted(agg.items()):
        span=(a["last"]-a["first"]).total_seconds()/60.0
        complete = span >= FULL_DAY_MIN_SPAN_MINUTES
        days.append(DayBar(d,a["o"],a["h"],a["l"],a["c"],a["first"],a["last"],a["n"],complete))
    return days, {x.d:x for x in days}

def sign(x: float, eps: float=1e-12) -> int:
    if x > eps: return 1
    if x < -eps: return -1
    return 0

def med(xs):
    return statistics.median(xs) if xs else None

def mean(xs):
    return statistics.fmean(xs) if xs else None

def summarize(records: list[dict], label: str) -> dict:
    sc=[r["signed_close_r"] for r in records]
    adv=[r["excursion_advantage_r"] for r in records]
    pm=[r["pressure_mfe_r"] for r in records]
    om=[r["opposite_mfe_r"] for r in records]
    return {
        "label": label,
        "n": len(records),
        "mean_signed_close_r": mean(sc),
        "median_signed_close_r": med(sc),
        "mean_excursion_advantage_r": mean(adv),
        "median_excursion_advantage_r": med(adv),
        "median_pressure_mfe_r": med(pm),
        "median_opposite_mfe_r": med(om),
    }

def metric_for_window(direction:int, window:list[DayBar], scale:float) -> dict:
    o=window[0].o
    c=window[-1].c
    hi=max(x.h for x in window)
    lo=min(x.l for x in window)
    if direction>0:
        fav=(hi-o)/scale
        opp=(o-lo)/scale
    else:
        fav=(o-lo)/scale
        opp=(hi-o)/scale
    return {
        "signed_close_r": direction*(c-o)/scale,
        "pressure_mfe_r": fav,
        "opposite_mfe_r": opp,
        "excursion_advantage_r": fav-opp,
    }

def previous_complete_days(days:list[DayBar], before:date, n:int=5) -> list[DayBar]:
    xs=[x for x in days if x.complete and x.d < before]
    return xs[-n:]

def outcome_window(days:list[DayBar], release_date:date, next_release_date:date|None) -> list[DayBar]:
    # First complete broker day strictly after release. Stop before the next release date.
    xs=[x for x in days if x.complete and x.d > release_date and (next_release_date is None or x.d < next_release_date)]
    return xs

def evaluate(rows:list[CotRow], days:list[DayBar], by_day:dict[date,DayBar]) -> tuple[list[dict], list[dict]]:
    all_weeks=[]
    primary=[]
    # Rows include late 2022 for prior delta; evaluate current report rows in 2023 only.
    for i in range(1,len(rows)):
        cur=rows[i]; prev=rows[i-1]
        if not (DISCOVERY_START <= cur.report_date <= DISCOVERY_END):
            continue
        if cur.release_date is None:
            continue
        next_release = rows[i+1].release_date if i+1 < len(rows) else None

        # Need exact report-date GOLD broker closes for price interaction.
        if cur.report_date not in by_day or prev.report_date not in by_day:
            continue
        price_change = by_day[cur.report_date].c - by_day[prev.report_date].c
        price_sign=sign(price_change)
        comm_delta=cur.comm_net-prev.comm_net
        comm_sign=sign(comm_delta)
        if price_sign==0:
            continue

        window=outcome_window(days,cur.release_date,next_release)
        if not window:
            continue
        prior=previous_complete_days(days,window[0].d,5)
        if len(prior)<5:
            continue
        scale=max(x.h for x in prior)-min(x.l for x in prior)
        if not math.isfinite(scale) or scale<=0:
            continue

        fade_direction=-price_sign
        m=metric_for_window(fade_direction,window,scale)
        rec={
            "report_date":cur.report_date.isoformat(),
            "release_date":cur.release_date.isoformat(),
            "release_lag_days":cur.release_lag_days,
            "operationally_fresh":cur.release_lag_days <= MAX_PRIMARY_RELEASE_LAG_DAYS,
            "window_start":window[0].d.isoformat(),
            "window_end":window[-1].d.isoformat(),
            "window_days":len(window),
            "prev_report_date":prev.report_date.isoformat(),
            "report_price_change":price_change,
            "report_price_sign":price_sign,
            "comm_long":cur.comm_long,
            "comm_short":cur.comm_short,
            "comm_net":cur.comm_net,
            "delta_comm_net":comm_delta,
            "delta_comm_sign":comm_sign,
            "commercial_price_divergence": (comm_sign == -price_sign and comm_sign != 0),
            "fade_direction":"LONG" if fade_direction>0 else "SHORT",
            "scale_prior5_range":scale,
            **m,
        }
        all_weeks.append(rec)
        if rec["operationally_fresh"] and rec["commercial_price_divergence"]:
            primary.append(rec)
    return all_weeks, primary

def stale_control(all_weeks:list[dict]) -> list[dict]:
    # Causal placebo: current report-price sign + PREVIOUS report's commercial-net delta sign.
    out=[]
    for i in range(1,len(all_weeks)):
        cur=all_weeks[i]; prev=all_weeks[i-1]
        if not cur["operationally_fresh"]:
            continue
        if prev["delta_comm_sign"] == -cur["report_price_sign"] and prev["delta_comm_sign"] != 0:
            out.append(cur)
    return out

def group_summary(records:list[dict]) -> dict:
    return {
        "pooled": summarize(records,"pooled"),
        "H1": summarize([r for r in records if r["window_start"] <= "2023-06-30"],"H1"),
        "H2": summarize([r for r in records if r["window_start"] >= "2023-07-01"],"H2"),
        "LONG": summarize([r for r in records if r["fade_direction"]=="LONG"],"LONG"),
        "SHORT": summarize([r for r in records if r["fade_direction"]=="SHORT"],"SHORT"),
    }

def classify(primary:list[dict], nondiv:list[dict], stale:list[dict]) -> tuple[str,list[str]]:
    reasons=[]
    ps=summarize(primary,"primary")
    h1=summarize([r for r in primary if r["window_start"] <= "2023-06-30"],"H1")
    h2=summarize([r for r in primary if r["window_start"] >= "2023-07-01"],"H2")
    nd=summarize(nondiv,"nondiv")
    st=summarize(stale,"stale")

    def req(cond,msg):
        if not cond: reasons.append(msg)
    req(ps["n"]>=15, "primary N < 15")
    req(ps["median_signed_close_r"] is not None and ps["median_signed_close_r"]>0, "pooled median signed close <= 0")
    req(ps["median_excursion_advantage_r"] is not None and ps["median_excursion_advantage_r"]>0, "pooled median excursion advantage <= 0")
    req(h1["n"]>=5 and h1["median_signed_close_r"]>0 and h1["median_excursion_advantage_r"]>0,
        "H1 breadth gate failed")
    req(h2["n"]>=5 and h2["median_signed_close_r"]>0 and h2["median_excursion_advantage_r"]>0,
        "H2 breadth gate failed")
    if nd["n"]>=5:
        req(ps["median_signed_close_r"]>nd["median_signed_close_r"],
            "commercial divergence did not beat simple weekly fade on median close")
        req(ps["median_excursion_advantage_r"]>nd["median_excursion_advantage_r"],
            "commercial divergence did not beat simple weekly fade on median excursion advantage")
    if st["n"]>=5:
        req(ps["median_signed_close_r"]>st["median_signed_close_r"],
            "fresh commercial interaction did not beat stale-COT placebo on median close")
        req(ps["median_excursion_advantage_r"]>st["median_excursion_advantage_r"],
            "fresh commercial interaction did not beat stale-COT placebo on median excursion advantage")
    return ("MECHANISM_SUPPORT_FOR_VALIDATION" if not reasons else "FAIL_CLOSE"), reasons

def main():
    ap=argparse.ArgumentParser(description="V5 scratch: CFTC Legacy Commercial x GOLD price interaction, 2023 discovery only.")
    ap.add_argument("gold_m1", type=Path, help="GOLD# 2023 MT5 M1 TSV/CSV")
    ap.add_argument("--out-dir", type=Path, default=Path("v5_038a_cot_scratch"))
    ap.add_argument("--cot-cache", type=Path, default=None, help="Optional CFTC API JSON cache path.")
    ap.add_argument("--release-cache", type=Path, default=None, help="Optional release-date JSON cache path.")
    args=ap.parse_args()

    if not args.gold_m1.exists():
        raise SystemExit(f"missing GOLD file: {args.gold_m1}")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    cot_cache=args.cot_cache or (args.out_dir/"cftc_gold_legacy_2022_2024.json")
    release_cache=args.release_cache or (args.out_dir/"cftc_gold_release_dates.json")

    rows, api_source=get_cot_rows(cot_cache)
    attach_release_dates(rows,release_cache)

    # Official spot-checks that should always match known 2023 CFTC pages.
    checks={
        date(2023,1,3):(113520,273494),
        date(2023,1,10):(111718,284196),
        date(2023,7,3):(114905,299622),
    }
    lookup={r.report_date:r for r in rows}
    for d,(cl,cs) in checks.items():
        if d not in lookup or (lookup[d].comm_long,lookup[d].comm_short)!=(cl,cs):
            raise RuntimeError(f"CFTC official spot-check failed {d}: got {lookup.get(d)} expected {(cl,cs)}")

    days,by_day=load_gold_days(args.gold_m1)
    all_weeks,primary=evaluate(rows,days,by_day)
    nondiv=[r for r in all_weeks if r["operationally_fresh"] and not r["commercial_price_divergence"]]
    delayed=[r for r in all_weeks if not r["operationally_fresh"]]
    stale=stale_control(all_weeks)

    classification,reasons=classify(primary,nondiv,stale)

    release_rows=[]
    for r in rows:
        if date(2022,12,1)<=r.report_date<=date(2024,1,15):
            release_rows.append({
                "report_date":r.report_date.isoformat(),
                "release_date":r.release_date.isoformat() if r.release_date else None,
                "release_lag_days":r.release_lag_days,
                "operationally_fresh": bool(r.release_lag_days is not None and r.release_lag_days<=MAX_PRIMARY_RELEASE_LAG_DAYS),
                "comm_long":r.comm_long,
                "comm_short":r.comm_short,
                "comm_net":r.comm_net,
                "archive_url":r.archive_url,
            })

    summary={
        "study":"V5-038A_COT_COMMERCIAL_PRICE_INTERACTION_SCRATCH",
        "authority":"NONE",
        "discovery_market":"GOLD#",
        "discovery_year":2023,
        "gold_file":str(args.gold_m1),
        "gold_sha256":sha256_file(args.gold_m1),
        "cftc_dataset":CFTC_DATASET,
        "cftc_gold_code":CFTC_GOLD_CODE,
        "cftc_api_source":api_source,
        "release_date_source":"official CFTC CMX Legacy archive page 'Updated <date>'",
        "max_primary_release_lag_days":MAX_PRIMARY_RELEASE_LAG_DAYS,
        "primary_definition":"weekly GOLD price change and Commercial net-position change have opposite signs; direction fades price / follows Commercial delta",
        "thresholds":"none on price magnitude or COT magnitude",
        "primary":group_summary(primary),
        "nondivergence_weekly_fade_control":group_summary(nondiv),
        "one_report_stale_commercial_control":group_summary(stale),
        "operational_delay_diagnostic":group_summary(delayed),
        "classification":classification,
        "failed_gates":reasons,
        "hard_stop_if_fail":"No magnitude/COT-index/Managed-Money/session/seasonality rescue in this phase.",
    }

    def write_csv(path,records):
        if not records:
            path.write_text("",encoding="utf-8"); return
        with path.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(records[0].keys()))
            w.writeheader(); w.writerows(records)

    write_csv(args.out_dir/"V5_038A_ALL_WEEK_LEDGER.csv",all_weeks)
    write_csv(args.out_dir/"V5_038A_PRIMARY_LEDGER.csv",primary)
    write_csv(args.out_dir/"V5_038A_RELEASE_LEDGER.csv",release_rows)
    (args.out_dir/"V5_038A_SUMMARY.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
