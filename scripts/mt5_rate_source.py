"""Load a reproducible closed-bar MT5 rate batch with optional NPZ caching."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np


FINGERPRINT_FIELDS = ("time", "open", "high", "low", "close", "tick_volume")


def parse_utc(value: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def rate_fingerprint(rates: np.ndarray) -> str:
    if rates.dtype.names is None:
        raise ValueError("rates must be a structured NumPy array")
    missing = [field for field in FINGERPRINT_FIELDS if field not in rates.dtype.names]
    if missing:
        raise ValueError(f"rates are missing fingerprint fields: {missing}")
    digest = hashlib.sha256()
    digest.update(str(len(rates)).encode("ascii"))
    for field in FINGERPRINT_FIELDS:
        digest.update(field.encode("ascii"))
        digest.update(np.ascontiguousarray(rates[field]).tobytes())
    return digest.hexdigest()


def validate_rates(rates: np.ndarray, minimum: int = 100) -> None:
    if len(rates) < minimum:
        raise ValueError(f"insufficient M1 rates: received={len(rates)} minimum={minimum}")
    times = np.asarray(rates["time"], dtype=np.int64)
    if np.any(times[1:] <= times[:-1]):
        raise ValueError("M1 rates must have unique, strictly increasing timestamps")


def save_rate_cache(path: Path, rates: np.ndarray, metadata: dict[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        **metadata,
        "bars": len(rates),
        "firstBarOpenTimeUtc": datetime.fromtimestamp(int(rates[0]["time"]), timezone.utc).isoformat(),
        "lastBarOpenTimeUtc": datetime.fromtimestamp(int(rates[-1]["time"]), timezone.utc).isoformat(),
        "sha256": rate_fingerprint(rates),
    }
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(
            handle,
            rates=rates,
            metadata=np.asarray(json.dumps(payload, sort_keys=True)),
        )
    os.replace(temporary, path)


def load_rate_cache(path: Path) -> tuple[np.ndarray, dict[str, Any]]:
    with np.load(path.resolve(), allow_pickle=False) as archive:
        rates = archive["rates"]
        metadata = json.loads(str(archive["metadata"].item()))
    validate_rates(rates)
    actual = rate_fingerprint(rates)
    expected = str(metadata.get("sha256") or "")
    if expected and actual != expected:
        raise ValueError(f"rate cache fingerprint mismatch: expected={expected} actual={actual}")
    metadata["sha256"] = actual
    metadata["cachePath"] = str(path.resolve())
    metadata["provider"] = "npz-cache"
    return rates, metadata


def load_mt5_m1_rates(
    symbol: str,
    bars: int,
    from_utc: str | None = None,
    to_utc: str | None = None,
    cache_path: Path | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    if cache_path is not None and cache_path.exists():
        rates, metadata = load_rate_cache(cache_path)
        cached_symbol = str(metadata.get("symbol") or "")
        if cached_symbol and cached_symbol != symbol:
            raise ValueError(f"rate cache symbol mismatch: requested={symbol} cached={cached_symbol}")
        return rates, metadata
    if bool(from_utc) != bool(to_utc):
        raise ValueError("--from-utc and --to-utc must be supplied together")

    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        raise RuntimeError(f"MetaTrader5 package unavailable: {exc}") from exc
    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    try:
        if not mt5.symbol_select(symbol, True):
            raise RuntimeError(f"symbol_select failed for {symbol}: {mt5.last_error()}")
        if from_utc and to_utc:
            start = parse_utc(from_utc)
            end = parse_utc(to_utc)
            if end <= start:
                raise ValueError("--to-utc must be later than --from-utc")
            terminal = mt5.terminal_info()
            elapsed_days = (end - start).total_seconds() / 86400.0
            required_estimate = int(elapsed_days * 24 * 60 * 5 / 7 * 1.10)
            max_bars = int(terminal.maxbars) if terminal is not None else 0
            if max_bars and max_bars < required_estimate:
                raise RuntimeError(
                    f"MT5 MaxBars={max_bars} cannot expose the requested range "
                    f"(~{required_estimate} M1 bars). Set Tools > Options > Charts > "
                    f"Max bars in chart to at least {required_estimate}, restart MT5, and rerun."
                )
            chunks: list[np.ndarray] = []
            cursor = start
            while cursor < end:
                chunk_end = min(cursor + timedelta(days=30), end)
                part = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, cursor, chunk_end)
                if part is not None and len(part):
                    start_epoch = int(cursor.timestamp())
                    end_epoch = int(chunk_end.timestamp())
                    valid = part[(part["time"] >= start_epoch) & (part["time"] < end_epoch)]
                    if len(valid):
                        chunks.append(valid)
                cursor = chunk_end
            if not chunks:
                raise RuntimeError(f"MT5 returned no in-range M1 bars: {mt5.last_error()}")
            rates = np.concatenate(chunks)
            _, unique_indices = np.unique(rates["time"], return_index=True)
            rates = rates[np.sort(unique_indices)]
            coverage_tolerance = 7 * 86400
            if int(rates[0]["time"]) > int(start.timestamp()) + coverage_tolerance:
                raise RuntimeError(
                    "MT5 history does not cover the requested start. Increase Max bars in chart, "
                    "restart MT5, and let GOLD M1 history synchronize before retrying."
                )
            if int(rates[-1]["time"]) < int(end.timestamp()) - coverage_tolerance:
                raise RuntimeError("MT5 history does not cover the requested end")
            request = {
                "mode": "utc-range",
                "requestedFromUtc": start.isoformat(),
                "requestedToUtc": end.isoformat(),
                "terminalMaxBars": max_bars,
            }
        else:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 1, bars)
            request = {"mode": "closed-bars-from-current", "requestedBars": bars}
        if rates is None:
            raise RuntimeError(f"MT5 rate request failed: {mt5.last_error()}")
    finally:
        mt5.shutdown()

    validate_rates(rates)
    metadata = {
        "provider": "MetaTrader5",
        "symbol": symbol,
        "timeframe": "M1",
        **request,
        "bars": len(rates),
        "firstBarOpenTimeUtc": datetime.fromtimestamp(int(rates[0]["time"]), timezone.utc).isoformat(),
        "lastBarOpenTimeUtc": datetime.fromtimestamp(int(rates[-1]["time"]), timezone.utc).isoformat(),
        "sha256": rate_fingerprint(rates),
    }
    if cache_path is not None:
        save_rate_cache(cache_path, rates, metadata)
        metadata["cachePath"] = str(cache_path.resolve())
    return rates, metadata
