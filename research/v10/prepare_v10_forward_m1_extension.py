"""Validate an MT5 M1 extension and write one chronological raw-M1 file.

This is a data-preparation utility, not a replay.  It proves that the MT5
cache reproduces every trusted prefix row before appending only newer rows.
The generated TSV can then be consumed line by line by an official causal
replay without preloading a future dataframe.
"""

from __future__ import annotations

import argparse
import calendar
import csv
import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import numpy as np


SOURCE_TS = "%Y.%m.%d %H:%M:%S"
EXPECTED_COLUMNS = (
    "<DATE>",
    "<TIME>",
    "<OPEN>",
    "<HIGH>",
    "<LOW>",
    "<CLOSE>",
    "<TICKVOL>",
    "<VOL>",
    "<SPREAD>",
)


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trusted-prefix", required=True, type=Path)
    parser.add_argument("--mt5-cache", required=True, type=Path)
    parser.add_argument("--out-m1", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def epoch(row: dict[str, str]) -> int:
    value = datetime.strptime(f"{row['<DATE>']} {row['<TIME>']}", SOURCE_TS)
    return calendar.timegm(value.timetuple())


def same_price(left: str, right: float) -> bool:
    return abs(float(left) - float(right)) <= 1e-9


def main() -> None:
    args = cli()
    args.out_m1.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)

    with np.load(args.mt5_cache.resolve(), allow_pickle=False) as archive:
        rates = archive["rates"]
        cache_metadata = json.loads(str(archive["metadata"].item()))

    if len(rates) == 0:
        raise ValueError("MT5 cache is empty")
    times = np.asarray(rates["time"], dtype=np.int64)
    if np.any(times[1:] <= times[:-1]):
        raise ValueError("MT5 cache timestamps are not unique and increasing")

    prefix_rows = 0
    prefix_first: int | None = None
    prefix_last: int | None = None
    with args.trusted_prefix.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != EXPECTED_COLUMNS:
            raise ValueError(f"unexpected trusted-prefix schema: {reader.fieldnames}")
        for index, row in enumerate(reader):
            if index >= len(rates):
                raise ValueError("MT5 cache ends before trusted prefix")
            ts = epoch(row)
            rate = rates[index]
            if int(rate["time"]) != ts:
                raise ValueError(
                    f"timestamp mismatch at row {index}: prefix={ts} mt5={int(rate['time'])}"
                )
            for source, field in (
                ("<OPEN>", "open"),
                ("<HIGH>", "high"),
                ("<LOW>", "low"),
                ("<CLOSE>", "close"),
            ):
                if not same_price(row[source], float(rate[field])):
                    raise ValueError(
                        f"{source} mismatch at row {index}: prefix={row[source]} mt5={rate[field]}"
                    )
            if int(row["<TICKVOL>"]) != int(rate["tick_volume"]):
                raise ValueError(f"tick-volume mismatch at row {index}")
            if int(row["<SPREAD>"]) != int(rate["spread"]):
                raise ValueError(f"spread mismatch at row {index}")
            prefix_first = ts if prefix_first is None else prefix_first
            prefix_last = ts
            prefix_rows += 1

    if prefix_last is None:
        raise ValueError("trusted prefix contains no rows")
    if prefix_rows >= len(rates):
        raise ValueError("MT5 cache contains no new rows after trusted prefix")
    if int(rates[prefix_rows - 1]["time"]) != prefix_last:
        raise ValueError("trusted-prefix final row does not align with MT5 cache")

    shutil.copyfile(args.trusted_prefix, args.out_m1)
    with args.out_m1.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        for rate in rates[prefix_rows:]:
            ts = datetime.fromtimestamp(int(rate["time"]), UTC).replace(tzinfo=None)
            writer.writerow(
                (
                    ts.strftime("%Y.%m.%d"),
                    ts.strftime("%H:%M:%S"),
                    f"{float(rate['open']):.10f}".rstrip("0").rstrip("."),
                    f"{float(rate['high']):.10f}".rstrip("0").rstrip("."),
                    f"{float(rate['low']):.10f}".rstrip("0").rstrip("."),
                    f"{float(rate['close']):.10f}".rstrip("0").rstrip("."),
                    int(rate["tick_volume"]),
                    int(rate["real_volume"]),
                    int(rate["spread"]),
                )
            )

    manifest = {
        "ok": True,
        "role": "validated raw-M1 extension for causal forward replay",
        "trusted_prefix": str(args.trusted_prefix.resolve()),
        "trusted_prefix_sha256": sha256_file(args.trusted_prefix),
        "mt5_cache": str(args.mt5_cache.resolve()),
        "mt5_cache_file_sha256": sha256_file(args.mt5_cache),
        "mt5_cache_payload_sha256": cache_metadata.get("sha256"),
        "symbol": cache_metadata.get("symbol"),
        "prefix_rows_verified": prefix_rows,
        "prefix_first": datetime.fromtimestamp(prefix_first, UTC).replace(tzinfo=None).isoformat(sep=" "),
        "prefix_last": datetime.fromtimestamp(prefix_last, UTC).replace(tzinfo=None).isoformat(sep=" "),
        "extension_rows": int(len(rates) - prefix_rows),
        "extension_first": datetime.fromtimestamp(int(rates[prefix_rows]["time"]), UTC).replace(tzinfo=None).isoformat(sep=" "),
        "extension_last": datetime.fromtimestamp(int(rates[-1]["time"]), UTC).replace(tzinfo=None).isoformat(sep=" "),
        "output": str(args.out_m1.resolve()),
        "output_sha256": sha256_file(args.out_m1),
        "output_rows": int(len(rates)),
    }
    args.manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
