from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import time
import threading
from typing import Any, Protocol

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.gemini_replay_provider import GeminiReplayError
from scripts.mentor_ai_replay_v4 import (
    CORE_PATH,
    RENDERER_PATH,
    RUNNER_PATH,
    V4_MANIFEST,
    GeminiProvider,
    V4Runner,
    atomic_json,
    load_secret,
    load_secret_pool,
    read_json,
    sha256_file,
    system_instruction_evidence,
    write_trades_csv,
)
from scripts.mentor_replay_v4_core import (
    PIPELINE_VERSION,
    MarketData,
    V4ContractError,
    canonical_hash,
    new_runtime,
    utc_text,
)
from scripts.mt5_rate_source import save_rate_cache, validate_rates


LIVE_ROOT = ROOT / "output" / "mentor_ai_live_v4"
LIVE_DATA_ROOT = ROOT / "data" / "mentor_ai_live_v4"
CHECKPOINT_NAME = "bar_transaction.json"


class ClosedM1Feed(Protocol):
    def connect(self) -> dict[str, Any]: ...
    def closed_rates(self, bars: int) -> tuple[np.ndarray, dict[str, Any]]: ...
    def broker_snapshot(self) -> dict[str, Any]: ...
    def submit_pending(
        self, order: dict[str, Any], volume: float, client_id: str
    ) -> dict[str, Any]: ...
    def cancel_pending(self, ticket: int, client_id: str) -> dict[str, Any]: ...
    def shutdown(self) -> None: ...


class Mt5ClosedM1Feed:
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        self.mt5: Any = None

    def connect(self) -> dict[str, Any]:
        try:
            import MetaTrader5 as mt5  # type: ignore
        except ImportError as exc:
            raise V4ContractError(f"MetaTrader5 package is unavailable: {exc}") from exc
        if not mt5.initialize():
            raise V4ContractError(f"MT5 initialize failed: {mt5.last_error()}")
        if not mt5.symbol_select(self.symbol, True):
            mt5.shutdown()
            raise V4ContractError(f"MT5 symbol_select failed: {mt5.last_error()}")
        account = mt5.account_info()
        terminal = mt5.terminal_info()
        info = mt5.symbol_info(self.symbol)
        if account is None or terminal is None or info is None:
            mt5.shutdown()
            raise V4ContractError(f"MT5 account/terminal/symbol info failed: {mt5.last_error()}")
        self.mt5 = mt5
        return {
            "login": int(account.login),
            "server": str(account.server),
            "tradeMode": int(account.trade_mode),
            "demoTradeMode": int(getattr(mt5, "ACCOUNT_TRADE_MODE_DEMO", 0)),
            "terminalConnected": bool(terminal.connected),
            "tradeAllowed": bool(terminal.trade_allowed),
            "point": float(info.point),
            "tradeStopsLevel": int(info.trade_stops_level),
            "volumeMin": float(info.volume_min),
            "volumeStep": float(info.volume_step),
            "volumeMax": float(info.volume_max),
            "digits": int(info.digits),
        }

    def closed_rates(self, bars: int) -> tuple[np.ndarray, dict[str, Any]]:
        if self.mt5 is None:
            raise V4ContractError("MT5 feed is not connected")
        rates = self.mt5.copy_rates_from_pos(
            self.symbol, self.mt5.TIMEFRAME_M1, 1, max(2, int(bars))
        )
        tick = self.mt5.symbol_info_tick(self.symbol)
        if rates is None or not len(rates) or tick is None:
            raise V4ContractError(f"MT5 closed M1 read failed: {self.mt5.last_error()}")
        rates = np.sort(rates, order="time")
        _, indexes = np.unique(rates["time"], return_index=True)
        rates = rates[np.sort(indexes)]
        validate_rates(rates, minimum=2)
        return rates, {
            "serverNow": int(tick.time),
            "bid": float(tick.bid),
            "ask": float(tick.ask),
        }

    def broker_snapshot(self) -> dict[str, Any]:
        if self.mt5 is None:
            raise V4ContractError("MT5 feed is not connected")
        orders = self.mt5.orders_get(symbol=self.symbol)
        positions = self.mt5.positions_get(symbol=self.symbol)
        if orders is None or positions is None:
            raise V4ContractError(
                f"MT5 broker reconciliation read failed: {self.mt5.last_error()}"
            )

        def record(item: Any) -> dict[str, Any]:
            return {
                "ticket": int(item.ticket),
                "symbol": str(item.symbol),
                "comment": str(getattr(item, "comment", "")),
                "type": int(item.type),
                "volume": float(item.volume_current if hasattr(item, "volume_current") else item.volume),
                "price": float(item.price_open),
                "sl": float(item.sl),
                "tp": float(item.tp),
            }

        return {
            "orders": [record(item) for item in orders],
            "positions": [record(item) for item in positions],
        }

    def submit_pending(
        self, order: dict[str, Any], volume: float, client_id: str
    ) -> dict[str, Any]:
        if self.mt5 is None:
            raise V4ContractError("MT5 feed is not connected")
        direction = str(order["direction"])
        request = {
            "action": self.mt5.TRADE_ACTION_PENDING,
            "symbol": self.symbol,
            "volume": float(volume),
            "type": (
                self.mt5.ORDER_TYPE_BUY_LIMIT
                if direction == "LONG" else self.mt5.ORDER_TYPE_SELL_LIMIT
            ),
            "price": float(order["entry"]),
            "sl": float(order["stop"]),
            "tp": float(order["target"]),
            "type_time": self.mt5.ORDER_TIME_GTC,
            "type_filling": self.mt5.ORDER_FILLING_RETURN,
            "comment": str(client_id)[:31],
        }
        checked = self.mt5.order_check(request)
        if checked is None or int(checked.retcode) not in {
            int(getattr(self.mt5, "TRADE_RETCODE_DONE", 10009)),
            int(getattr(self.mt5, "TRADE_RETCODE_PLACED", 10008)),
        }:
            code = None if checked is None else int(checked.retcode)
            raise V4ContractError(f"DEMO_ORDER_CHECK_REJECTED:{code}")
        result = self.mt5.order_send(request)
        if result is None or int(result.retcode) not in {
            int(getattr(self.mt5, "TRADE_RETCODE_DONE", 10009)),
            int(getattr(self.mt5, "TRADE_RETCODE_PLACED", 10008)),
        }:
            code = None if result is None else int(result.retcode)
            raise V4ContractError(f"DEMO_ORDER_SEND_REJECTED:{code}")
        return {
            "ticket": int(result.order),
            "retcode": int(result.retcode),
            "clientId": client_id,
        }

    def cancel_pending(self, ticket: int, client_id: str) -> dict[str, Any]:
        if self.mt5 is None:
            raise V4ContractError("MT5 feed is not connected")
        result = self.mt5.order_send({
            "action": self.mt5.TRADE_ACTION_REMOVE,
            "order": int(ticket),
            "symbol": self.symbol,
            "comment": str(client_id)[:31],
        })
        if result is None or int(result.retcode) != int(
            getattr(self.mt5, "TRADE_RETCODE_DONE", 10009)
        ):
            code = None if result is None else int(result.retcode)
            raise V4ContractError(f"DEMO_ORDER_CANCEL_REJECTED:{code}")
        return {"ticket": int(ticket), "retcode": int(result.retcode)}

    def shutdown(self) -> None:
        if self.mt5 is not None:
            self.mt5.shutdown()
            self.mt5 = None


def merge_rates(existing: np.ndarray | None, incoming: np.ndarray) -> np.ndarray:
    validate_rates(incoming, minimum=1)
    if existing is None or not len(existing):
        return incoming.copy()
    validate_rates(existing, minimum=1)
    if existing.dtype != incoming.dtype:
        raise V4ContractError("MT5 M1 dtype changed; refusing to corrupt the live archive")
    if (
        int(incoming[0]["time"]) > int(existing[-1]["time"])
        and int(incoming[-1]["time"]) > int(existing[-1]["time"])
    ):
        raise V4ContractError(
            "LIVE_ARCHIVE_UNRECOVERABLE_GAP: MT5 backfill does not overlap the archive"
        )
    combined = np.concatenate((existing, incoming))
    order = np.argsort(combined["time"], kind="stable")
    combined = combined[order]
    _, reverse_indexes = np.unique(combined["time"][::-1], return_index=True)
    keep = np.sort(len(combined) - 1 - reverse_indexes)
    merged = combined[keep]
    validate_rates(merged, minimum=1)
    if len(existing) and not np.array_equal(merged[: len(existing)], existing):
        raise V4ContractError("historical MT5 M1 bars changed; live archive is append-only")
    return merged


def adaptive_backfill(
    feed: ClosedM1Feed,
    existing: np.ndarray | None,
    *,
    initial_bars: int,
    maximum_bars: int,
    offset_seconds: int,
) -> tuple[np.ndarray, dict[str, Any], int]:
    """Expand the MT5 request until it overlaps the append-only archive."""
    bars = max(2, int(initial_bars))
    while True:
        incoming, snapshot = feed.closed_rates(bars)
        incoming, snapshot = normalize_broker_time(incoming, snapshot, offset_seconds)
        if existing is None or not len(existing) or int(incoming[0]["time"]) <= int(
            existing[-1]["time"]
        ):
            return incoming, snapshot, bars
        if bars >= int(maximum_bars):
            raise V4ContractError(
                "LIVE_ARCHIVE_UNRECOVERABLE_GAP: adaptive MT5 backfill exhausted"
            )
        bars = min(int(maximum_bars), bars * 2)


class LiveRequestBuffer:
    """Durably sample closed M1 bars and broker ticks while the model responds."""

    def __init__(
        self,
        feed: ClosedM1Feed,
        run_dir: Path,
        *,
        offset_seconds: int,
        poll_seconds: float = 1.0,
        poll_bars: int = 8,
    ) -> None:
        self.feed = feed
        self.run_dir = run_dir
        self.offset_seconds = int(offset_seconds)
        self.poll_seconds = max(0.05, float(poll_seconds))
        self.poll_bars = max(2, int(poll_bars))
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._context: dict[str, Any] | None = None
        self._error: Exception | None = None

    def before_request(self, context: dict[str, Any]) -> None:
        if self._thread is not None:
            raise V4ContractError("request market buffer is already running")
        self._context = dict(context)
        self._stop.clear()
        self._error = None
        self._thread = threading.Thread(target=self._capture, daemon=True)
        self._thread.start()

    def _capture(self) -> None:
        path = self.run_dir / "request_market_buffer.jsonl"
        seen: set[int] = set()
        try:
            while not self._stop.is_set():
                rates, snapshot = self.feed.closed_rates(self.poll_bars)
                rates, snapshot = normalize_broker_time(
                    rates, snapshot, self.offset_seconds
                )
                rows = []
                for row in rates:
                    timestamp = int(row["time"])
                    if timestamp in seen:
                        continue
                    seen.add(timestamp)
                    rows.append({
                        "time": timestamp,
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "tick_volume": int(row["tick_volume"]),
                        "spread": int(row["spread"]),
                        "real_volume": int(row["real_volume"]),
                    })
                record = {
                    **(self._context or {}),
                    "capturedAtUtc": utc_text(int(time.time())),
                    "tick": {
                        "serverNow": int(snapshot["serverNow"]),
                        "bid": float(snapshot["bid"]),
                        "ask": float(snapshot["ask"]),
                    },
                    "closedM1": rows,
                }
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("a", encoding="utf-8", newline="\n") as handle:
                    handle.write(json.dumps(record, separators=(",", ":")) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                self._stop.wait(self.poll_seconds)
        except Exception as exc:  # fail closed in the caller after join
            self._error = exc

    def after_request(self, context: dict[str, Any]) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=max(2.0, self.poll_seconds * 4.0))
        self._thread = None
        if self._error is not None:
            raise V4ContractError(f"REQUEST_MARKET_BUFFER_FAILED:{self._error}")


def normalize_volume(account: dict[str, Any], requested: float | None = None) -> float:
    minimum = float(account["volumeMin"])
    maximum = float(account["volumeMax"])
    step = float(account["volumeStep"])
    raw = minimum if requested is None else float(requested)
    steps = round((max(minimum, min(maximum, raw)) - minimum) / step)
    return round(minimum + steps * step, 8)


class DemoOrderRouter:
    """Idempotent DEMO-only bridge from frozen local orders to MT5 pending orders."""

    def __init__(
        self, feed: ClosedM1Feed, account: dict[str, Any], *, enabled: bool
    ) -> None:
        assert_demo_order_gate(account, enabled)
        self.feed = feed
        self.account = account
        self.enabled = bool(enabled)

    def sync(self, runtime: dict[str, Any]) -> dict[str, int]:
        if not self.enabled:
            return {"submitted": 0, "canceled": 0, "reconciled": 0}
        snapshot = self.feed.broker_snapshot()
        broker_by_id = {
            str(item["comment"]): {**item, "kind": kind}
            for kind in ("orders", "positions")
            for item in snapshot.get(kind, [])
            if str(item.get("comment", "")).startswith("MENTOR-")
        }
        local_records = {
            str(item["orderId"]): item for item in runtime.get("orders", [])
        }
        slots = {
            str(item.get("order", {}).get("orderId")): item
            for item in runtime.get("scenarioSlots", [])
            if isinstance(item.get("order"), dict)
        }
        submitted = canceled = reconciled = 0
        for order_id, record in local_records.items():
            client_id = str(record.get("clientId") or f"MENTOR-{order_id}")[:31]
            record["clientId"] = client_id
            broker = broker_by_id.get(client_id)
            status = str(record.get("status"))
            if status == "PENDING" and broker is None:
                slot = slots.get(order_id)
                if slot is None:
                    raise V4ContractError("DEMO_ROUTER_PENDING_ORDER_HAS_NO_SLOT")
                result = self.feed.submit_pending(
                    slot["order"], normalize_volume(self.account), client_id
                )
                record.update({
                    "brokerSubmitted": True,
                    "brokerTicket": int(result["ticket"]),
                    "brokerStatus": "PENDING",
                })
                submitted += 1
            elif status == "CANCELED" and broker is not None and broker["kind"] == "orders":
                self.feed.cancel_pending(int(broker["ticket"]), client_id)
                record.update({"brokerStatus": "CANCELED", "brokerSubmitted": False})
                canceled += 1
            elif broker is not None:
                record.update({
                    "brokerSubmitted": True,
                    "brokerTicket": int(broker["ticket"]),
                    "brokerStatus": "FILLED" if broker["kind"] == "positions" else "PENDING",
                })
                reconciled += 1
        return {"submitted": submitted, "canceled": canceled, "reconciled": reconciled}


def validate_feed_clock(
    snapshot: dict[str, Any],
    *,
    local_now: int,
    stale_seconds: int,
    max_clock_skew_seconds: int,
) -> tuple[bool, str | None]:
    server_now = int(snapshot["serverNow"])
    age = local_now - server_now
    if age > stale_seconds:
        return False, f"STALE_MARKET_DATA age={age}s"
    if age < -max_clock_skew_seconds:
        return False, f"CLOCK_SKEW serverAhead={-age}s"
    return True, None


def resolve_broker_utc_offset(
    *,
    raw_server_now: int,
    local_now: int,
    max_clock_skew_seconds: int,
    previous_offset_seconds: int | None = None,
) -> int:
    raw_delta = int(raw_server_now) - int(local_now)
    candidate = int(round(raw_delta / 3600.0)) * 3600
    if abs(candidate) <= 14 * 3600 and abs(raw_delta - candidate) <= max_clock_skew_seconds:
        return candidate
    if previous_offset_seconds is not None:
        return int(previous_offset_seconds)
    raise V4ContractError(
        f"cannot resolve broker UTC offset: rawDelta={raw_delta}s"
    )


def normalize_broker_time(
    rates: np.ndarray,
    snapshot: dict[str, Any],
    offset_seconds: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    normalized = rates.copy()
    normalized["time"] = normalized["time"].astype(np.int64) - int(offset_seconds)
    return normalized, {
        **snapshot,
        "rawServerNow": int(snapshot["serverNow"]),
        "serverNow": int(snapshot["serverNow"]) - int(offset_seconds),
        "brokerUtcOffsetSeconds": int(offset_seconds),
    }


def assert_demo_order_gate(account: dict[str, Any], enable_demo_orders: bool) -> None:
    if not enable_demo_orders:
        return
    if int(account["tradeMode"]) != int(account["demoTradeMode"]):
        raise V4ContractError("demo order mode refused: connected account is not DEMO")
    if not bool(account["terminalConnected"]) or not bool(account["tradeAllowed"]):
        raise V4ContractError("demo order mode refused: MT5 trading is not allowed")


def reconcile_broker_snapshot(
    runtime: dict[str, Any], snapshot: dict[str, Any]
) -> dict[str, Any]:
    """Fail closed on any Mentor-owned broker/local identity disagreement."""
    broker_records = [
        {**item, "kind": kind}
        for kind in ("orders", "positions")
        for item in snapshot.get(kind, [])
        if str(item.get("comment", "")).startswith("MENTOR-")
    ]
    broker_ids = [str(item["comment"]) for item in broker_records]
    if len(broker_ids) != len(set(broker_ids)):
        raise V4ContractError("BROKER_RECONCILIATION_DUPLICATE_CLIENT_ID")
    local_records = [
        item for item in runtime.get("orders", [])
        if bool(item.get("brokerSubmitted"))
        and str(item.get("status")) in {"PENDING", "FILLED"}
    ]
    local_by_id = {
        str(item["clientId"]): item for item in local_records
    }
    if len(local_by_id) != len(local_records):
        raise V4ContractError("LOCAL_RECONCILIATION_DUPLICATE_CLIENT_ID")
    unknown = sorted(set(broker_ids) - set(local_by_id))
    missing = sorted(set(local_by_id) - set(broker_ids))
    if unknown:
        raise V4ContractError(
            "BROKER_RECONCILIATION_UNKNOWN_MENTOR_ORDER:" + ",".join(unknown)
        )
    if missing:
        raise V4ContractError(
            "BROKER_RECONCILIATION_LOCAL_ORDER_MISSING:" + ",".join(missing)
        )
    result = {
        "status": "MATCHED",
        "brokerMentorRecords": len(broker_records),
        "localSubmittedRecords": len(local_records),
        "snapshotHash": canonical_hash(broker_records),
        "checkedAtUtc": utc_text(int(time.time())),
    }
    runtime["brokerReconciliation"] = result
    return result


def truncate_file(path: Path, size: int) -> None:
    if not path.exists():
        return
    with path.open("r+b") as handle:
        handle.truncate(max(0, int(size)))


def recover_interrupted_bar(run_dir: Path) -> bool:
    checkpoint_path = run_dir / CHECKPOINT_NAME
    if not checkpoint_path.exists():
        return False
    checkpoint = read_json(checkpoint_path)
    current_state_path = run_dir / "state.json"
    current = read_json(current_state_path) if current_state_path.exists() else {}
    restored = copy.deepcopy(checkpoint["runtimeBefore"])
    restored.setdefault("inFlightRequests", {}).update(
        current.get("inFlightRequests", {})
    )
    truncate_file(run_dir / "decision_ledger.jsonl", int(checkpoint["ledgerBytes"]))
    truncate_file(run_dir / "trades.jsonl", int(checkpoint["tradesBytes"]))
    atomic_json(run_dir / "state.json", restored)
    checkpoint_path.unlink()
    return True


def begin_bar_transaction(runner: V4Runner, row: dict[str, Any]) -> Path:
    path = runner.run_dir / CHECKPOINT_NAME
    atomic_json(
        path,
        {
            "barId": row["barId"],
            "runtimeBefore": copy.deepcopy(runner.runtime),
            "ledgerBytes": (runner.run_dir / "decision_ledger.jsonl").stat().st_size
            if (runner.run_dir / "decision_ledger.jsonl").exists() else 0,
            "tradesBytes": (runner.run_dir / "trades.jsonl").stat().st_size
            if (runner.run_dir / "trades.jsonl").exists() else 0,
        },
    )
    return path


def process_closed_bars(
    runner: V4Runner,
    *,
    server_now: int,
    daily_plan_limit: int,
) -> int:
    processed = 0
    total = len(runner.market.rates)
    while int(runner.runtime["cursor"]) < total:
        index = int(runner.runtime["cursor"])
        row = runner.market.m1_row(index)
        if int(row["available"]) > int(server_now):
            break
        checkpoint = begin_bar_transaction(runner, row)
        try:
            utc_day = datetime.fromtimestamp(
                row["available"], timezone.utc
            ).date().isoformat()
            live_day = runner.runtime.setdefault(
                "liveDailyPlanCalls", {"utcDay": utc_day, "count": 0}
            )
            if live_day.get("utcDay") != utc_day:
                live_day.update({"utcDay": utc_day, "count": 0})
                runner.segment_provider_call_base = int(runner.stats["providerApiCalls"])
                runner.segment_token_base = int(runner.stats["totalTokens"])
            allowed = int(live_day["count"]) < int(daily_plan_limit)
            result = runner.advance_closed_m1_bar(
                row,
                planning_enabled=True,
                api_allowed=allowed,
            )
            live_day["count"] += int(result["planRequests"])
            if not allowed:
                runner.event(
                    "LIVE_PLAN_DAILY_LIMIT",
                    row["available"],
                    {"limit": daily_plan_limit, "apiCalled": False},
                )
            runner.save()
            checkpoint.unlink(missing_ok=True)
            processed += 1
        except GeminiReplayError:
            # Provider failures happen before a semantic state transition. Preserve
            # charged usage and retry the same closed bar after the circuit pause.
            runner.save()
            checkpoint.unlink(missing_ok=True)
            raise
        except Exception:
            # Keep the checkpoint. The next process restores the exact pre-bar
            # state and truncates partial ledger/trade writes before retrying.
            raise
    return processed


def local_wait_events(state: str) -> str:
    """Describe the next locally observed event without invoking a model."""
    return {
        "FLAT": "NEXT_H1_PLAN_EVIDENCE",
        "PLANNED": "CHILD_TOUCH|OBJECTIVE|SOURCE_INVALIDATION",
        "REACTION_MONITOR": "MATURE_SWEEP|BODY_CHOCH",
        "TRIGGER_WATCH": "EXECUTION_OB|FIRST_RETEST",
        "PENDING": "FILL|LOCAL_CANCEL",
        "FILLED": "SL|TP",
    }.get(str(state), "FAIL_CLOSED")


def load_archive(path: Path) -> np.ndarray | None:
    if not path.exists():
        return None
    with np.load(path, allow_pickle=False) as payload:
        return payload["rates"]


def run_live(args: argparse.Namespace, feed: ClosedM1Feed | None = None) -> int:
    api_key, config = load_secret()
    symbol = str(args.symbol or config["symbol"])
    run_id = str(args.run_id or f"live_{symbol}_{datetime.now(timezone.utc).strftime('%Y%m%d')}")
    run_dir = LIVE_ROOT / run_id
    archive_path = LIVE_DATA_ROOT / f"{symbol}_M1_live.npz"
    clock_path = LIVE_DATA_ROOT / f"{symbol}_broker_clock.json"
    feed = feed or Mt5ClosedM1Feed(symbol)
    account = feed.connect()
    assert_demo_order_gate(account, bool(args.enable_demo_orders))
    try:
        incoming, snapshot = feed.closed_rates(int(args.history_bars))
        previous_clock = read_json(clock_path) if clock_path.exists() else {}
        offset = resolve_broker_utc_offset(
            raw_server_now=int(snapshot["serverNow"]),
            local_now=int(time.time()),
            max_clock_skew_seconds=int(args.max_clock_skew_seconds),
            previous_offset_seconds=previous_clock.get("brokerUtcOffsetSeconds"),
        )
        incoming, snapshot = normalize_broker_time(incoming, snapshot, offset)
        existing_archive = load_archive(archive_path)
        backfill_bars_used = int(args.history_bars)
        if (
            existing_archive is not None and len(existing_archive)
            and int(incoming[0]["time"]) > int(existing_archive[-1]["time"])
        ):
            incoming, snapshot, backfill_bars_used = adaptive_backfill(
                feed,
                existing_archive,
                initial_bars=int(args.history_bars),
                maximum_bars=int(args.maximum_backfill_bars),
                offset_seconds=offset,
            )
        atomic_json(
            clock_path,
            {
                "symbol": symbol,
                "server": account["server"],
                "brokerUtcOffsetSeconds": offset,
                "observedAtUtc": utc_text(int(time.time())),
            },
        )
        healthy, reason = validate_feed_clock(
            snapshot,
            local_now=int(time.time()),
            stale_seconds=int(args.stale_seconds),
            max_clock_skew_seconds=int(args.max_clock_skew_seconds),
        )
        if not healthy:
            print(f"[LIVE PAUSED] {reason}", flush=True)
        rates = merge_rates(existing_archive, incoming)
        save_rate_cache(
            archive_path,
            rates,
            {"provider": "MetaTrader5-live", "symbol": symbol, "timeframe": "M1"},
        )
        config = {
            **config,
            "provider": "gemini",
            "symbol": symbol,
            "dataset": str(archive_path.resolve()),
            "point": float(account["point"]),
            "brokerStopsLevelPrice": float(account["tradeStopsLevel"]) * float(account["point"]),
            "brokerSpecResolved": True,
            "maximumApiCallsPerRun": int(args.maximum_api_calls_per_day),
            "maximumTokensPerRun": int(args.maximum_tokens_per_day),
            "applyLiveLatencyClock": True,
            "brokerOrderLatencyMs": int(args.broker_order_latency_ms),
        }
        market = MarketData.from_rates(rates, float(config["point"]))
        if args.preflight_only:
            print("MENTOR_AI_LIVE_V4_PREFLIGHT_OK")
            print(
                f"symbol={symbol} bars={len(rates)} point={config['point']} "
                f"stopsLevelPrice={config['brokerStopsLevelPrice']} healthy={healthy} "
                f"backfillBars={backfill_bars_used}"
            )
            print(f"archive={archive_path.resolve()}")
            return 0
        run_dir.mkdir(parents=True, exist_ok=True)
        recovered = recover_interrupted_bar(run_dir)
        state_path = run_dir / "state.json"
        resumed_state = state_path.exists()
        manifest_path = run_dir / "manifest.json"
        live_identity = {
            "pipelineVersion": PIPELINE_VERSION,
            "symbol": symbol,
            "agentsSha256": sha256_file(ROOT / "AGENTS.md"),
            "contractsManifestSha256": sha256_file(V4_MANIFEST),
            "runnerSha256": sha256_file(RUNNER_PATH),
            "coreSha256": sha256_file(CORE_PATH),
            "rendererSha256": sha256_file(RENDERER_PATH),
        }
        if manifest_path.exists():
            manifest = read_json(manifest_path)
            mismatched = [
                key for key, value in live_identity.items()
                if manifest.get(key) != value
            ]
            if mismatched:
                raise V4ContractError(
                    "live resume rules/code changed; start a new run-id: "
                    + ",".join(mismatched)
                )
            old_account = manifest.get("account", {})
            if int(old_account.get("login", -1)) != int(account["login"]):
                raise V4ContractError("live resume account changed; start a new run-id")
        if state_path.exists():
            runtime = read_json(state_path)
            if runtime.get("pipelineVersion") != PIPELINE_VERSION:
                raise V4ContractError("live runtime pipeline version changed")
        else:
            runtime = new_runtime(len(rates))
            atomic_json(
                manifest_path,
                {
                    **live_identity,
                    "mode": "DEMO_ORDER" if args.enable_demo_orders else "LIVE_SHADOW",
                    "runId": run_id,
                    "symbol": symbol,
                    "createdAtUtc": utc_text(int(time.time())),
                    "account": {k: account[k] for k in ("login", "server", "tradeMode")},
                    "config": {key: value for key, value in config.items() if key != "apiKey"},
                    "systemInstructionsSha256": canonical_hash(system_instruction_evidence(config)),
                },
            )
        key_pool, _ = load_secret_pool(int(config.get("apiKeySlot", 1)))
        provider = GeminiProvider(key_pool, config)
        runner = V4Runner(
            config=config,
            market=market,
            run_dir=run_dir,
            provider=provider,
            runtime=runtime,
            request_observer=LiveRequestBuffer(
                feed,
                run_dir,
                offset_seconds=offset,
                poll_seconds=float(args.request_buffer_poll_seconds),
                poll_bars=int(args.request_buffer_bars),
            ),
        )
        demo_router = DemoOrderRouter(
            feed, account, enabled=bool(args.enable_demo_orders)
        )
        broker_reader = getattr(feed, "broker_snapshot", None)
        if broker_reader is None:
            raise V4ContractError("live feed does not provide broker reconciliation")
        reconcile_broker_snapshot(runner.runtime, broker_reader())
        runner.save()
        if not state_path.exists() and healthy:
            # Startup is not a semantic event. A full-map PLAN is allowed only
            # for a new closed H1 evidence set; it is never driven by continuous
            # price observation or parent-root proximity.
            startup_row = runner.market.m1_row(len(rates) - 1)
            startup_day = datetime.fromtimestamp(
                startup_row["available"], timezone.utc
            ).date().isoformat()
            runner.runtime["liveDailyPlanCalls"] = {
                "utcDay": startup_day,
                "count": 0,
            }
            allowed = int(args.maximum_plan_calls_per_day) > 0
            before = int(runner.stats["planRequests"])
            runner.schedule_flat_plan(
                int(startup_row["available"]), api_allowed=allowed
            )
            runner.runtime["liveDailyPlanCalls"]["count"] += (
                int(runner.stats["planRequests"]) - before
            )
            runner.save()
        print(
            f"[LIVE READY] mode=SHADOW symbol={symbol} state={runner.runtime['state']} "
            f"resumed={resumed_state} recoveredInterruptedBar={recovered} "
            f"lastClosed={utc_text(int(rates[-1]['time']) + 60)} "
            f"waiting={local_wait_events(str(runner.runtime['state']))} "
            "waitingTokens=0",
            flush=True,
        )
        provider_pause_seconds = 60.0
        while True:
            incoming, snapshot = feed.closed_rates(int(args.poll_bars))
            offset = resolve_broker_utc_offset(
                raw_server_now=int(snapshot["serverNow"]),
                local_now=int(time.time()),
                max_clock_skew_seconds=int(args.max_clock_skew_seconds),
                previous_offset_seconds=offset,
            )
            incoming, snapshot = normalize_broker_time(incoming, snapshot, offset)
            healthy, reason = validate_feed_clock(
                snapshot,
                local_now=int(time.time()),
                stale_seconds=int(args.stale_seconds),
                max_clock_skew_seconds=int(args.max_clock_skew_seconds),
            )
            if not healthy:
                print(f"[LIVE PAUSED] {reason}; no API and no order", flush=True)
                if args.once:
                    break
                time.sleep(float(args.poll_seconds))
                continue
            merged = merge_rates(rates, incoming)
            if len(merged) != len(rates):
                rates = merged
                save_rate_cache(
                    archive_path,
                    rates,
                    {"provider": "MetaTrader5-live", "symbol": symbol, "timeframe": "M1"},
                )
                runner.market = MarketData.from_rates(rates, float(config["point"]))
            try:
                processed = process_closed_bars(
                    runner,
                    server_now=int(snapshot["serverNow"]),
                    daily_plan_limit=int(args.maximum_plan_calls_per_day),
                )
            except GeminiReplayError as exc:
                print(
                    f"[LIVE API PAUSED] {exc}; state preserved, retry in "
                    f"{provider_pause_seconds:.0f}s; no order",
                    flush=True,
                )
                if args.once:
                    break
                time.sleep(provider_pause_seconds)
                provider.quota_disabled_models.clear()
                provider_pause_seconds = min(3600.0, provider_pause_seconds * 2.0)
                continue
            provider_pause_seconds = 60.0
            demo_result = demo_router.sync(runner.runtime)
            reconcile_broker_snapshot(runner.runtime, broker_reader())
            runner.save()
            if processed:
                write_trades_csv(run_dir, runner.trades)
                print(
                    f"[LIVE] {utc_text(int(snapshot['serverNow']))} bars={processed} "
                    f"state={runner.runtime['state']} api={runner.stats['providerApiCalls']} "
                    f"tokens={runner.stats['totalTokens']} trades={len(runner.trades)} "
                    f"demoSubmitted={demo_result['submitted']} "
                    f"waiting={local_wait_events(str(runner.runtime['state']))} "
                    "waitingTokens=0",
                    flush=True,
                )
            if args.once:
                break
            time.sleep(float(args.poll_seconds))
    finally:
        feed.shutdown()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MT5 closed-M1 Mentor AI V4 live shadow observer")
    parser.add_argument("--run-id")
    parser.add_argument("--symbol")
    parser.add_argument("--history-bars", type=int, default=160000)
    parser.add_argument("--maximum-backfill-bars", type=int, default=2000000)
    parser.add_argument("--poll-bars", type=int, default=240)
    parser.add_argument("--poll-seconds", type=float, default=5.0)
    parser.add_argument("--request-buffer-poll-seconds", type=float, default=1.0)
    parser.add_argument("--request-buffer-bars", type=int, default=8)
    parser.add_argument("--stale-seconds", type=int, default=180)
    parser.add_argument("--max-clock-skew-seconds", type=int, default=30)
    parser.add_argument("--maximum-plan-calls-per-day", type=int, default=12)
    parser.add_argument("--maximum-api-calls-per-day", type=int, default=20)
    parser.add_argument("--maximum-tokens-per-day", type=int, default=350000)
    parser.add_argument("--broker-order-latency-ms", type=int, default=250)
    parser.add_argument("--enable-demo-orders", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--once", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return run_live(args)
    except (GeminiReplayError, V4ContractError, OSError, ValueError) as exc:
        print(f"MENTOR_AI_LIVE_V4_FAIL_CLOSED: {type(exc).__name__}: {exc}", flush=True)
        match = re.search(r"retry in ([0-9.]+)s", str(exc), flags=re.IGNORECASE)
        if match:
            print(f"providerRetryAfterSeconds={match.group(1)}", flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
