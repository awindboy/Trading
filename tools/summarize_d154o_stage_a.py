#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import math
import os
import shutil
import statistics
import tempfile
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

UNIVERSE_ID = "D154O_STAGE_A_UL32_20260824"
REFERENCE = "GOLD#"
EXPECTED_FROM = dt.datetime(2026, 8, 17, 0, 0, 0)
EXPECTED_TO = dt.datetime(2026, 8, 23, 23, 59, 59)
MAX_TR_GAP_MINUTES = 5

# Frozen data-quality guards. These are not strategy/outcome thresholds.
MIN_ACTIVE_DAYS = 3
MIN_VALID_BARS = 1000
MIN_VALID_TR = 500
MIN_VALID_PRICE_FRACTION = 0.99
MIN_FVG_COUNT = 20

RATES_NAME = "D154O_STAGE_A_M1.csv"
META_NAME = "D154O_STAGE_A_METADATA.csv"
STATUS_NAME = "D154O_STAGE_A_STATUS.csv"


@dataclass(frozen=True)
class Bar:
    symbol: str
    asset_class: str
    time: dt.datetime
    epoch: int
    open: float
    high: float
    low: float
    close: float
    tick_volume: int
    spread_points: int | None
    real_volume: int
    point: float
    digits: int

    @property
    def valid_price(self) -> bool:
        vals = (self.open, self.high, self.low, self.close)
        if not all(math.isfinite(v) and v > 0 for v in vals):
            return False
        if self.high < self.low:
            return False
        if self.high + 1e-15 < max(self.open, self.close):
            return False
        if self.low - 1e-15 > min(self.open, self.close):
            return False
        return True

    @property
    def spread_price(self) -> float | None:
        if self.spread_points is None or self.spread_points < 0:
            return None
        if not math.isfinite(self.point) or self.point <= 0:
            return None
        return self.spread_points * self.point


def detect_text(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-16", "utf-8", "cp949", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def common_files_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("%APPDATA% is unavailable; pass --input-dir explicitly.")
    return Path(appdata) / "MetaQuotes" / "Terminal" / "Common" / "Files"


def desktop_dir() -> Path:
    if os.name == "nt":
        try:
            import winreg

            key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as k:
                value, _ = winreg.QueryValueEx(k, "Desktop")
            p = Path(os.path.expandvars(value))
            if p.exists():
                return p
        except Exception:
            pass
    for p in (Path.home() / "Desktop", Path.home() / "바탕 화면"):
        if p.exists():
            return p
    return Path.home()


def parse_server_time(s: str) -> dt.datetime:
    s = s.strip()
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return dt.datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError(f"bad server time: {s!r}")


def parse_int(s: str) -> int | None:
    s = s.strip()
    if s == "":
        return None
    return int(s)


def q(values: list[float], p: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * p
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return xs[lo]
    w = pos - lo
    return xs[lo] * (1 - w) + xs[hi] * w


def med(values: Iterable[float]) -> float | None:
    xs = list(values)
    return statistics.median(xs) if xs else None


def safe_ratio(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or not math.isfinite(a) or not math.isfinite(b) or b <= 0:
        return None
    return a / b


def fmt(v: object) -> object:
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return ""
        return f"{v:.12g}"
    if v is None:
        return ""
    return v


def load_universe(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if obj.get("universe_id") != UNIVERSE_ID:
        raise RuntimeError(f"manifest universe_id mismatch: {obj.get('universe_id')}")
    symbols = [x["symbol"] for x in obj["symbols"]]
    if len(symbols) != 32 or len(set(symbols)) != 32:
        raise RuntimeError("manifest must contain exactly 32 unique Stage-A symbols")
    if REFERENCE not in symbols:
        raise RuntimeError("GOLD# reference is missing from manifest")
    return obj


def read_csv(path: Path) -> list[dict[str, str]]:
    text = detect_text(path)
    return list(csv.DictReader(io.StringIO(text)))


def validate_status(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    if len(rows) != 1:
        raise RuntimeError("status CSV must contain exactly one data row")
    r = rows[0]
    if r.get("universe_id") != UNIVERSE_ID:
        raise RuntimeError("status universe_id mismatch")
    if r.get("state") != "EXPORT_COMPLETE":
        raise RuntimeError(f"export is not complete: state={r.get('state')}")
    if int(r.get("expected_symbols", "0")) != 32 or int(r.get("successful_symbols", "0")) != 32:
        raise RuntimeError("export did not complete all 32 symbols")
    if parse_server_time(r["from_server"]) != EXPECTED_FROM:
        raise RuntimeError(f"export from_server mismatch: {r['from_server']}")
    if parse_server_time(r["to_server"]) != EXPECTED_TO:
        raise RuntimeError(f"export to_server mismatch: {r['to_server']}")
    return r


def load_metadata(path: Path, manifest: dict) -> dict[str, dict[str, str]]:
    rows = read_csv(path)
    expected = {x["symbol"]: x["asset_class"] for x in manifest["symbols"]}
    got = {r.get("symbol", ""): r for r in rows}
    if set(got) != set(expected):
        missing = sorted(set(expected) - set(got))
        extra = sorted(set(got) - set(expected))
        raise RuntimeError(f"metadata symbol-set mismatch; missing={missing} extra={extra}")

    for symbol, r in got.items():
        if r.get("universe_id") != UNIVERSE_ID:
            raise RuntimeError(f"metadata universe mismatch for {symbol}")
        if r.get("asset_class") != expected[symbol]:
            raise RuntimeError(f"asset class mismatch for {symbol}")
        if r.get("select_ok") != "1" or r.get("copy_ok") != "1" or int(r.get("rows", "0")) <= 0:
            raise RuntimeError(f"metadata export failure for {symbol}: {r}")
        # Broker category should visibly be an Ultra Low path. This is an environment guard,
        # not a performance filter.
        if "ultra low" not in r.get("symbol_path", "").lower():
            raise RuntimeError(
                f"{symbol} is not confirmed under an Ultra Low broker path: {r.get('symbol_path')!r}"
            )
    return got


def load_bars(path: Path, manifest: dict) -> dict[str, list[Bar]]:
    expected = {x["symbol"]: x["asset_class"] for x in manifest["symbols"]}
    groups: dict[str, list[Bar]] = defaultdict(list)
    for n, r in enumerate(read_csv(path), 2):
        if r.get("universe_id") != UNIVERSE_ID:
            raise RuntimeError(f"rates universe mismatch at CSV line {n}")
        symbol = r.get("symbol", "")
        if symbol not in expected:
            raise RuntimeError(f"unexpected symbol in rates CSV: {symbol}")
        if r.get("asset_class") != expected[symbol]:
            raise RuntimeError(f"asset class mismatch in rates CSV for {symbol}")
        try:
            spread_points = parse_int(r.get("spread_points", ""))
            b = Bar(
                symbol=symbol,
                asset_class=expected[symbol],
                time=parse_server_time(r["time_server"]),
                epoch=int(r["time_epoch"]),
                open=float(r["open"]),
                high=float(r["high"]),
                low=float(r["low"]),
                close=float(r["close"]),
                tick_volume=int(r["tick_volume"]),
                spread_points=spread_points,
                real_volume=int(r["real_volume"]),
                point=float(r["point"]),
                digits=int(r["digits"]),
            )
        except Exception as e:
            raise RuntimeError(f"cannot parse rates CSV line {n}: {e}") from e
        if b.time < EXPECTED_FROM or b.time > EXPECTED_TO:
            raise RuntimeError(f"out-of-window bar for {symbol}: {b.time}")
        groups[symbol].append(b)

    if set(groups) != set(expected):
        missing = sorted(set(expected) - set(groups))
        raise RuntimeError(f"rates CSV missing symbols: {missing}")

    for symbol, bars in groups.items():
        bars.sort(key=lambda x: x.time)
        times = [b.time for b in bars]
        if len(times) != len(set(times)):
            raise RuntimeError(f"duplicate M1 timestamps for {symbol}")
    return groups


def bar_tr(bar: Bar, prev: Bar | None) -> float | None:
    if prev is None or not bar.valid_price or not prev.valid_price:
        return None
    gap = (bar.time - prev.time).total_seconds() / 60.0
    if gap <= 0 or gap > MAX_TR_GAP_MINUTES:
        return None
    return max(bar.high - bar.low, abs(bar.high - prev.close), abs(bar.low - prev.close))


def fvg_observations(bars: list[Bar]) -> list[tuple[dt.datetime, float, float]]:
    out: list[tuple[dt.datetime, float, float]] = []
    for i in range(2, len(bars)):
        b1, b2, b3 = bars[i - 2], bars[i - 1], bars[i]
        if not (b1.valid_price and b2.valid_price and b3.valid_price):
            continue
        g12 = (b2.time - b1.time).total_seconds() / 60.0
        g23 = (b3.time - b2.time).total_seconds() / 60.0
        if g12 <= 0 or g12 > MAX_TR_GAP_MINUTES or g23 <= 0 or g23 > MAX_TR_GAP_MINUTES:
            continue
        width = 0.0
        if b3.low > b1.high:
            width = b3.low - b1.high
        elif b3.high < b1.low:
            width = b1.low - b3.high
        if width <= 0:
            continue
        sp = b3.spread_price
        if sp is None:
            continue
        out.append((b3.time, width, sp / width))
    return out


def symbol_weekly(symbol: str, bars: list[Bar], meta: dict[str, str]) -> tuple[dict, list[dict]]:
    total = len(bars)
    valid_bars = [b for b in bars if b.valid_price]
    valid_price_fraction = len(valid_bars) / total if total else 0.0
    missing_spread_count = sum(1 for b in bars if b.spread_price is None)
    zero_spread_count = sum(1 for b in bars if b.spread_price == 0)
    active_days = len({b.time.date() for b in valid_bars})

    spread_prices = [b.spread_price for b in valid_bars if b.spread_price is not None]
    spread_bps = [
        b.spread_price / b.close * 10000.0
        for b in valid_bars
        if b.spread_price is not None and b.close > 0
    ]

    tr_values: list[float] = []
    spread_over_tr: list[float] = []
    trs_by_time: dict[dt.datetime, float] = {}
    for i, b in enumerate(bars):
        prev = bars[i - 1] if i > 0 else None
        tr = bar_tr(b, prev)
        if tr is None or tr <= 0:
            continue
        trs_by_time[b.time] = tr
        tr_values.append(tr)
        sp = b.spread_price
        if sp is not None:
            spread_over_tr.append(sp / tr)

    fvgs = fvg_observations(bars)
    fvg_widths = [x[1] for x in fvgs]
    fvg_spread_over_width = [x[2] for x in fvgs]

    median_spread = med(spread_prices)
    median_tr = med(tr_values)
    primary_proxy = safe_ratio(median_spread, median_tr)
    fvg_proxy = med(fvg_spread_over_width) if len(fvgs) >= MIN_FVG_COUNT else None
    median_spread_bps = med(spread_bps)

    quality_reasons: list[str] = []
    if active_days < MIN_ACTIVE_DAYS:
        quality_reasons.append(f"active_days<{MIN_ACTIVE_DAYS}")
    if len(valid_bars) < MIN_VALID_BARS:
        quality_reasons.append(f"valid_bars<{MIN_VALID_BARS}")
    if len(tr_values) < MIN_VALID_TR:
        quality_reasons.append(f"valid_tr<{MIN_VALID_TR}")
    if valid_price_fraction < MIN_VALID_PRICE_FRACTION:
        quality_reasons.append(f"valid_price_fraction<{MIN_VALID_PRICE_FRACTION}")
    if missing_spread_count > 0:
        quality_reasons.append("missing_or_invalid_spread")
    if primary_proxy is None or median_spread_bps is None:
        quality_reasons.append("required_proxy_unavailable")

    quality_status = "OK" if not quality_reasons else "INSUFFICIENT_DATA"
    fvg_status = "OK" if len(fvgs) >= MIN_FVG_COUNT else "INSUFFICIENT_FVG"

    weekly = {
        "universe_id": UNIVERSE_ID,
        "symbol": symbol,
        "asset_class": bars[0].asset_class if bars else "",
        "reference": 1 if symbol == REFERENCE else 0,
        "symbol_path": meta.get("symbol_path", ""),
        "point": float(meta.get("point", "0") or 0),
        "digits": int(meta.get("digits", "0") or 0),
        "active_days": active_days,
        "total_m1_rows": total,
        "valid_m1_bars": len(valid_bars),
        "valid_price_fraction": valid_price_fraction,
        "missing_spread_fraction": missing_spread_count / total if total else 1.0,
        "zero_spread_fraction": zero_spread_count / total if total else 0.0,
        "valid_tr_count": len(tr_values),
        "raw_fvg_count": len(fvgs),
        "median_spread_price": median_spread,
        "median_valid_m1_tr": median_tr,
        "raw_spread_over_m1_tr": primary_proxy,
        "bar_spread_over_tr_q25": q(spread_over_tr, 0.25),
        "bar_spread_over_tr_q50": q(spread_over_tr, 0.50),
        "bar_spread_over_tr_q75": q(spread_over_tr, 0.75),
        "bar_spread_over_tr_q90": q(spread_over_tr, 0.90),
        "median_raw_fvg_width": med(fvg_widths),
        "median_spread_over_raw_fvg_width": fvg_proxy,
        "median_spread_bps": median_spread_bps,
        "quality_status": quality_status,
        "quality_reasons": ";".join(quality_reasons),
        "fvg_proxy_status": fvg_status,
    }

    by_date: dict[dt.date, list[Bar]] = defaultdict(list)
    for b in bars:
        by_date[b.time.date()].append(b)

    daily: list[dict] = []
    for day in sorted(by_date):
        ds = by_date[day]
        dsp = [b.spread_price for b in ds if b.valid_price and b.spread_price is not None]
        dbps = [
            b.spread_price / b.close * 10000.0
            for b in ds
            if b.valid_price and b.spread_price is not None and b.close > 0
        ]
        dtr = [trs_by_time[b.time] for b in ds if b.time in trs_by_time]
        dfvg = [x for x in fvgs if x[0].date() == day]
        daily.append(
            {
                "universe_id": UNIVERSE_ID,
                "symbol": symbol,
                "asset_class": weekly["asset_class"],
                "date_server": day.isoformat(),
                "m1_rows": len(ds),
                "valid_bars": sum(1 for b in ds if b.valid_price),
                "valid_tr_count": len(dtr),
                "raw_fvg_count": len(dfvg),
                "median_spread_price": med(dsp),
                "median_valid_m1_tr": med(dtr),
                "raw_spread_over_m1_tr": safe_ratio(med(dsp), med(dtr)),
                "median_spread_bps": med(dbps),
            }
        )

    return weekly, daily


def add_gold_relatives(rows: list[dict]) -> None:
    gold = next((r for r in rows if r["symbol"] == REFERENCE), None)
    if gold is None or gold["quality_status"] != "OK":
        raise RuntimeError("GOLD# reference failed Stage-A data quality; cannot compute GOLD-relative screen")

    keys = (
        "raw_spread_over_m1_tr",
        "median_spread_over_raw_fvg_width",
        "median_spread_bps",
    )
    for r in rows:
        for key in keys:
            r[key + "_vs_gold"] = safe_ratio(r.get(key), gold.get(key))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"refusing to write empty CSV: {path}")
    fields: list[str] = []
    seen: set[str] = set()
    for r in rows:
        for k in r:
            if k not in seen:
                seen.add(k)
                fields.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: fmt(r.get(k)) for k in fields})


def build_readme(rows: list[dict]) -> str:
    ok = sum(r["quality_status"] == "OK" for r in rows)
    fvg_ok = sum(r["fvg_proxy_status"] == "OK" for r in rows)
    return f"""D154O Stage A outcome-blind raw screen package
Universe: {UNIVERSE_ID}
Symbols: {len(rows)} (data-quality OK: {ok}; FVG proxy OK: {fvg_ok})
Window: {EXPECTED_FROM} through {EXPECTED_TO} broker/server time
Reference: {REFERENCE}

Primary chart proxy:
  median spread_price / median valid M1 true range

Secondary proxies:
  median per-FVG spread_price / generic raw M1 FVG width
  median spread / close in basis points

Important:
- These are chart-only proxies, NOT exact D154K strategy-derived metrics.
- No strategy win rate, P/L, Entry gate, spread threshold, symbol veto, or GoldLikeScore is produced here.
- The full 32-symbol universe is kept visible. The later Gold-like shortlist and negative controls must be frozen before any new-symbol 2025 strategy outcome is generated.
- TR excludes the first bar after a gap > {MAX_TR_GAP_MINUTES} minutes.
- Raw FVG detection also refuses three-bar sequences that cross a >{MAX_TR_GAP_MINUTES}-minute gap.
- Data-quality guards are frozen infrastructure checks, not profitability filters.
"""


def main() -> None:
    ap = argparse.ArgumentParser(description="Summarize D154O Stage-A raw M1+spread export.")
    ap.add_argument("--input-dir", type=Path, default=None, help="Directory containing the three D154O export CSVs. Defaults to MT5 Common Files.")
    ap.add_argument("--output-dir", type=Path, default=None, help="Optional output directory. Default: a temporary directory zipped to Desktop.")
    ap.add_argument("--manifest", type=Path, default=None, help="Universe JSON. Default: repo/config/d154o_stage_a_universe.json")
    args = ap.parse_args()

    repo = Path(__file__).resolve().parents[1]
    manifest_path = args.manifest or (repo / "config" / "d154o_stage_a_universe.json")
    manifest = load_universe(manifest_path)

    in_dir = args.input_dir or common_files_dir()
    rates_path = in_dir / RATES_NAME
    meta_path = in_dir / META_NAME
    status_path = in_dir / STATUS_NAME
    for p in (rates_path, meta_path, status_path):
        if not p.exists():
            raise SystemExit(f"ERROR: required export file not found: {p}")

    status = validate_status(status_path)
    metadata = load_metadata(meta_path, manifest)
    groups = load_bars(rates_path, manifest)

    weekly: list[dict] = []
    daily: list[dict] = []
    manifest_order = {x["symbol"]: i for i, x in enumerate(manifest["symbols"])}
    for item in manifest["symbols"]:
        symbol = item["symbol"]
        w, d = symbol_weekly(symbol, groups[symbol], metadata[symbol])
        weekly.append(w)
        daily.extend(d)
    add_gold_relatives(weekly)

    # Preserve frozen universe order; do not silently rank markets by one proxy.
    weekly.sort(key=lambda r: manifest_order[r["symbol"]])
    daily.sort(key=lambda r: (manifest_order[r["symbol"]], r["date_server"]))

    own_temp = args.output_dir is None
    out_dir = args.output_dir or Path(tempfile.mkdtemp(prefix="D154O_STAGE_A_"))
    out_dir.mkdir(parents=True, exist_ok=True)

    write_csv(out_dir / "D154O_STAGE_A_WEEKLY_SCREEN.csv", weekly)
    write_csv(out_dir / "D154O_STAGE_A_DAILY_SCREEN.csv", daily)
    (out_dir / "D154O_STAGE_A_UNIVERSE.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out_dir / "D154O_STAGE_A_EXPORT_STATUS.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    (out_dir / "README.txt").write_text(build_readme(weekly), encoding="utf-8")

    raw_dir = out_dir / "raw_input"
    raw_dir.mkdir(exist_ok=True)
    for p in (rates_path, meta_path, status_path):
        shutil.copy2(p, raw_dir / p.name)

    result_manifest = {
        "universe_id": UNIVERSE_ID,
        "generated_at_local": dt.datetime.now().isoformat(timespec="seconds"),
        "input_dir": str(in_dir),
        "reference": REFERENCE,
        "quality_thresholds": {
            "min_active_days": MIN_ACTIVE_DAYS,
            "min_valid_bars": MIN_VALID_BARS,
            "min_valid_tr": MIN_VALID_TR,
            "min_valid_price_fraction": MIN_VALID_PRICE_FRACTION,
            "min_fvg_count": MIN_FVG_COUNT,
            "max_gap_minutes_for_tr_and_fvg": MAX_TR_GAP_MINUTES,
        },
        "symbol_quality": {
            r["symbol"]: {
                "quality_status": r["quality_status"],
                "quality_reasons": r["quality_reasons"],
                "fvg_proxy_status": r["fvg_proxy_status"],
            }
            for r in weekly
        },
        "outcome_blind": True,
        "strategy_outcomes_included": False,
        "weighted_gold_like_score": False,
    }
    (out_dir / "D154O_STAGE_A_RESULT_MANIFEST.json").write_text(
        json.dumps(result_manifest, indent=2), encoding="utf-8"
    )

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = desktop_dir() / f"D154O_STAGE_A_UL32_{stamp}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(out_dir.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(out_dir))

    print("D154O Stage-A summary PASS")
    print(f"  universe: {UNIVERSE_ID}")
    print(f"  symbols:  {len(weekly)}")
    print(f"  quality OK: {sum(r['quality_status'] == 'OK' for r in weekly)}/{len(weekly)}")
    print(f"  FVG proxy OK: {sum(r['fvg_proxy_status'] == 'OK' for r in weekly)}/{len(weekly)}")
    print(f"  result ZIP: {zip_path}")
    print("Upload that ZIP for outcome-blind shortlist/control freeze analysis.")

    if own_temp:
        # Keep the temporary result directory for local audit; the ZIP is the handoff artifact.
        print(f"  expanded copy: {out_dir}")


if __name__ == "__main__":
    main()
