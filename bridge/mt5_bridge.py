from __future__ import annotations

import json
import importlib
import math
import os
import re
import base64
import csv
import io
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Event, Lock, Thread
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse
from zoneinfo import ZoneInfo
from scripts.ai_feedback_provider import (
    ai_feedback_provider_payload,
    read_ai_feedback_config,
    write_ai_feedback_config,
)

try:
    import MetaTrader5 as mt5
except Exception as exc:  # pragma: no cover - depends on local Windows MT5 setup.
    mt5 = None
    MT5_IMPORT_ERROR = str(exc)
else:
    MT5_IMPORT_ERROR = ""

try:
    import numpy as np
except Exception as exc:  # pragma: no cover - workspace dependency.
    np = None
    NUMPY_IMPORT_ERROR = str(exc)
else:
    NUMPY_IMPORT_ERROR = ""


HOST = os.environ.get("MT5_BRIDGE_HOST", "0.0.0.0")
PORT = int(os.environ.get("MT5_BRIDGE_PORT", "8765"))
DATA_DIR = Path(os.environ.get("TRADING_JOURNAL_DATA_DIR", Path(__file__).resolve().parents[1] / "data"))
LOG_DIR = Path(os.environ.get("TRADING_JOURNAL_LOG_DIR", Path(__file__).resolve().parents[1] / "logs"))
JOURNAL_FILE = Path(os.environ.get("TRADING_JOURNAL_FILE", DATA_DIR / "journal.json"))
LOCAL_APP_DATA = Path(os.environ.get("LOCALAPPDATA", str(DATA_DIR)))
JOURNAL_DB_FILE = Path(os.environ.get("TRADING_JOURNAL_DB", LOCAL_APP_DATA / "TradingJournal" / "journal.db"))
EA_EXPORT_DIR = os.environ.get("MT5_JOURNAL_EA_DIR")
EA_EVENT_FILE = os.environ.get("MT5_JOURNAL_EA_EVENT_FILE", "events.jsonl")
EA_EVENT_CSV_FILE = os.environ.get("MT5_JOURNAL_EA_EVENT_CSV_FILE", "events.csv")
MAX_SCREENSHOT_BYTES = int(os.environ.get("MT5_JOURNAL_MAX_SCREENSHOT_BYTES", str(5 * 1024 * 1024)))
EA_WATCH_INTERVAL_SECONDS = float(os.environ.get("MT5_JOURNAL_WATCH_INTERVAL_SECONDS", "5"))
LIVE_WATCH_INTERVAL_SECONDS = float(os.environ.get("MT5_LIVE_WATCH_INTERVAL_SECONDS", "1"))
HISTORY_BACKFILL_INTERVAL_SECONDS = float(os.environ.get("MT5_HISTORY_BACKFILL_INTERVAL_SECONDS", "30"))
EA_HEARTBEAT_STALE_SECONDS = float(os.environ.get("MT5_EA_HEARTBEAT_STALE_SECONDS", "120"))
MT5_SERVER_TZ = ZoneInfo(os.environ.get("MT5_SERVER_TZ", "Etc/GMT-3"))
MT5_BRIDGE_AUTO_LAUNCH = os.environ.get("MT5_BRIDGE_AUTO_LAUNCH", "0").strip().lower() in {"1", "true", "yes", "on"}
JOURNAL_LOCK = Lock()
JOURNAL_DB_READY = False
EA_WATCH_STOP = Event()
LIVE_WATCH_STOP = Event()
HISTORY_WATCH_STOP = Event()
CLIENT_ERROR_FILE = LOG_DIR / "client-errors.jsonl"
SL_TP_COMMENT_PATTERN = re.compile(r"\[(sl|tp)\s+([0-9]+(?:\.[0-9]+)?)\]", re.IGNORECASE)
AI_FEEDBACK_JOB_LOCK = Lock()
AI_FEEDBACK_JOBS: dict[str, dict[str, Any]] = {}
AI_FEEDBACK_ACTIVE_JOB_ID = ""
REPLAY_DATASET_DIR = Path(
    os.environ.get("TRADING_REPLAY_DATASET_DIR", Path(__file__).resolve().parents[1] / "output" / "datasets")
)
REPLAY_MAX_BARS = int(os.environ.get("TRADING_REPLAY_MAX_BARS", "40000"))
REPLAY_SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
AUTO_THESIS_TEXTS = {
    "MT5 청산 거래 자동 가져오기",
    "MT5 현재 포지션 자동 불러오기",
}
BROKEN_EMOTION_TEXTS = {"???", "李⑤텇??"}
AUTO_THESIS_PREFIXES = ("MT5 comment:",)


def to_jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "item"):
        return value.item()
    return str(value)


def as_dict(row: Any) -> dict[str, Any]:
    if hasattr(row, "_asdict"):
        return {key: to_jsonable(value) for key, value in row._asdict().items()}
    if isinstance(row, dict):
        return {key: to_jsonable(value) for key, value in row.items()}
    dtype = getattr(row, "dtype", None)
    names = getattr(dtype, "names", None)
    if names:
        return {key: to_jsonable(row[key]) for key in names}
    return {}


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def account_value(account: dict[str, Any]) -> float:
    balance = as_float(account.get("balance"))
    equity = as_float(account.get("equity"))
    if balance > 0:
        return balance
    if equity > 0:
        return equity
    return max(abs(balance), abs(equity), 0.0)


def iso_from_seconds(value: Any) -> str:
    seconds = as_int(value)
    if seconds <= 0:
        return ""
    return datetime.fromtimestamp(seconds, tz=timezone.utc).astimezone().isoformat(timespec="seconds")


def date_from_iso(value: str) -> str:
    return value[:10] if value else datetime.now().date().isoformat()


def parse_since(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone()
    except ValueError:
        return None


def imported_trade_time(trade: dict[str, Any]) -> datetime | None:
    for key in ("closeTime", "openTime", "updatedAt", "createdAt", "date"):
        parsed = parse_since(trade.get(key))
        if parsed is not None:
            return parsed
    broker_meta = trade.get("brokerMeta")
    if isinstance(broker_meta, dict):
        for key in ("closeTime", "openTime"):
            parsed = parse_since(broker_meta.get(key))
            if parsed is not None:
                return parsed
    return None


def filter_trades_since(trades: list[dict[str, Any]], since: datetime | None) -> list[dict[str, Any]]:
    if since is None:
        return trades
    return [trade for trade in trades if (imported_trade_time(trade) or datetime.min.replace(tzinfo=since.tzinfo)) > since]


def journal_trade_sort_key(trade: dict[str, Any]) -> str:
    broker_meta = trade.get("brokerMeta")
    if isinstance(broker_meta, dict):
        for key in ("closeTime", "openTime"):
            value = str(broker_meta.get(key) or "")
            if value:
                return value
    return str(trade.get("date") or trade.get("createdAt") or "")


def latest_journal_trade_time() -> datetime | None:
    payload = journal_payload()
    trades = payload.get("trades") if isinstance(payload, dict) else []
    if not isinstance(trades, list):
        return None
    times = [imported_trade_time(trade) for trade in trades if isinstance(trade, dict)]
    valid_times = [value for value in times if value is not None]
    if not valid_times:
        return None
    return max(valid_times) - timedelta(seconds=60)


def weighted_average(rows: list[dict[str, Any]], value_key: str, weight_key: str) -> float:
    weighted = sum(as_float(row.get(value_key)) * as_float(row.get(weight_key)) for row in rows)
    weight = sum(as_float(row.get(weight_key)) for row in rows)
    return weighted / weight if weight else 0.0


def sl_tp_from_comment(value: Any) -> tuple[float, float]:
    stop_price = 0.0
    target_price = 0.0
    for key, price in SL_TP_COMMENT_PATTERN.findall(str(value or "")):
        if key.lower() == "sl":
            stop_price = as_float(price)
        if key.lower() == "tp":
            target_price = as_float(price)
    return stop_price, target_price


def floor_to_step(value: float, step: float) -> float:
    if step <= 0:
        return value
    return math.floor((value + 1e-12) / step) * step


def journal_updated_at() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def trade_storage_id(trade: dict[str, Any]) -> str:
    return str(trade.get("id") or trade.get("externalId") or f"trade:{time.time_ns()}")


def review_storage_id(review: dict[str, Any]) -> str:
    return str(review.get("periodKey") or review.get("id") or f"review:{time.time_ns()}")


def connect_journal_db() -> sqlite3.Connection:
    ensure_journal_db()
    connection = sqlite3.connect(JOURNAL_DB_FILE, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout=30000")
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=NORMAL")
    return connection


def create_journal_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS trades (
            id TEXT PRIMARY KEY,
            external_id TEXT,
            updated_at TEXT NOT NULL,
            sort_time TEXT NOT NULL,
            data TEXT NOT NULL
        )
        """
    )
    connection.execute("CREATE INDEX IF NOT EXISTS idx_trades_external_id ON trades(external_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_trades_sort_time ON trades(sort_time)")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reviews (
            id TEXT PRIMARY KEY,
            period_key TEXT,
            updated_at TEXT NOT NULL,
            sort_time TEXT NOT NULL,
            data TEXT NOT NULL
        )
        """
    )
    connection.execute("CREATE INDEX IF NOT EXISTS idx_reviews_period_key ON reviews(period_key)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_reviews_sort_time ON reviews(sort_time)")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS replay_sessions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            symbol TEXT NOT NULL,
            dataset TEXT NOT NULL,
            week_start INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            data TEXT NOT NULL
        )
        """
    )
    connection.execute("CREATE INDEX IF NOT EXISTS idx_replay_sessions_updated_at ON replay_sessions(updated_at)")


def upsert_trade_rows(connection: sqlite3.Connection, trades: list[Any], updated_at: str) -> None:
    for trade in trades:
        if not isinstance(trade, dict):
            continue
        trade_id = trade_storage_id(trade)
        trade["id"] = trade_id
        external_id = str(trade.get("externalId") or "")
        sort_time = journal_trade_sort_key(trade)
        connection.execute(
            """
            INSERT INTO trades (id, external_id, updated_at, sort_time, data)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                external_id=excluded.external_id,
                updated_at=excluded.updated_at,
                sort_time=excluded.sort_time,
                data=excluded.data
            """,
            (trade_id, external_id, updated_at, sort_time, json.dumps(trade, ensure_ascii=False)),
        )


def upsert_review_rows(connection: sqlite3.Connection, reviews: list[Any], updated_at: str) -> None:
    for review in reviews:
        if not isinstance(review, dict):
            continue
        review_id = review_storage_id(review)
        review["id"] = str(review.get("id") or review_id)
        period_key = str(review.get("periodKey") or "")
        sort_time = str(review.get("startDate") or review.get("updatedAt") or updated_at)
        connection.execute(
            """
            INSERT INTO reviews (id, period_key, updated_at, sort_time, data)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                period_key=excluded.period_key,
                updated_at=excluded.updated_at,
                sort_time=excluded.sort_time,
                data=excluded.data
            """,
            (review_id, period_key, updated_at, sort_time, json.dumps(review, ensure_ascii=False)),
        )


def migrate_json_journal(connection: sqlite3.Connection) -> None:
    trade_count = connection.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
    review_count = connection.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    if trade_count or review_count or not JOURNAL_FILE.exists():
        return

    try:
        payload = json.loads(JOURNAL_FILE.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return

    if not isinstance(payload, dict):
        return
    trades = payload.get("trades") if isinstance(payload.get("trades"), list) else []
    reviews = payload.get("reviews") if isinstance(payload.get("reviews"), list) else []
    updated_at = str(payload.get("updatedAt") or journal_updated_at())
    upsert_trade_rows(connection, trades, updated_at)
    upsert_review_rows(connection, reviews, updated_at)
    connection.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('updatedAt', ?)", (updated_at,))


def ensure_journal_db() -> None:
    global JOURNAL_DB_READY
    if JOURNAL_DB_READY:
        return
    JOURNAL_DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(JOURNAL_DB_FILE, timeout=30)
    try:
        connection.execute("PRAGMA busy_timeout=30000")
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        create_journal_schema(connection)
        migrate_json_journal(connection)
        connection.commit()
    finally:
        connection.close()
    JOURNAL_DB_READY = True


def load_journal_from_db() -> dict[str, Any]:
    with connect_journal_db() as connection:
        trades = [
            json.loads(row["data"])
            for row in connection.execute("SELECT data FROM trades ORDER BY sort_time DESC, updated_at DESC")
        ]
        reviews = [
            json.loads(row["data"])
            for row in connection.execute("SELECT data FROM reviews ORDER BY sort_time DESC, updated_at DESC")
        ]
        meta = connection.execute("SELECT value FROM meta WHERE key='updatedAt'").fetchone()

    return {
        "ok": True,
        "trades": trades,
        "reviews": reviews,
        "updatedAt": str(meta["value"] if meta else ""),
        "storage": str(JOURNAL_DB_FILE),
        "legacyStorage": str(JOURNAL_FILE),
    }


def journal_payload() -> dict[str, Any]:
    with JOURNAL_LOCK:
        try:
            return load_journal_from_db()
        except (OSError, sqlite3.Error, json.JSONDecodeError) as exc:
            return {
                "ok": False,
                "error": f"Journal DB error: {exc}",
                "trades": [],
                "reviews": [],
                "storage": str(JOURNAL_DB_FILE),
                "legacyStorage": str(JOURNAL_FILE),
            }


def review_has_content(review: Any) -> bool:
    if not isinstance(review, dict):
        return False
    for key in ("good", "bad", "lesson", "nextPlan"):
        if str(review.get(key) or "").strip():
            return True
    return False


def save_journal(payload: dict[str, Any]) -> dict[str, Any]:
    trades = payload.get("trades")
    if not isinstance(trades, list):
        raise RuntimeError("Journal payload must include a trades array.")
    reviews = payload.get("reviews", [])
    if not isinstance(reviews, list):
        reviews = []

    existing_trades: list[Any] = []
    existing_reviews: list[Any] = []
    existing_payload = journal_payload()
    if isinstance(existing_payload, dict):
        if isinstance(existing_payload.get("trades"), list):
            existing_trades = existing_payload["trades"]
        if isinstance(existing_payload.get("reviews"), list):
            existing_reviews = existing_payload["reviews"]

    if existing_trades:
        existing_by_external_id = {
            str(trade.get("externalId")): trade
            for trade in existing_trades
            if isinstance(trade, dict) and trade.get("externalId")
        }
        existing_by_id = {
            str(trade.get("id")): trade
            for trade in existing_trades
            if isinstance(trade, dict) and trade.get("id")
        }
        merged_trades: list[Any] = []
        seen_existing_ids: set[int] = set()
        for incoming in trades:
            if not isinstance(incoming, dict):
                merged_trades.append(incoming)
                continue
            existing = existing_by_external_id.get(str(incoming.get("externalId") or "")) or existing_by_id.get(str(incoming.get("id") or ""))
            if isinstance(existing, dict):
                merged = merge_journal_trade(existing, incoming)
                seen_existing_ids.add(id(existing))
                merged_trades.append(merged)
            else:
                merged_trades.append(incoming)

        incoming_keys = {
            str(trade.get("externalId") or trade.get("id") or "")
            for trade in trades
            if isinstance(trade, dict)
        }
        for existing in existing_trades:
            if not isinstance(existing, dict):
                continue
            key = str(existing.get("externalId") or existing.get("id") or "")
            if id(existing) not in seen_existing_ids and key not in incoming_keys:
                merged_trades.append(existing)
        trades = merged_trades

    existing_content_count = sum(1 for review in existing_reviews if review_has_content(review))
    incoming_content_count = sum(1 for review in reviews if review_has_content(review))
    if existing_reviews and (len(reviews) < len(existing_reviews) or incoming_content_count < existing_content_count):
        existing_by_key = {
            str(review.get("periodKey") or review.get("id") or ""): review
            for review in existing_reviews
            if isinstance(review, dict)
        }
        incoming_by_key = {
            str(review.get("periodKey") or review.get("id") or ""): review
            for review in reviews
            if isinstance(review, dict)
        }
        merged_by_key = {**incoming_by_key}
        for key, existing_review in existing_by_key.items():
            incoming_review = incoming_by_key.get(key)
            if not incoming_review or (review_has_content(existing_review) and not review_has_content(incoming_review)):
                merged_by_key[key] = existing_review
        reviews = list(merged_by_key.values())

    updated_at = journal_updated_at()
    document = {
        "ok": True,
        "updatedAt": updated_at,
        "trades": trades,
        "reviews": reviews,
    }

    with JOURNAL_LOCK:
        with connect_journal_db() as connection:
            connection.execute("BEGIN IMMEDIATE")
            upsert_trade_rows(connection, trades, updated_at)
            upsert_review_rows(connection, reviews, updated_at)
            connection.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('updatedAt', ?)", (updated_at,))
            connection.commit()

    return {
        **document,
        "storage": str(JOURNAL_DB_FILE),
        "legacyStorage": str(JOURNAL_FILE),
    }


def patch_trade_payload(trade_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    if not trade_id:
        raise RuntimeError("Trade id is required.")
    if not isinstance(patch, dict):
        raise RuntimeError("Trade patch must be an object.")

    updated_at = journal_updated_at()
    with JOURNAL_LOCK:
        with connect_journal_db() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT data FROM trades
                WHERE id=? OR external_id=?
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (trade_id, trade_id),
            ).fetchone()
            existing = json.loads(row["data"]) if row else {}
            incoming = dict(patch)
            incoming["id"] = str(incoming.get("id") or existing.get("id") or trade_id)
            if existing:
                merged = merge_journal_trade(existing, incoming)
            else:
                merged = incoming
            merged["updatedAt"] = str(incoming.get("updatedAt") or updated_at)
            upsert_trade_rows(connection, [merged], updated_at)
            connection.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('updatedAt', ?)", (updated_at,))
            connection.commit()

    return {
        "ok": True,
        "updatedAt": updated_at,
        "trade": merged,
        "storage": str(JOURNAL_DB_FILE),
        "legacyStorage": str(JOURNAL_FILE),
    }


def patch_review_payload(review_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    if not review_id:
        raise RuntimeError("Review id is required.")
    if not isinstance(patch, dict):
        raise RuntimeError("Review patch must be an object.")

    updated_at = journal_updated_at()
    with JOURNAL_LOCK:
        with connect_journal_db() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT data FROM reviews
                WHERE id=? OR period_key=?
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (review_id, review_id),
            ).fetchone()
            existing = json.loads(row["data"]) if row else {}
            incoming = dict(patch)
            merged = {**existing, **incoming}
            merged["id"] = str(merged.get("id") or existing.get("id") or review_id)
            merged["periodKey"] = str(merged.get("periodKey") or existing.get("periodKey") or review_id)
            merged["updatedAt"] = str(incoming.get("updatedAt") or updated_at)
            for field in ("marketSummary", "good", "bad", "lesson", "nextPlan"):
                if existing.get(field) and not str(incoming.get(field) or "").strip():
                    merged[field] = existing.get(field)
            upsert_review_rows(connection, [merged], updated_at)
            connection.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('updatedAt', ?)", (updated_at,))
            connection.commit()

    return {
        "ok": True,
        "updatedAt": updated_at,
        "review": merged,
        "storage": str(JOURNAL_DB_FILE),
        "legacyStorage": str(JOURNAL_FILE),
    }


def delete_trade_payload(trade_id: str) -> dict[str, Any]:
    if not trade_id:
        raise RuntimeError("Trade id is required.")
    updated_at = journal_updated_at()
    with JOURNAL_LOCK:
        with connect_journal_db() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute("DELETE FROM trades WHERE id=? OR external_id=?", (trade_id, trade_id))
            connection.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('updatedAt', ?)", (updated_at,))
            connection.commit()
            deleted = cursor.rowcount
    return {"ok": True, "deleted": deleted, "updatedAt": updated_at, "storage": str(JOURNAL_DB_FILE)}


def delete_review_payload(review_id: str) -> dict[str, Any]:
    if not review_id:
        raise RuntimeError("Review id is required.")
    updated_at = journal_updated_at()
    with JOURNAL_LOCK:
        with connect_journal_db() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute("DELETE FROM reviews WHERE id=? OR period_key=?", (review_id, review_id))
            connection.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('updatedAt', ?)", (updated_at,))
            connection.commit()
            deleted = cursor.rowcount
    return {"ok": True, "deleted": deleted, "updatedAt": updated_at, "storage": str(JOURNAL_DB_FILE)}


def save_client_error(payload: dict[str, Any]) -> dict[str, Any]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    event = {
        "receivedAt": journal_updated_at(),
        "message": str(payload.get("message") or ""),
        "stack": str(payload.get("stack") or ""),
        "componentStack": str(payload.get("componentStack") or ""),
        "href": str(payload.get("href") or ""),
        "userAgent": str(payload.get("userAgent") or ""),
        "at": str(payload.get("at") or ""),
    }
    with CLIENT_ERROR_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return {"ok": True, "log": str(CLIENT_ERROR_FILE)}


def trade_result(status: str, pnl: float) -> str:
    if status == "open":
        return "open"
    if pnl > 0:
        return "win"
    if pnl < 0:
        return "loss"
    return "breakeven"


def pnl_components_from_values(
    profit: float = 0.0,
    commission: float = 0.0,
    swap_value: float = 0.0,
    fee: float = 0.0,
) -> dict[str, float]:
    gross = as_float(profit)
    commission_value = as_float(commission)
    swap_amount = as_float(swap_value)
    fee_value = as_float(fee)
    return {
        "brokerGrossPnl": gross,
        "brokerCommission": commission_value,
        "brokerSwap": swap_amount,
        "brokerFee": fee_value,
        "brokerPnl": gross + commission_value + swap_amount + fee_value,
        "fees": abs(commission_value) + abs(swap_amount) + abs(fee_value),
    }


def pnl_components_from_rows(rows: list[dict[str, Any]]) -> dict[str, float]:
    return pnl_components_from_values(
        profit=sum(as_float(row.get("profit")) for row in rows),
        commission=sum(as_float(row.get("commission")) for row in rows),
        swap_value=sum(as_float(row.get("swap")) for row in rows),
        fee=sum(as_float(row.get("fee")) for row in rows),
    )


def merge_tags(*tag_lists: Any) -> list[str]:
    tags: list[str] = []
    for value in tag_lists:
        if isinstance(value, list):
            raw_tags = value
        else:
            raw_tags = str(value or "").replace("#", ",").split(",")
        for tag in raw_tags:
            normalized = str(tag).strip()
            if normalized and normalized not in tags:
                tags.append(normalized)
    return tags


def normalize_imported_for_journal(imported: dict[str, Any], account: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    external_id = str(imported.get("externalId") or f"mt5-ea:{imported.get('positionId') or now}")
    status = str(imported.get("status") or "closed")
    pnl = as_float(imported.get("brokerPnl"))
    symbol = str(imported.get("symbol") or "").upper()
    comment = str(imported.get("comment") or "")
    return {
        "id": external_id,
        "externalId": external_id,
        "source": "mt5",
        "createdAt": imported.get("openTime") or imported.get("closeTime") or now,
        "updatedAt": now,
        "date": imported.get("date") or date_from_iso(str(imported.get("closeTime") or imported.get("openTime") or "")),
        "market": "XM MT5",
        "symbol": symbol,
        "currency": str(imported.get("currency") or account.get("currency") or "USD").upper(),
        "direction": imported.get("direction") or "long",
        "setup": "기타",
        "timeframe": "MT5",
        "status": status,
        "result": trade_result(status, pnl),
        "accountValue": as_float(imported.get("accountValue"), account_value(account)),
        "riskPercent": 0,
        "entryPrice": as_float(imported.get("entryPrice")),
        "stopPrice": as_float(imported.get("stopPrice")),
        "targetPrice": as_float(imported.get("targetPrice")),
        "exitPrice": as_float(imported.get("exitPrice")),
        "quantity": as_float(imported.get("quantity")),
        "fees": as_float(imported.get("fees")),
        "brokerPnl": pnl,
        "brokerGrossPnl": as_float(imported.get("brokerGrossPnl"), pnl),
        "brokerCommission": as_float(imported.get("brokerCommission")),
        "brokerSwap": as_float(imported.get("brokerSwap")),
        "brokerFee": as_float(imported.get("brokerFee")),
        "confidence": 3,
        "discipline": 3,
        "emotion": "차분함",
        "grade": "B",
        "tags": merge_tags(["MT5", "XM", symbol]),
        "thesis": "",
        "riskPlan": "",
        "good": "",
        "bad": "",
        "lesson": "",
        "screenshot": imported.get("screenshot") or None,
        "screenshotName": imported.get("screenshotName") or None,
        "brokerMeta": {
            "accountLogin": account.get("login"),
            "server": account.get("server"),
            "ticket": as_int(imported.get("ticket")),
            "positionId": as_int(imported.get("positionId")),
            "order": as_int(imported.get("order")),
            "magic": as_int(imported.get("magic")),
            "comment": comment,
            "openTime": imported.get("openTime") or "",
            "closeTime": imported.get("closeTime") or "",
        },
    }


def merge_journal_trade(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    preserved_fields = {
        "id",
        "createdAt",
        "confidence",
        "discipline",
        "emotion",
        "grade",
        "riskPlan",
        "good",
        "bad",
        "lesson",
    }
    merged = {**existing, **incoming}
    for field in preserved_fields:
        if existing.get(field) not in (None, ""):
            merged[field] = existing.get(field)

    if str(existing.get("emotion") or "") in BROKEN_EMOTION_TEXTS:
        merged["emotion"] = incoming.get("emotion") or "차분함"

    existing_thesis = str(existing.get("thesis") or "")
    should_preserve_thesis = (
        existing_thesis
        and existing_thesis not in AUTO_THESIS_TEXTS
        and not existing_thesis.startswith(AUTO_THESIS_PREFIXES)
    )
    if should_preserve_thesis:
        merged["thesis"] = existing.get("thesis")

    if existing.get("setup") and "MT5" not in str(existing.get("setup")):
        merged["setup"] = existing.get("setup")
    else:
        merged["setup"] = incoming.get("setup") or "기타"

    merged["tags"] = merge_tags(incoming.get("tags"), existing.get("tags"))
    merged["screenshot"] = incoming.get("screenshot") or existing.get("screenshot")
    merged["screenshotName"] = incoming.get("screenshotName") or existing.get("screenshotName")

    for field in (
        "stopPrice",
        "targetPrice",
        "entryPrice",
        "exitPrice",
        "quantity",
        "brokerPnl",
        "brokerGrossPnl",
        "brokerCommission",
        "brokerSwap",
        "brokerFee",
        "fees",
    ):
        if not as_float(incoming.get(field)) and existing.get(field) not in (None, ""):
            merged[field] = existing.get(field)

    return merged


def merge_trades_into_journal(imported: list[dict[str, Any]], account: dict[str, Any]) -> dict[str, Any]:
    if not imported:
        return {"ok": True, "updated": 0, "trades": 0, "storage": str(JOURNAL_DB_FILE)}

    incoming_trades = [normalize_imported_for_journal(trade, account) for trade in imported]
    document = journal_payload()
    current = document.get("trades") if isinstance(document, dict) else []
    if not isinstance(current, list):
        current = []

    by_external_id = {
        str(trade.get("externalId")): trade
        for trade in current
        if isinstance(trade, dict) and trade.get("externalId")
    }
    by_id = {str(trade.get("id")): trade for trade in current if isinstance(trade, dict) and trade.get("id")}
    changed = 0

    for incoming in incoming_trades:
        existing = by_external_id.get(str(incoming.get("externalId"))) or by_id.get(str(incoming.get("id")))
        if existing:
            merged = merge_journal_trade(existing, incoming)
            if merged != existing:
                existing.clear()
                existing.update(merged)
                changed += 1
        else:
            current.append(incoming)
            by_external_id[str(incoming.get("externalId"))] = incoming
            changed += 1

    if changed:
        current.sort(key=journal_trade_sort_key, reverse=True)
        save_journal({"trades": current, "reviews": document.get("reviews", []) if isinstance(document, dict) else []})

    return {"ok": True, "updated": changed, "trades": len(current), "storage": str(JOURNAL_DB_FILE)}


def rounded_volume(value: float, step: float) -> float:
    decimals = max(0, min(8, len(str(step).split(".")[-1]) if "." in str(step) else 0))
    return round(value, decimals)


def mt5_last_error() -> str:
    if mt5 is None:
        return MT5_IMPORT_ERROR or "MetaTrader5 package is not installed."
    error = mt5.last_error()
    return f"{error[0]} {error[1]}" if isinstance(error, tuple) and len(error) >= 2 else str(error)


def mt5_terminal_running() -> bool:
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq terminal64.exe", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except Exception:
        return False
    return "terminal64.exe" in result.stdout.lower()


def initialize_mt5() -> None:
    if mt5 is None:
        raise RuntimeError(MT5_IMPORT_ERROR or "MetaTrader5 package is not installed.")

    if not MT5_BRIDGE_AUTO_LAUNCH and not mt5_terminal_running():
        raise RuntimeError("MT5 terminal is not running. Start MT5 with the launcher or open XM MT5 manually.")

    path = os.environ.get("MT5_PATH")
    login = os.environ.get("MT5_LOGIN")
    password = os.environ.get("MT5_PASSWORD")
    server = os.environ.get("MT5_SERVER")

    kwargs: dict[str, Any] = {}
    if path:
        kwargs["path"] = path
    if login and password and server:
        kwargs.update({"login": int(login), "password": password, "server": server})

    if not mt5.initialize(**kwargs):
        raise RuntimeError(f"MT5 initialize failed: {mt5_last_error()}")


def account_payload() -> dict[str, Any]:
    account = mt5.account_info()
    if account is None:
        raise RuntimeError(f"MT5 account_info failed: {mt5_last_error()}")

    row = as_dict(account)
    return {
        "login": as_int(row.get("login")),
        "server": row.get("server") or "",
        "name": row.get("name") or "",
        "currency": row.get("currency") or "USD",
        "balance": as_float(row.get("balance")),
        "equity": as_float(row.get("equity")),
        "margin": as_float(row.get("margin")),
        "marginFree": as_float(row.get("margin_free")),
        "leverage": as_int(row.get("leverage")),
    }


def terminal_data_path() -> Path | None:
    if mt5 is None:
        return None
    info = mt5.terminal_info()
    if info is None:
        return None
    row = as_dict(info)
    data_path = row.get("data_path")
    return Path(str(data_path)) if data_path else None


def ea_export_dir() -> Path:
    if EA_EXPORT_DIR:
        return Path(EA_EXPORT_DIR)
    data_path = terminal_data_path()
    if data_path:
        return data_path / "MQL5" / "Files" / "trading_journal"
    return DATA_DIR / "trading_journal"


def positions_payload() -> list[dict[str, Any]]:
    positions = mt5.positions_get()
    if positions is None:
        return []

    buy_type = getattr(mt5, "POSITION_TYPE_BUY", 0)
    payload: list[dict[str, Any]] = []

    for position in positions:
        row = as_dict(position)
        direction = "long" if as_int(row.get("type")) == buy_type else "short"
        payload.append(
            {
                "ticket": as_int(row.get("ticket")),
                "symbol": row.get("symbol") or "",
                "direction": direction,
                "volume": as_float(row.get("volume")),
                "priceOpen": as_float(row.get("price_open")),
                "priceCurrent": as_float(row.get("price_current")),
                "stopLoss": as_float(row.get("sl")),
                "takeProfit": as_float(row.get("tp")),
                "profit": as_float(row.get("profit")),
                "swap": as_float(row.get("swap")),
                "comment": row.get("comment") or "",
                "time": iso_from_seconds(row.get("time")),
            }
        )

    return payload


def position_identifier(row: dict[str, Any]) -> int:
    return as_int(row.get("identifier") or row.get("position_id") or row.get("position") or row.get("ticket"))


def imported_from_position(row: dict[str, Any], account: dict[str, Any], status: str = "open") -> dict[str, Any]:
    buy_type = getattr(mt5, "POSITION_TYPE_BUY", 0)
    position_id = position_identifier(row)
    login = as_int(account.get("login"))
    direction = "long" if as_int(row.get("type")) == buy_type else "short"
    pnl_components = pnl_components_from_values(
        profit=as_float(row.get("profit")),
        swap_value=as_float(row.get("swap")),
    )
    return {
        "externalId": f"mt5:{login}:{position_id}" if login else f"mt5-live:{position_id}",
        "date": date_from_iso(iso_from_seconds(row.get("time"))),
        "symbol": row.get("symbol") or "",
        "direction": direction,
        "status": status,
        "entryPrice": as_float(row.get("price_open")),
        "stopPrice": as_float(row.get("sl")),
        "targetPrice": as_float(row.get("tp")),
        "exitPrice": as_float(row.get("price_current")),
        "quantity": as_float(row.get("volume")),
        **pnl_components,
        "currency": account.get("currency") or "USD",
        "accountValue": account_value(account),
        "comment": row.get("comment") or "",
        "openTime": iso_from_seconds(row.get("time")),
        "closeTime": "",
        "positionId": position_id,
        "ticket": as_int(row.get("ticket")),
        "order": as_int(row.get("ticket")),
        "magic": as_int(row.get("magic")),
        "source": "mt5-live",
    }


def closed_imported_from_position(row: dict[str, Any], account: dict[str, Any]) -> dict[str, Any]:
    imported = imported_from_position(row, account, "closed")
    position_id = position_identifier(row)
    open_seconds = as_int(row.get("time"))
    date_from = datetime.fromtimestamp(open_seconds, tz=timezone.utc).astimezone() - timedelta(days=1) if open_seconds else datetime.now() - timedelta(days=14)
    date_to = datetime.now() + timedelta(minutes=5)

    try:
        deals = mt5.history_deals_get(date_from, date_to) or []
    except Exception:
        deals = []

    deal_type_buy = getattr(mt5, "DEAL_TYPE_BUY", 0)
    deal_type_sell = getattr(mt5, "DEAL_TYPE_SELL", 1)
    entry_out_values = {
        getattr(mt5, "DEAL_ENTRY_OUT", 1),
        getattr(mt5, "DEAL_ENTRY_INOUT", 2),
        getattr(mt5, "DEAL_ENTRY_OUT_BY", 3),
    }
    exit_rows: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    for deal in deals:
        deal_row = as_dict(deal)
        if as_int(deal_row.get("position_id") or deal_row.get("position")) != position_id:
            continue
        if as_int(deal_row.get("type")) not in {deal_type_buy, deal_type_sell}:
            continue
        all_rows.append(deal_row)
        if as_int(deal_row.get("entry")) in entry_out_values:
            exit_rows.append(deal_row)

    if exit_rows:
        imported["exitPrice"] = weighted_average(exit_rows, "price", "volume")
        imported["quantity"] = sum(as_float(item.get("volume")) for item in exit_rows) or imported["quantity"]
        imported["closeTime"] = iso_from_seconds(exit_rows[-1].get("time"))
        imported["date"] = date_from_iso(imported["closeTime"])
        imported["ticket"] = as_int(exit_rows[-1].get("ticket"), imported["ticket"])
        imported["order"] = as_int(exit_rows[-1].get("order"), imported["order"])

    if all_rows:
        imported.update(pnl_components_from_rows(all_rows))

    return imported


def parse_mt5_datetime(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        parsed_iso = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed_iso.tzinfo is not None:
            return parsed_iso.astimezone().isoformat(timespec="seconds")
    except ValueError:
        pass
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            parsed = datetime.strptime(text[:19], fmt).replace(tzinfo=MT5_SERVER_TZ)
            return parsed.astimezone().isoformat(timespec="seconds")
        except ValueError:
            continue
    return text


def seconds_since_iso(value: str) -> float:
    if not value:
        return 0.0
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return 0.0
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return max(0.0, (datetime.now().astimezone() - parsed).total_seconds())


def read_text_file(path: Path) -> str:
    if not path.exists():
        return ""

    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "mbcs", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    text = read_text_file(path)
    if not text:
        return []

    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            row = json.loads(stripped)
        except json.JSONDecodeError:
            events.append(
                {
                    "event": "parse_error",
                    "lineNumber": line_number,
                    "raw": stripped[:500],
                }
            )
            continue
        if isinstance(row, dict):
            events.append(row)
    return events


def read_csv_events(path: Path) -> list[dict[str, Any]]:
    text = read_text_file(path)
    if not text:
        return []

    try:
        rows = csv.DictReader(io.StringIO(text))
        events = []
        for row in rows:
            if not row:
                continue
            events.append({str(key): value for key, value in row.items() if key is not None})
        return events
    except csv.Error as exc:
        return [{"event": "parse_error", "raw": str(exc)}]


def file_modified_iso(path: Path) -> tuple[str, float]:
    if not path.exists():
        return "", 0.0
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).astimezone()
    return modified.isoformat(timespec="seconds"), max(0.0, (datetime.now().astimezone() - modified).total_seconds())


def ea_events_file_signature(export_dir: Path) -> str:
    parts: list[str] = []
    for name in (EA_EVENT_FILE, EA_EVENT_CSV_FILE):
        path = export_dir / name
        if path.exists():
            stat = path.stat()
            parts.append(f"{name}:{stat.st_mtime_ns}:{stat.st_size}")
        else:
            parts.append(f"{name}:missing")
    return "|".join(parts)


def screenshot_data_url(export_dir: Path, relative_path: Any) -> tuple[str, str]:
    if not relative_path:
        return "", ""

    normalized = str(relative_path).replace("/", "\\").lstrip("\\/")
    screenshot_path = (export_dir / normalized).resolve()
    try:
        screenshot_path.relative_to(export_dir.resolve())
    except ValueError:
        return "", ""

    if not screenshot_path.exists() or screenshot_path.stat().st_size > MAX_SCREENSHOT_BYTES:
        return "", ""

    suffix = screenshot_path.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg" if suffix in {".jpg", ".jpeg"} else "image/bmp"
    encoded = base64.b64encode(screenshot_path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}", screenshot_path.name


def event_sort_key(event: dict[str, Any]) -> str:
    return parse_mt5_datetime(event.get("time")) or str(event.get("eventId") or "")


def ea_events_payload(days: int, account: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    export_dir = ea_export_dir()
    event_file = export_dir / EA_EVENT_FILE
    csv_file = export_dir / EA_EVENT_CSV_FILE
    json_events = read_jsonl(event_file)
    csv_events = read_csv_events(csv_file)
    json_usable = [event for event in json_events if event.get("event") != "parse_error"]
    csv_usable = [event for event in csv_events if event.get("event") != "parse_error"]
    events = json_events if json_usable or not csv_usable else csv_events
    event_source = "jsonl" if events is json_events else "csv"
    parse_errors = [event for event in events if event.get("event") == "parse_error"]
    usable_events = [event for event in events if event.get("event") != "parse_error"]
    trade_event_names = {"open", "update", "close"}
    trade_events = [event for event in usable_events if str(event.get("event") or "").lower() in trade_event_names]
    status_events = [event for event in usable_events if str(event.get("event") or "").lower() not in trade_event_names]

    cutoff = datetime.now().astimezone() - timedelta(days=max(1, min(days, 365)))
    grouped: dict[str, dict[str, Any]] = {}

    for event in sorted(trade_events, key=event_sort_key):
        position_id = as_int(event.get("positionId"))
        if not position_id:
            continue

        login = as_int(event.get("accountLogin"), as_int(account.get("login")))
        external_id = f"mt5:{login}:{position_id}" if login else f"mt5-ea:{position_id}"
        state = grouped.setdefault(
            external_id,
            {
                "externalId": external_id,
                "status": "open",
                "positionId": position_id,
                "accountLogin": login,
                "server": event.get("server") or account.get("server") or "",
                "events": [],
            },
        )
        state["events"].append(event)

        event_type = str(event.get("event") or "").lower()
        event_time = parse_mt5_datetime(event.get("time"))
        open_time = parse_mt5_datetime(event.get("openTime")) or state.get("openTime") or event_time

        for key in ("symbol", "direction", "comment", "server"):
            if event.get(key):
                state[key] = event.get(key)

        state["ticket"] = as_int(event.get("ticket"), as_int(state.get("ticket")))
        state["positionId"] = position_id
        state["openTime"] = open_time
        state["entryPrice"] = as_float(event.get("entryPrice"), as_float(state.get("entryPrice")))
        state["quantity"] = as_float(event.get("volume"), as_float(state.get("quantity")))
        state["stopPrice"] = as_float(event.get("stopLoss")) or as_float(state.get("stopPrice"))
        state["targetPrice"] = as_float(event.get("takeProfit")) or as_float(state.get("targetPrice"))

        screenshot, screenshot_name = screenshot_data_url(export_dir, event.get("screenshot"))
        if screenshot:
            state["screenshot"] = screenshot
            state["screenshotName"] = screenshot_name

        if event_type == "close":
            close_time = parse_mt5_datetime(event.get("closeTime")) or event_time
            profit = as_float(event.get("profit"))
            commission = as_float(event.get("commission"))
            swap_value = as_float(event.get("closeSwap"), as_float(event.get("swap")))
            fee = as_float(event.get("fee"))
            state.update(
                {
                    "status": "closed",
                    "closeTime": close_time,
                    "exitPrice": as_float(event.get("closePrice")),
                    "quantity": as_float(event.get("closeVolume")) or as_float(state.get("quantity")),
                    **pnl_components_from_values(profit=profit, commission=commission, swap_value=swap_value, fee=fee),
                    "ticket": as_int(event.get("closeDeal"), as_int(state.get("ticket"))),
                    "order": as_int(event.get("ticket"), as_int(state.get("order"))),
                }
            )
        elif event_type in {"open", "update"}:
            state.update(
                pnl_components_from_values(
                    profit=as_float(event.get("floatingProfit")),
                    swap_value=as_float(event.get("swap")),
                )
            )

    imported: list[dict[str, Any]] = []
    for state in grouped.values():
        open_time = str(state.get("openTime") or "")
        close_time = str(state.get("closeTime") or "")
        time_for_filter = close_time or open_time
        if time_for_filter:
            try:
                parsed_time = datetime.fromisoformat(time_for_filter)
                if parsed_time < cutoff:
                    continue
            except ValueError:
                pass

        status = str(state.get("status") or "open")
        imported.append(
            {
                "externalId": state.get("externalId") or "",
                "date": date_from_iso(close_time or open_time),
                "symbol": state.get("symbol") or "",
                "direction": state.get("direction") or "long",
                "status": status,
                "entryPrice": as_float(state.get("entryPrice")),
                "stopPrice": as_float(state.get("stopPrice")),
                "targetPrice": as_float(state.get("targetPrice")),
                "exitPrice": as_float(state.get("exitPrice")),
                "quantity": as_float(state.get("quantity")),
                "brokerPnl": as_float(state.get("brokerPnl")),
                "brokerGrossPnl": as_float(state.get("brokerGrossPnl"), as_float(state.get("brokerPnl"))),
                "brokerCommission": as_float(state.get("brokerCommission")),
                "brokerSwap": as_float(state.get("brokerSwap")),
                "brokerFee": as_float(state.get("brokerFee")),
                "fees": as_float(state.get("fees")),
                "currency": account.get("currency") or "USD",
                "accountValue": account_value(account),
                "comment": state.get("comment") or "",
                "openTime": open_time,
                "closeTime": close_time,
                "positionId": as_int(state.get("positionId")),
                "ticket": as_int(state.get("ticket")),
                "order": as_int(state.get("order")),
                "magic": 0,
                "screenshot": state.get("screenshot") or "",
                "screenshotName": state.get("screenshotName") or "",
                "source": "mt5-ea",
            }
        )

    imported.sort(key=lambda item: item.get("closeTime") or item.get("openTime") or "", reverse=True)
    event_mtime, seconds_since_file_modified = file_modified_iso(event_file if event_source == "jsonl" else csv_file)
    csv_mtime, seconds_since_csv_modified = file_modified_iso(csv_file)
    last_event = usable_events[-1] if usable_events else {}
    last_status = status_events[-1] if status_events else {}
    last_event_time = parse_mt5_datetime(last_event.get("time")) if last_event else ""
    last_status_time = parse_mt5_datetime(last_status.get("time")) if last_status else ""
    seconds_since_status = seconds_since_iso(last_status_time)
    last_status_name = str(last_status.get("event") or "")
    if not event_file.exists():
        attachment_state = "missing"
        attachment_message = "EA event file was not created yet. Attach TradeJournalExporterEA to an MT5 chart."
    elif last_status_name == "ea_stop":
        attachment_state = "stopped"
        attachment_message = "EA wrote ea_stop. Attach it again or enable Algo Trading."
    elif status_events and seconds_since_file_modified <= EA_HEARTBEAT_STALE_SECONDS:
        attachment_state = "connected"
        attachment_message = "EA heartbeat is being received."
    elif status_events:
        attachment_state = "stale"
        attachment_message = "EA event file exists, but heartbeat is stale."
    else:
        attachment_state = "unknown"
        attachment_message = "EA event file exists, but no status event was found."

    meta = {
        "eventFile": str(event_file),
        "eventFileExists": event_file.exists(),
        "eventFileModifiedAt": event_mtime,
        "secondsSinceEventFileModified": seconds_since_file_modified,
        "csvFile": str(csv_file),
        "csvFileExists": csv_file.exists(),
        "csvFileModifiedAt": csv_mtime,
        "secondsSinceCsvFileModified": seconds_since_csv_modified,
        "eventSource": event_source,
        "eventCount": len(usable_events),
        "jsonEventCount": len(json_usable),
        "csvEventCount": len(csv_usable),
        "tradeEventCount": len(trade_events),
        "statusEventCount": len(status_events),
        "parseErrorCount": len(parse_errors),
        "tradeCount": len(imported),
        "lastEvent": last_event.get("event") or "",
        "lastEventTime": last_event_time,
        "lastStatus": last_status.get("event") or "",
        "lastStatusTime": last_status_time,
        "lastStatusChartSymbol": last_status.get("chartSymbol") or "",
        "lastStatusPositionsTotal": as_int(last_status.get("positionsTotal")),
        "lastStatusEaVersion": last_status.get("eaVersion") or "",
        "lastStatusFeatures": last_status.get("features") or "",
        "secondsSinceLastEvent": seconds_since_iso(last_event_time),
        "secondsSinceLastStatus": seconds_since_status,
        "attachmentState": attachment_state,
        "attachmentMessage": attachment_message,
    }
    return imported, meta


def merge_imported_trades(*trade_lists: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_external_id: dict[str, dict[str, Any]] = {}

    for trade_list in trade_lists:
        for incoming in trade_list:
            external_id = str(incoming.get("externalId") or "")
            if not external_id:
                continue

            existing = by_external_id.get(external_id, {})
            merged = {**existing, **incoming}

            # `deals_payload()` is the broker's closed-deal ledger.  EA events
            # can be delayed and frequently contain the last open-position PnL,
            # so they must never overwrite a completed broker record.
            existing_is_closed_broker_record = bool(existing.get("closeTime")) and str(
                incoming.get("source") or ""
            ) == "mt5-ea"
            if existing_is_closed_broker_record:
                for key in (
                    "date",
                    "symbol",
                    "direction",
                    "entryPrice",
                    "stopPrice",
                    "targetPrice",
                    "exitPrice",
                    "quantity",
                    "brokerPnl",
                    "brokerGrossPnl",
                    "brokerCommission",
                    "brokerSwap",
                    "brokerFee",
                    "fees",
                    "currency",
                    "accountValue",
                    "comment",
                    "openTime",
                    "closeTime",
                    "positionId",
                    "ticket",
                    "order",
                    "magic",
                ):
                    if key in existing:
                        merged[key] = existing[key]
                merged["status"] = "closed"
            for key in (
                "entryPrice",
                "stopPrice",
                "targetPrice",
                "exitPrice",
                "quantity",
                "brokerPnl",
                "brokerGrossPnl",
                "brokerCommission",
                "brokerSwap",
                "brokerFee",
                "fees",
            ):
                if not as_float(incoming.get(key)) and key in existing:
                    merged[key] = existing.get(key)
            for key in ("screenshot", "screenshotName", "comment", "openTime", "closeTime"):
                if not incoming.get(key) and key in existing:
                    merged[key] = existing.get(key)
            by_external_id[external_id] = merged

    return sorted(
        by_external_id.values(),
        key=lambda item: str(item.get("closeTime") or item.get("openTime") or item.get("date") or ""),
        reverse=True,
    )


def symbol_payload(symbol: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if not symbol:
        raise RuntimeError("symbol is required.")
    if not mt5.symbol_select(symbol, True):
        raise RuntimeError(f"symbol_select failed for {symbol}: {mt5_last_error()}")

    info = mt5.symbol_info(symbol)
    tick = mt5.symbol_info_tick(symbol)
    if info is None:
        raise RuntimeError(f"symbol_info failed for {symbol}: {mt5_last_error()}")
    if tick is None:
        raise RuntimeError(f"symbol_info_tick failed for {symbol}: {mt5_last_error()}")

    return as_dict(info), as_dict(tick)


def symbol_info_payload(info: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": info.get("name") or info.get("symbol") or "",
        "description": info.get("description") or "",
        "currencyBase": info.get("currency_base") or "",
        "currencyProfit": info.get("currency_profit") or "",
        "currencyMargin": info.get("currency_margin") or "",
        "digits": as_int(info.get("digits")),
        "point": as_float(info.get("point")),
        "tradeTickSize": as_float(info.get("trade_tick_size")),
        "tradeTickValue": as_float(info.get("trade_tick_value")),
        "volumeMin": as_float(info.get("volume_min")),
        "volumeMax": as_float(info.get("volume_max")),
        "volumeStep": as_float(info.get("volume_step")),
        "spread": as_int(info.get("spread")),
        "tradeMode": as_int(info.get("trade_mode")),
    }


def tick_payload(tick: dict[str, Any]) -> dict[str, Any]:
    return {
        "time": iso_from_seconds(tick.get("time")),
        "timeRaw": as_int(tick.get("time")),
        "bid": as_float(tick.get("bid")),
        "ask": as_float(tick.get("ask")),
        "last": as_float(tick.get("last")),
        "volume": as_float(tick.get("volume")),
        "flags": as_int(tick.get("flags")),
    }


def timeframe_value(timeframe: str) -> int:
    normalized = (timeframe or "M5").upper()
    values = {
        "M1": getattr(mt5, "TIMEFRAME_M1", 1),
        "M5": getattr(mt5, "TIMEFRAME_M5", 5),
        "M15": getattr(mt5, "TIMEFRAME_M15", 15),
        "M30": getattr(mt5, "TIMEFRAME_M30", 30),
        "H1": getattr(mt5, "TIMEFRAME_H1", 16385),
        "H4": getattr(mt5, "TIMEFRAME_H4", 16388),
        "D1": getattr(mt5, "TIMEFRAME_D1", 16408),
    }
    if normalized not in values:
        raise RuntimeError("timeframe must be one of M1, M5, M15, M30, H1, H4, D1.")
    return values[normalized]


def chart_payload(symbol: str, timeframe: str, bars: int) -> dict[str, Any]:
    initialize_mt5()
    normalized_symbol = symbol.strip().upper()
    normalized_timeframe = (timeframe or "M5").upper()
    max_bars = max(50, min(as_int(bars, 500), 2000))
    info, tick = symbol_payload(normalized_symbol)
    rates = mt5.copy_rates_from_pos(normalized_symbol, timeframe_value(normalized_timeframe), 0, max_bars)
    if rates is None:
        raise RuntimeError(f"copy_rates_from_pos failed for {normalized_symbol}: {mt5_last_error()}")

    payload_bars = []
    for rate in rates:
        row = as_dict(rate)
        payload_bars.append(
            {
                "time": as_int(row.get("time")),
                "open": as_float(row.get("open")),
                "high": as_float(row.get("high")),
                "low": as_float(row.get("low")),
                "close": as_float(row.get("close")),
                "volume": as_float(row.get("tick_volume")),
                "spread": as_int(row.get("spread")),
                "realVolume": as_float(row.get("real_volume")),
            }
        )

    return {
        "ok": True,
        "generatedAt": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "symbol": normalized_symbol,
        "timeframe": normalized_timeframe,
        "bars": payload_bars,
        "tick": tick_payload(tick),
        "symbolInfo": symbol_info_payload(info),
    }


def live_payload(symbol: str) -> dict[str, Any]:
    initialize_mt5()
    normalized_symbol = symbol.strip().upper()
    account = account_payload()
    info, tick = symbol_payload(normalized_symbol)
    return {
        "ok": True,
        "generatedAt": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "account": account,
        "positions": positions_payload(),
        "tick": tick_payload(tick),
        "symbolInfo": symbol_info_payload(info),
    }


def generate_ai_feedback_payload(trade_id: str = "") -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    feedback_module = importlib.import_module("scripts.generate_ai_trade_feedback")
    feedback_module = importlib.reload(feedback_module)

    result = feedback_module.generate_feedback(trade_id or None)
    updated_trade = None
    with connect_journal_db() as connection:
        row = connection.execute("SELECT data FROM trades WHERE id=?", (str(result.get("tradeId") or ""),)).fetchone()
        if row:
            updated_trade = json.loads(row["data"])
    return {
        **result,
        "trade": updated_trade,
    }


def ai_feedback_preflight_payload(trade_id: str = "") -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    feedback_module = importlib.import_module("scripts.generate_ai_trade_feedback")
    feedback_module = importlib.reload(feedback_module)

    trade = feedback_module.load_trade(trade_id or None)
    symbol = str(trade.get("symbol") or "").strip().upper()
    result: dict[str, Any] = {
        "ok": True,
        "tradeId": str(trade.get("id") or ""),
        "symbol": symbol,
        "generatedAt": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "mt5PackageAvailable": mt5 is not None,
        "mt5TerminalRunning": mt5_terminal_running(),
        "canUseBars": False,
        "timeframes": [],
        "message": "",
    }
    if mt5 is None:
        result["message"] = MT5_IMPORT_ERROR or "MetaTrader5 package is not installed."
        return result
    if not result["mt5TerminalRunning"]:
        result["message"] = "MT5 terminal is not running. AI feedback will use the saved chart image fallback."
        return result

    try:
        open_time = feedback_module.parse_trade_time(trade, "openTime")
        close_time = feedback_module.parse_trade_time(trade, "closeTime")
    except Exception as exc:
        result["message"] = f"Cannot parse trade time: {exc}"
        return result

    available_count = 0
    candidate_timeframes = getattr(feedback_module, "CANDIDATE_TIMEFRAMES", ("D1", "H4", "H1", "M30", "M15", "M5", "M1"))
    for timeframe in candidate_timeframes:
        try:
            used_symbol, bars = feedback_module.fetch_bars(symbol, timeframe, open_time - timedelta(days=3), close_time + timedelta(days=1))
            bar_count = len(bars)
            available = bar_count > 0
            available_count += 1 if available else 0
            result["timeframes"].append(
                {
                    "timeframe": timeframe,
                    "available": available,
                    "bars": bar_count,
                    "symbol": used_symbol,
                    "error": "",
                }
            )
        except Exception as exc:
            result["timeframes"].append(
                {
                    "timeframe": timeframe,
                    "available": False,
                    "bars": 0,
                    "symbol": symbol,
                    "error": str(exc),
                }
            )

    result["canUseBars"] = available_count == len(candidate_timeframes)
    result["message"] = (
        "MT5 candidate timeframe bars are available for this trade."
        if result["canUseBars"]
        else "Some MT5 candidate timeframe bars are unavailable. AI feedback will fall back unless MT5/history data is ready."
    )
    result["provider"] = ai_feedback_provider_payload()
    result["canUseAi"] = bool(result["provider"].get("ready"))
    return result


def ai_feedback_config_payload() -> dict[str, Any]:
    return {"ok": True, **ai_feedback_provider_payload()}


def save_ai_feedback_config(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    request_payload = payload if isinstance(payload, dict) else {}
    provider = str(request_payload.get("provider") or "gemini").strip()
    model = str(request_payload.get("model") or "gemini-1.5-flash").strip()
    enabled = bool(request_payload.get("enabled", True))
    api_key = request_payload.get("apiKey")
    if api_key is not None and not isinstance(api_key, str):
        api_key = str(api_key)
    if api_key is not None:
        api_key = str(api_key).strip()

    try:
        cfg = write_ai_feedback_config(provider=provider, model=model, api_key=api_key if api_key is not None else None, enabled=enabled)
        return {
            "ok": True,
            "provider": ai_feedback_provider_payload(),
            "config": {"provider": cfg.provider, "model": cfg.model, "enabled": cfg.enabled},
            "message": "AI feedback provider 설정을 저장했습니다.",
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def ai_feedback_batch_targets(mode: str = "missing", overwrite: bool = False) -> list[dict[str, Any]]:
    normalized_mode = (mode or "missing").strip().lower()
    targets: list[dict[str, Any]] = []
    with connect_journal_db() as connection:
        rows = connection.execute("SELECT data FROM trades ORDER BY sort_time ASC, updated_at ASC").fetchall()
    for row in rows:
        trade = json.loads(row["data"])
        if trade.get("status") != "closed":
            continue
        if normalized_mode == "losses" and not (trade.get("result") == "loss" or as_float(trade.get("brokerPnl")) < 0):
            continue
        if normalized_mode == "missing" and not overwrite and isinstance(trade.get("aiFeedback"), dict):
            continue
        if not overwrite and normalized_mode == "all" and isinstance(trade.get("aiFeedback"), dict):
            continue
        trade_id = str(trade.get("id") or "")
        if not trade_id:
            continue
        targets.append(
            {
                "id": trade_id,
                "symbol": str(trade.get("symbol") or ""),
                "date": str(trade.get("date") or ""),
                "result": str(trade.get("result") or ""),
            }
        )
    return targets


def ai_feedback_job_snapshot(job_id: str) -> dict[str, Any]:
    with AI_FEEDBACK_JOB_LOCK:
        job = AI_FEEDBACK_JOBS.get(job_id)
        if not job:
            return {"ok": False, "error": "AI feedback job not found."}
        return {"ok": True, **json.loads(json.dumps(job, ensure_ascii=False))}


def run_ai_feedback_batch_job(job_id: str, targets: list[dict[str, Any]]) -> None:
    global AI_FEEDBACK_ACTIVE_JOB_ID
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    feedback_module = importlib.import_module("scripts.generate_ai_trade_feedback")
    feedback_module = importlib.reload(feedback_module)

    try:
        for target in targets:
            trade_id = str(target.get("id") or "")
            with AI_FEEDBACK_JOB_LOCK:
                job = AI_FEEDBACK_JOBS.get(job_id)
                if not job:
                    return
                job["status"] = "running"
                job["currentTradeId"] = trade_id
                job["currentSymbol"] = target.get("symbol") or ""
                job["updatedAt"] = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
            try:
                result = feedback_module.generate_feedback(trade_id)
                with AI_FEEDBACK_JOB_LOCK:
                    job = AI_FEEDBACK_JOBS[job_id]
                    job["completed"] = as_int(job.get("completed")) + 1
                    job["lastTradeId"] = trade_id
                    job["usedBars"] = as_int(job.get("usedBars")) + (1 if result.get("usedBars") else 0)
                    job["updatedAt"] = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
            except Exception as exc:
                with AI_FEEDBACK_JOB_LOCK:
                    job = AI_FEEDBACK_JOBS[job_id]
                    job["failed"] = as_int(job.get("failed")) + 1
                    errors = job.setdefault("errors", [])
                    errors.append({"tradeId": trade_id, "symbol": target.get("symbol") or "", "error": str(exc)})
                    del errors[:-10]
                    job["updatedAt"] = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
        with AI_FEEDBACK_JOB_LOCK:
            job = AI_FEEDBACK_JOBS.get(job_id)
            if job:
                job["status"] = "completed"
                job["currentTradeId"] = ""
                job["currentSymbol"] = ""
                job["completedAt"] = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
                job["updatedAt"] = job["completedAt"]
    finally:
        with AI_FEEDBACK_JOB_LOCK:
            if AI_FEEDBACK_ACTIVE_JOB_ID == job_id:
                AI_FEEDBACK_ACTIVE_JOB_ID = ""


def start_ai_feedback_batch_payload(payload: dict[str, Any]) -> dict[str, Any]:
    global AI_FEEDBACK_ACTIVE_JOB_ID
    mode = str(payload.get("mode") or "missing")
    overwrite = bool(payload.get("overwrite"))
    with AI_FEEDBACK_JOB_LOCK:
        if AI_FEEDBACK_ACTIVE_JOB_ID:
            active = AI_FEEDBACK_JOBS.get(AI_FEEDBACK_ACTIVE_JOB_ID)
            if active and active.get("status") in {"queued", "running"}:
                return {"ok": True, "jobId": AI_FEEDBACK_ACTIVE_JOB_ID, "total": as_int(active.get("total")), "alreadyRunning": True}

    targets = ai_feedback_batch_targets(mode, overwrite)
    job_id = f"ai-feedback-{time.time_ns()}"
    now = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    job = {
        "jobId": job_id,
        "status": "queued" if targets else "completed",
        "mode": mode,
        "overwrite": overwrite,
        "total": len(targets),
        "completed": 0,
        "failed": 0,
        "usedBars": 0,
        "currentTradeId": "",
        "currentSymbol": "",
        "errors": [],
        "createdAt": now,
        "updatedAt": now,
    }
    with AI_FEEDBACK_JOB_LOCK:
        AI_FEEDBACK_JOBS[job_id] = job
        if targets:
            AI_FEEDBACK_ACTIVE_JOB_ID = job_id
    if targets:
        Thread(target=run_ai_feedback_batch_job, args=(job_id, targets), daemon=True).start()
    return {"ok": True, "jobId": job_id, "total": len(targets), "alreadyRunning": False}


def order_type(side: str) -> int:
    normalized = side.lower()
    if normalized in {"buy", "long"}:
        return getattr(mt5, "ORDER_TYPE_BUY", 0)
    if normalized in {"sell", "short"}:
        return getattr(mt5, "ORDER_TYPE_SELL", 1)
    raise RuntimeError("side must be buy or sell.")


def filling_type(fill_policy: str) -> int:
    normalized = fill_policy.upper()
    if normalized == "FOK":
        return getattr(mt5, "ORDER_FILLING_FOK", 0)
    if normalized == "RETURN":
        return getattr(mt5, "ORDER_FILLING_RETURN", 2)
    return getattr(mt5, "ORDER_FILLING_IOC", 1)


def build_order_preview(payload: dict[str, Any], include_order_check: bool = True) -> dict[str, Any]:
    initialize_mt5()
    account = account_payload()

    symbol = str(payload.get("symbol") or "").strip().upper()
    side = str(payload.get("side") or "buy").lower()
    risk_percent = as_float(payload.get("riskPercent"), 1.0)
    stop_loss = as_float(payload.get("stopLoss"))
    take_profit = as_float(payload.get("takeProfit"))
    deviation = max(0, as_int(payload.get("deviation"), 20))
    comment = str(payload.get("comment") or "Trade Ledger").strip()[:31]
    fill_policy = str(payload.get("fillPolicy") or "IOC")
    magic = as_int(payload.get("magic"), 20260627)

    if risk_percent <= 0:
        raise RuntimeError("riskPercent must be greater than 0.")
    if stop_loss <= 0:
        raise RuntimeError("stopLoss must be greater than 0.")

    info, tick = symbol_payload(symbol)
    trade_type = order_type(side)
    is_buy = trade_type == getattr(mt5, "ORDER_TYPE_BUY", 0)
    entry_price = as_float(tick.get("ask") if is_buy else tick.get("bid"))
    bid = as_float(tick.get("bid"))
    ask = as_float(tick.get("ask"))

    if entry_price <= 0:
        raise RuntimeError(f"{symbol} has no tradable tick price.")
    if is_buy and stop_loss >= entry_price:
        raise RuntimeError("Buy order stopLoss must be below the current ask.")
    if not is_buy and stop_loss <= entry_price:
        raise RuntimeError("Sell order stopLoss must be above the current bid.")
    if take_profit > 0:
        if is_buy and take_profit <= entry_price:
            raise RuntimeError("Buy order takeProfit must be above the current ask.")
        if not is_buy and take_profit >= entry_price:
            raise RuntimeError("Sell order takeProfit must be below the current bid.")

    risk_basis = as_float(account.get("balance") or account.get("equity"))
    risk_amount = risk_basis * risk_percent / 100
    risk_per_lot = abs(as_float(mt5.order_calc_profit(trade_type, symbol, 1.0, entry_price, stop_loss)))
    if risk_per_lot <= 0:
        raise RuntimeError("Could not calculate risk per 1 lot. Check symbol, SL, and account currency.")

    raw_volume = risk_amount / risk_per_lot
    volume_min = as_float(info.get("volume_min"), 0.01)
    volume_max = as_float(info.get("volume_max"), 100.0)
    volume_step = as_float(info.get("volume_step"), 0.01)
    capped_volume = min(raw_volume, volume_max)
    volume = rounded_volume(floor_to_step(capped_volume, volume_step), volume_step)
    warnings: list[str] = []

    if raw_volume < volume_min:
        min_loss = abs(as_float(mt5.order_calc_profit(trade_type, symbol, volume_min, entry_price, stop_loss)))
        raise RuntimeError(
            f"Risk is below min lot. Min volume {volume_min:g} would risk about {min_loss:.2f} {account.get('currency') or ''}."
        )
    if raw_volume > volume_max:
        warnings.append(f"Requested risk exceeds max volume. Volume capped at {volume_max:g}.")
    if volume < volume_min:
        raise RuntimeError("Calculated volume is below symbol minimum volume.")

    estimated_loss = abs(as_float(mt5.order_calc_profit(trade_type, symbol, volume, entry_price, stop_loss)))
    estimated_profit = (
        as_float(mt5.order_calc_profit(trade_type, symbol, volume, entry_price, take_profit)) if take_profit > 0 else 0.0
    )
    request = {
        "action": getattr(mt5, "TRADE_ACTION_DEAL", 1),
        "symbol": symbol,
        "volume": volume,
        "type": trade_type,
        "price": entry_price,
        "sl": stop_loss,
        "tp": take_profit if take_profit > 0 else 0.0,
        "deviation": deviation,
        "magic": magic,
        "comment": comment,
        "type_time": getattr(mt5, "ORDER_TIME_GTC", 0),
        "type_filling": filling_type(fill_policy),
    }

    order_check = None
    if include_order_check:
        checked = mt5.order_check(request)
        order_check = as_dict(checked) if checked is not None else {"error": mt5_last_error()}

    return {
        "ok": True,
        "generatedAt": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "account": account,
        "symbol": symbol,
        "side": "buy" if is_buy else "sell",
        "entryPrice": entry_price,
        "bid": bid,
        "ask": ask,
        "spread": ask - bid if ask and bid else 0.0,
        "stopLoss": stop_loss,
        "takeProfit": take_profit,
        "riskPercent": risk_percent,
        "riskAmount": risk_amount,
        "riskPerLot": risk_per_lot,
        "rawVolume": raw_volume,
        "volume": volume,
        "volumeMin": volume_min,
        "volumeMax": volume_max,
        "volumeStep": volume_step,
        "estimatedLoss": estimated_loss,
        "estimatedProfit": estimated_profit,
        "rewardRisk": estimated_profit / estimated_loss if estimated_loss > 0 and estimated_profit > 0 else 0.0,
        "currency": account.get("currency") or "USD",
        "request": request,
        "orderCheck": order_check,
        "warnings": warnings,
    }


def send_order(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("confirm") != "LIVE_ORDER" or payload.get("ackRisk") is not True:
        raise RuntimeError("Live order requires confirm=LIVE_ORDER and ackRisk=true.")

    preview = build_order_preview(payload, include_order_check=True)
    result = mt5.order_send(preview["request"])
    if result is None:
        raise RuntimeError(f"order_send failed: {mt5_last_error()}")

    result_payload = as_dict(result)
    done_codes = {
        getattr(mt5, "TRADE_RETCODE_DONE", 10009),
        getattr(mt5, "TRADE_RETCODE_PLACED", 10008),
    }

    return {
        "ok": as_int(result_payload.get("retcode")) in done_codes,
        "generatedAt": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "preview": preview,
        "result": result_payload,
    }


def order_sl_tp_from_history(
    orders_by_position: dict[int, list[dict[str, Any]]],
    orders_by_ticket: dict[int, dict[str, Any]],
    position_id: int,
    entry_rows: list[dict[str, Any]],
    deal_rows: list[dict[str, Any]],
) -> tuple[float, float]:
    stop_price = 0.0
    target_price = 0.0

    def use_first_nonzero(rows: list[dict[str, Any]]) -> None:
        nonlocal stop_price, target_price
        for row in rows:
            sl = as_float(row.get("sl"))
            tp = as_float(row.get("tp"))
            comment_sl, comment_tp = sl_tp_from_comment(row.get("comment"))
            if not stop_price and sl > 0:
                stop_price = sl
            if not target_price and tp > 0:
                target_price = tp
            if not stop_price and comment_sl > 0:
                stop_price = comment_sl
            if not target_price and comment_tp > 0:
                target_price = comment_tp
            if stop_price and target_price:
                return

    sorted_entry_deals = sorted(entry_rows, key=lambda item: as_int(item.get("time")))
    use_first_nonzero(sorted_entry_deals)

    entry_orders = [
        orders_by_ticket[order_ticket]
        for order_ticket in [as_int(deal.get("order")) for deal in sorted_entry_deals]
        if order_ticket and order_ticket in orders_by_ticket
    ]
    entry_orders.sort(key=lambda item: as_int(item.get("time_done") or item.get("time_setup") or item.get("time")))
    use_first_nonzero(entry_orders)

    position_orders = sorted(
        orders_by_position.get(position_id, []),
        key=lambda item: as_int(item.get("time_done") or item.get("time_setup") or item.get("time")),
    )
    use_first_nonzero(position_orders)

    sorted_deals = sorted(deal_rows, key=lambda item: as_int(item.get("time")))
    use_first_nonzero(sorted_deals)

    return stop_price, target_price


def deals_payload(days: int, account: dict[str, Any], since: datetime | None = None) -> list[dict[str, Any]]:
    date_to = datetime.now()
    date_from = date_to - timedelta(days=max(1, min(days, 365)))
    if since is not None:
        date_from = max(date_from, since.replace(tzinfo=None) - timedelta(days=1))
    deals = mt5.history_deals_get(date_from, date_to)
    if deals is None:
        return []

    orders = mt5.history_orders_get(date_from - timedelta(days=90), date_to)
    orders_by_position: dict[int, list[dict[str, Any]]] = {}
    orders_by_ticket: dict[int, dict[str, Any]] = {}
    if orders is not None:
        for order in orders:
            row = as_dict(order)
            ticket = as_int(row.get("ticket") or row.get("order"))
            position_id = as_int(row.get("position_id") or row.get("position"))
            if ticket:
                orders_by_ticket[ticket] = row
            if position_id:
                orders_by_position.setdefault(position_id, []).append(row)

    deal_type_buy = getattr(mt5, "DEAL_TYPE_BUY", 0)
    deal_type_sell = getattr(mt5, "DEAL_TYPE_SELL", 1)
    entry_in = getattr(mt5, "DEAL_ENTRY_IN", 0)
    entry_out = getattr(mt5, "DEAL_ENTRY_OUT", 1)
    entry_inout = getattr(mt5, "DEAL_ENTRY_INOUT", 2)
    entry_out_by = getattr(mt5, "DEAL_ENTRY_OUT_BY", 3)

    groups: dict[int, list[dict[str, Any]]] = {}
    for deal in deals:
        row = as_dict(deal)
        if as_int(row.get("type")) not in {deal_type_buy, deal_type_sell}:
            continue
        if not row.get("symbol") or as_float(row.get("volume")) <= 0:
            continue

        position_id = as_int(row.get("position_id") or row.get("position") or row.get("ticket"))
        if not position_id:
            continue
        groups.setdefault(position_id, []).append(row)

    imported: list[dict[str, Any]] = []
    for position_id, rows in groups.items():
        rows.sort(key=lambda item: as_int(item.get("time")))
        entry_rows = [row for row in rows if as_int(row.get("entry")) == entry_in]
        exit_rows = [row for row in rows if as_int(row.get("entry")) in {entry_out, entry_inout, entry_out_by}]
        if not entry_rows or not exit_rows:
            continue

        first_entry = entry_rows[0]
        last_exit = exit_rows[-1]
        direction = "long" if as_int(first_entry.get("type")) == deal_type_buy else "short"
        open_time = iso_from_seconds(first_entry.get("time"))
        close_time = iso_from_seconds(last_exit.get("time"))
        pnl_components = pnl_components_from_rows(rows)
        stop_price, target_price = order_sl_tp_from_history(
            orders_by_position,
            orders_by_ticket,
            position_id,
            entry_rows,
            rows,
        )

        imported.append(
            {
                "externalId": f"mt5:{account.get('login')}:{position_id}",
                "date": date_from_iso(close_time),
                "symbol": first_entry.get("symbol") or "",
                "direction": direction,
                "entryPrice": weighted_average(entry_rows, "price", "volume"),
                "stopPrice": stop_price,
                "targetPrice": target_price,
                "exitPrice": weighted_average(exit_rows, "price", "volume"),
                "quantity": sum(as_float(row.get("volume")) for row in exit_rows),
                **pnl_components,
                "currency": account.get("currency") or "USD",
                "accountValue": account_value(account),
                "comment": first_entry.get("comment") or last_exit.get("comment") or "",
                "openTime": open_time,
                "closeTime": close_time,
                "positionId": position_id,
                "ticket": as_int(last_exit.get("ticket")),
                "order": as_int(last_exit.get("order")),
                "magic": as_int(first_entry.get("magic")),
            }
        )

    imported.sort(key=lambda item: item["closeTime"], reverse=True)
    return filter_trades_since(imported, since)


def snapshot(days: int, since: datetime | None = None) -> dict[str, Any]:
    initialize_mt5()
    account = account_payload()
    deal_trades = deals_payload(days, account, since)
    ea_trades, ea_meta = ea_events_payload(days, account)
    ea_trades = filter_trades_since(ea_trades, since)
    return {
        "ok": True,
        "generatedAt": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "account": account,
        "positions": positions_payload(),
        "trades": merge_imported_trades(deal_trades, ea_trades),
        "dealTradeCount": len(deal_trades),
        "ea": ea_meta,
    }


def ea_events_response(days: int, since: datetime | None = None) -> dict[str, Any]:
    initialize_mt5()
    account = account_payload()
    trades, meta = ea_events_payload(days, account)
    trades = filter_trades_since(trades, since)
    return {
        "ok": True,
        "generatedAt": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "account": account,
        "trades": trades,
        "ea": meta,
    }


def sync_ea_events_to_journal(days: int = 14, since: datetime | None = None) -> dict[str, Any]:
    initialize_mt5()
    account = account_payload()
    # Always merge EA events against the broker ledger.  An EA `open` or
    # `update` event can arrive after the position has closed and contains a
    # stale floating PnL; importing it by itself would reopen the trade.
    deal_trades = deals_payload(days, account, since)
    ea_trades, meta = ea_events_payload(days, account)
    ea_trades = filter_trades_since(ea_trades, since)
    trades = merge_imported_trades(deal_trades, ea_trades)
    merge_result = merge_trades_into_journal(trades, account)
    return {
        "ok": True,
        "generatedAt": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "ea": meta,
        "journal": merge_result,
    }


def ea_watch_loop() -> None:
    last_signature = ""
    while not EA_WATCH_STOP.wait(EA_WATCH_INTERVAL_SECONDS):
        try:
            export_dir = ea_export_dir()
            if not (export_dir / EA_EVENT_FILE).exists() and not (export_dir / EA_EVENT_CSV_FILE).exists():
                continue
            signature = ea_events_file_signature(export_dir)
            if signature == last_signature:
                continue
            result = sync_ea_events_to_journal(14)
            last_signature = signature
            updated = result.get("journal", {}).get("updated", 0)
            if updated:
                print(f"EA watcher merged {updated} journal trade(s).")
        except Exception as exc:
            print(f"EA watcher skipped: {exc}")


def start_ea_watcher() -> Thread:
    thread = Thread(target=ea_watch_loop, name="mt5-ea-journal-watcher", daemon=True)
    thread.start()
    return thread


def live_position_watch_loop() -> None:
    tracked: dict[int, dict[str, Any]] = {}
    while not LIVE_WATCH_STOP.wait(LIVE_WATCH_INTERVAL_SECONDS):
        try:
            initialize_mt5()
            account = account_payload()
            positions = mt5.positions_get()
            if positions is None:
                continue

            current: dict[int, dict[str, Any]] = {}
            changed_imports: list[dict[str, Any]] = []
            for position in positions:
                row = as_dict(position)
                position_id = position_identifier(row)
                if not position_id:
                    continue
                current[position_id] = row
                previous = tracked.get(position_id)

                if previous is None:
                    changed_imports.append(imported_from_position(row, account, "open"))
                    continue

                changed = (
                    not math.isclose(as_float(previous.get("sl")), as_float(row.get("sl")), rel_tol=0, abs_tol=1e-10)
                    or not math.isclose(as_float(previous.get("tp")), as_float(row.get("tp")), rel_tol=0, abs_tol=1e-10)
                    or not math.isclose(as_float(previous.get("volume")), as_float(row.get("volume")), rel_tol=0, abs_tol=1e-10)
                    or not math.isclose(as_float(previous.get("price_current")), as_float(row.get("price_current")), rel_tol=0, abs_tol=1e-10)
                )
                if changed:
                    changed_imports.append(imported_from_position(row, account, "open"))

            for position_id, previous in list(tracked.items()):
                if position_id in current:
                    continue
                changed_imports.append(closed_imported_from_position(previous, account))

            if changed_imports:
                merge_result = merge_trades_into_journal(changed_imports, account)
                updated = merge_result.get("updated", 0)
                if updated:
                    print(f"Live watcher merged {updated} journal trade(s).")

            tracked = current
        except Exception as exc:
            print(f"Live watcher skipped: {exc}")


def start_live_position_watcher() -> Thread:
    thread = Thread(target=live_position_watch_loop, name="mt5-live-position-watcher", daemon=True)
    thread.start()
    return thread


def history_backfill_once(days: int = 14, since: datetime | None = None) -> dict[str, Any]:
    initialize_mt5()
    account = account_payload()
    deal_trades = deals_payload(days, account, since)
    ea_trades, _ = ea_events_payload(days, account)
    ea_trades = filter_trades_since(ea_trades, since)
    trades = merge_imported_trades(deal_trades, ea_trades)
    merge_result = merge_trades_into_journal(trades, account)
    return {
        "ok": True,
        "generatedAt": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "imported": len(trades),
        "journal": merge_result,
    }


def history_backfill_loop() -> None:
    while not HISTORY_WATCH_STOP.wait(HISTORY_BACKFILL_INTERVAL_SECONDS):
        try:
            result = history_backfill_once(14)
            updated = result.get("journal", {}).get("updated", 0)
            if updated:
                print(f"History backfill merged {updated} journal trade(s).")
        except Exception as exc:
            print(f"History backfill skipped: {exc}")


def start_history_backfill_watcher() -> Thread:
    thread = Thread(target=history_backfill_loop, name="mt5-history-backfill-watcher", daemon=True)
    thread.start()
    return thread


def replay_dataset_path(name: str) -> Path:
    filename = Path(str(name or "")).name
    if filename != str(name or "") or not filename.lower().endswith(".npz"):
        raise RuntimeError("Invalid replay dataset name.")
    path = (REPLAY_DATASET_DIR / filename).resolve()
    if path.parent != REPLAY_DATASET_DIR.resolve() or not path.is_file():
        raise RuntimeError(f"Replay dataset not found: {filename}")
    return path


def replay_dataset_metadata(path: Path) -> dict[str, Any]:
    if np is None:
        raise RuntimeError(f"NumPy is unavailable: {NUMPY_IMPORT_ERROR}")
    with np.load(path, allow_pickle=True) as payload:
        if "rates" not in payload.files:
            raise RuntimeError(f"Dataset has no rates array: {path.name}")
        rates = payload["rates"]
        if not rates.size:
            raise RuntimeError(f"Dataset is empty: {path.name}")
        metadata: dict[str, Any] = {}
        if "metadata" in payload.files:
            raw = payload["metadata"].item()
            try:
                decoded = json.loads(str(raw))
            except (json.JSONDecodeError, TypeError, ValueError):
                decoded = {}
            if isinstance(decoded, dict):
                metadata = decoded
        symbol = str(metadata.get("symbol") or path.stem.split("_M1", 1)[0] or "GOLD")
        default_point = 0.01 if symbol.upper() in {"GOLD", "XAUUSD"} else 0.00001
        return {
            "name": path.name,
            "size": path.stat().st_size,
            "symbol": symbol,
            "timeframe": str(metadata.get("timeframe") or "M1"),
            "point": float(metadata.get("point") or default_point),
            "firstTime": int(rates["time"][0]),
            "lastTime": int(rates["time"][-1]) + 60,
            "bars": int(rates.shape[0]),
        }


def replay_datasets_payload() -> dict[str, Any]:
    REPLAY_DATASET_DIR.mkdir(parents=True, exist_ok=True)
    datasets: list[dict[str, Any]] = []
    errors: list[str] = []
    for path in sorted(REPLAY_DATASET_DIR.glob("*.npz")):
        try:
            datasets.append(replay_dataset_metadata(path))
        except Exception as exc:
            errors.append(f"{path.name}: {exc}")
    return {
        "ok": True,
        "datasets": datasets,
        "errors": errors,
        "datasetDirectory": str(REPLAY_DATASET_DIR),
    }


def replay_timestamp(value: Any) -> int:
    text = str(value or "").strip()
    if not text:
        raise RuntimeError("Replay start time is required.")
    try:
        return int(float(text))
    except ValueError:
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError as exc:
            raise RuntimeError(f"Invalid replay start time: {text}") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return int(parsed.timestamp())


def replay_data_payload(dataset: str, start_value: Any, days: int, warmup_days: int) -> dict[str, Any]:
    if np is None:
        raise RuntimeError(f"NumPy is unavailable: {NUMPY_IMPORT_ERROR}")
    path = replay_dataset_path(dataset)
    replay_start = replay_timestamp(start_value)
    replay_days = min(max(int(days), 1), 14)
    history_days = min(max(int(warmup_days), 1), 30)
    replay_end = replay_start + replay_days * 86400
    source_start = replay_start - history_days * 86400
    metadata = replay_dataset_metadata(path)
    point = float(metadata["point"])

    with np.load(path, allow_pickle=True) as payload:
        rates = payload["rates"]
        mask = (rates["time"] >= source_start) & (rates["time"] < replay_end)
        selected = rates[mask]
        if not selected.size:
            raise RuntimeError("The selected replay range has no M1 bars.")
        if selected.shape[0] > REPLAY_MAX_BARS:
            raise RuntimeError(
                f"Replay range contains {selected.shape[0]:,} bars; limit is {REPLAY_MAX_BARS:,}."
            )
        fields = set(selected.dtype.names or ())
        spread_field = "spread" if "spread" in fields else None
        bars = [
            {
                "time": int(row["time"]),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "spread": float(row[spread_field]) * point if spread_field else 0.0,
            }
            for row in selected
        ]

    replay_bar_count = sum(1 for bar in bars if replay_start <= bar["time"] < replay_end)
    return {
        "ok": True,
        "dataset": metadata,
        "symbol": metadata["symbol"],
        "timeframe": "M1",
        "replayStart": replay_start,
        "replayEnd": replay_end,
        "sourceStart": int(bars[0]["time"]),
        "bars": bars,
        "replayBars": replay_bar_count,
        "warmupBars": len(bars) - replay_bar_count,
    }


def replay_session_id(value: Any) -> str:
    session_id = str(value or "").strip()
    if not REPLAY_SESSION_ID_PATTERN.fullmatch(session_id):
        raise RuntimeError("Invalid replay session id.")
    return session_id


def replay_sessions_payload() -> dict[str, Any]:
    connection = connect_journal_db()
    try:
        rows = connection.execute(
            """
            SELECT id, name, symbol, dataset, week_start, created_at, updated_at, data
            FROM replay_sessions
            ORDER BY updated_at DESC
            """
        ).fetchall()
    finally:
        connection.close()
    sessions: list[dict[str, Any]] = []
    for row in rows:
        try:
            data = json.loads(row["data"])
        except json.JSONDecodeError:
            data = {}
        sessions.append(
            {
                "id": row["id"],
                "name": row["name"],
                "symbol": row["symbol"],
                "dataset": row["dataset"],
                "weekStart": int(row["week_start"]),
                "createdAt": row["created_at"],
                "updatedAt": row["updated_at"],
                "cursorTime": as_int(data.get("cursorTime")),
                "maxSeenTime": as_int(data.get("maxSeenTime")),
                "eventCount": len(data.get("events") or []),
                "drawingCount": len(data.get("drawings") or []),
                "orderCount": len(data.get("orders") or []),
            }
        )
    return {"ok": True, "sessions": sessions, "storage": str(JOURNAL_DB_FILE)}


def replay_session_payload(session_id: str) -> dict[str, Any]:
    normalized = replay_session_id(session_id)
    connection = connect_journal_db()
    try:
        row = connection.execute("SELECT data FROM replay_sessions WHERE id=?", (normalized,)).fetchone()
    finally:
        connection.close()
    if row is None:
        raise RuntimeError("Replay session not found.")
    return {"ok": True, "session": json.loads(row["data"]), "storage": str(JOURNAL_DB_FILE)}


def save_replay_session(payload: dict[str, Any]) -> dict[str, Any]:
    session_id = replay_session_id(payload.get("id"))
    name = str(payload.get("name") or "이름 없는 재생").strip()[:120]
    symbol = str(payload.get("symbol") or "GOLD").strip().upper()[:32]
    dataset = replay_dataset_path(str(payload.get("dataset") or "")).name
    week_start = as_int(payload.get("weekStart"))
    if week_start <= 0:
        raise RuntimeError("Replay weekStart is required.")
    now = journal_updated_at()
    normalized = dict(payload)
    normalized.update(
        {
            "id": session_id,
            "name": name,
            "symbol": symbol,
            "dataset": dataset,
            "weekStart": week_start,
            "updatedAt": now,
        }
    )
    connection = connect_journal_db()
    try:
        existing = connection.execute(
            "SELECT created_at FROM replay_sessions WHERE id=?",
            (session_id,),
        ).fetchone()
        created_at = str(existing["created_at"] if existing else normalized.get("createdAt") or now)
        normalized["createdAt"] = created_at
        encoded = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))
        connection.execute(
            """
            INSERT INTO replay_sessions (id, name, symbol, dataset, week_start, created_at, updated_at, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                symbol=excluded.symbol,
                dataset=excluded.dataset,
                week_start=excluded.week_start,
                updated_at=excluded.updated_at,
                data=excluded.data
            """,
            (session_id, name, symbol, dataset, week_start, created_at, now, encoded),
        )
        connection.commit()
    finally:
        connection.close()
    return {"ok": True, "session": normalized, "storage": str(JOURNAL_DB_FILE)}


def delete_replay_session(session_id: str) -> dict[str, Any]:
    normalized = replay_session_id(session_id)
    connection = connect_journal_db()
    try:
        cursor = connection.execute("DELETE FROM replay_sessions WHERE id=?", (normalized,))
        connection.commit()
        deleted = cursor.rowcount > 0
    finally:
        connection.close()
    return {"ok": True, "deleted": deleted, "id": normalized}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_json(200, {"ok": True})

    def read_json_body(self) -> dict[str, Any]:
        length = as_int(self.headers.get("Content-Length"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON body: {exc}") from exc
        if not isinstance(data, dict):
            raise RuntimeError("JSON body must be an object.")
        return data

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path == "/health":
            ea_dir = ""
            ea_event_path = ""
            ea_csv_path = ""
            try:
                if mt5 is not None:
                    initialize_mt5()
                    ea_dir = str(ea_export_dir())
                    ea_event_path = str(ea_export_dir() / EA_EVENT_FILE)
                    ea_csv_path = str(ea_export_dir() / EA_EVENT_CSV_FILE)
            except Exception:
                ea_dir = str(Path(EA_EXPORT_DIR)) if EA_EXPORT_DIR else ""
                ea_event_path = str(Path(EA_EXPORT_DIR) / EA_EVENT_FILE) if EA_EXPORT_DIR else ""
                ea_csv_path = str(Path(EA_EXPORT_DIR) / EA_EVENT_CSV_FILE) if EA_EXPORT_DIR else ""
            self.send_json(
                200,
                {
                    "ok": True,
                    "packageAvailable": mt5 is not None,
                    "importError": MT5_IMPORT_ERROR,
                    "journalStorage": str(JOURNAL_DB_FILE),
                    "legacyJournalStorage": str(JOURNAL_FILE),
                    "eaExportDir": ea_dir,
                    "eaEventFile": ea_event_path,
                    "eaEventCsvFile": ea_csv_path,
                    "eaWatchIntervalSeconds": EA_WATCH_INTERVAL_SECONDS,
                    "eaHeartbeatStaleSeconds": EA_HEARTBEAT_STALE_SECONDS,
                    "liveWatchIntervalSeconds": LIVE_WATCH_INTERVAL_SECONDS,
                    "historyBackfillIntervalSeconds": HISTORY_BACKFILL_INTERVAL_SECONDS,
                },
            )
            return

        if parsed.path == "/journal":
            self.send_json(200, journal_payload())
            return

        if parsed.path == "/replay/datasets":
            try:
                self.send_json(200, replay_datasets_payload())
            except Exception as exc:
                self.send_json(200, {"ok": False, "error": str(exc), "datasets": []})
            return

        if parsed.path == "/replay/data":
            dataset = str((query.get("dataset") or [""])[0]).strip()
            start = (query.get("start") or [""])[0]
            days = as_int((query.get("days") or ["7"])[0], 7)
            warmup_days = as_int((query.get("warmupDays") or ["14"])[0], 14)
            try:
                self.send_json(200, replay_data_payload(dataset, start, days, warmup_days))
            except Exception as exc:
                self.send_json(200, {"ok": False, "error": str(exc), "bars": []})
            return

        if parsed.path == "/replay/sessions":
            try:
                self.send_json(200, replay_sessions_payload())
            except Exception as exc:
                self.send_json(200, {"ok": False, "error": str(exc), "sessions": []})
            return

        if parsed.path.startswith("/replay/sessions/"):
            session_id = unquote(parsed.path.removeprefix("/replay/sessions/")).strip()
            try:
                self.send_json(200, replay_session_payload(session_id))
            except Exception as exc:
                self.send_json(200, {"ok": False, "error": str(exc)})
            return

        if parsed.path == "/snapshot":
            days = as_int((query.get("days") or ["14"])[0], 14)
            since = parse_since((query.get("since") or [""])[0])
            try:
                self.send_json(200, snapshot(days, since))
            except Exception as exc:
                self.send_json(
                    200,
                    {
                        "ok": False,
                        "error": str(exc),
                        "positions": [],
                        "trades": [],
                    },
                )
            return

        if parsed.path == "/ea-events":
            days = as_int((query.get("days") or ["14"])[0], 14)
            since = parse_since((query.get("since") or [""])[0])
            try:
                self.send_json(200, ea_events_response(days, since))
            except Exception as exc:
                self.send_json(
                    200,
                    {
                        "ok": False,
                        "error": str(exc),
                        "trades": [],
                    },
                )
            return

        if parsed.path == "/ea-sync":
            days = as_int((query.get("days") or ["14"])[0], 14)
            since = parse_since((query.get("since") or [""])[0])
            try:
                self.send_json(200, sync_ea_events_to_journal(days, since))
            except Exception as exc:
                self.send_json(
                    200,
                    {
                        "ok": False,
                        "error": str(exc),
                    },
                )
            return

        if parsed.path == "/backfill-sync":
            days = as_int((query.get("days") or ["14"])[0], 14)
            since = parse_since((query.get("since") or [""])[0])
            try:
                self.send_json(200, history_backfill_once(days, since))
            except Exception as exc:
                self.send_json(
                    200,
                    {
                        "ok": False,
                        "error": str(exc),
                    },
                )
            return

        if parsed.path == "/chart":
            symbol = str((query.get("symbol") or ["XAUUSD"])[0]).strip().upper()
            timeframe = str((query.get("timeframe") or ["M5"])[0]).strip().upper()
            bars = as_int((query.get("bars") or ["500"])[0], 500)
            try:
                self.send_json(200, chart_payload(symbol, timeframe, bars))
            except Exception as exc:
                self.send_json(
                    200,
                    {
                        "ok": False,
                        "error": str(exc),
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "bars": [],
                    },
                )
            return

        if parsed.path == "/live":
            symbol = str((query.get("symbol") or ["XAUUSD"])[0]).strip().upper()
            try:
                self.send_json(200, live_payload(symbol))
            except Exception as exc:
                self.send_json(
                    200,
                    {
                        "ok": False,
                        "error": str(exc),
                        "positions": [],
                    },
                )
            return

        if parsed.path == "/ai-feedback/preflight":
            trade_id = str((query.get("tradeId") or [""])[0]).strip()
            self.send_json(200, ai_feedback_preflight_payload(trade_id))
            return

        if parsed.path == "/ai-feedback/config":
            self.send_json(200, ai_feedback_config_payload())
            return

        if parsed.path.startswith("/ai-feedback/jobs/"):
            job_id = unquote(parsed.path.removeprefix("/ai-feedback/jobs/")).strip()
            self.send_json(200, ai_feedback_job_snapshot(job_id))
            return

        self.send_json(404, {"ok": False, "error": "Not found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            payload = self.read_json_body()

            if parsed.path == "/order/preview":
                self.send_json(200, {"ok": False, "error": "Web order entry is disabled. Use MT5 for execution."})
                return

            if parsed.path == "/order/send":
                self.send_json(200, {"ok": False, "error": "Web order entry is disabled. Use MT5 for execution."})
                return

            if parsed.path == "/journal":
                self.send_json(200, save_journal(payload))
                return

            if parsed.path == "/replay/sessions":
                self.send_json(200, save_replay_session(payload))
                return

            if parsed.path == "/ai-feedback/first-loss":
                self.send_json(200, generate_ai_feedback_payload(str(payload.get("tradeId") or "")))
                return

            if parsed.path == "/ai-feedback/batch":
                self.send_json(200, start_ai_feedback_batch_payload(payload))
                return

            if parsed.path == "/ai-feedback/config":
                self.send_json(200, save_ai_feedback_config(payload))
                return

            if parsed.path == "/client-error":
                self.send_json(200, save_client_error(payload))
                return

            self.send_json(404, {"ok": False, "error": "Not found"})
        except Exception as exc:
            self.send_json(200, {"ok": False, "error": str(exc)})

    def do_PATCH(self) -> None:
        parsed = urlparse(self.path)
        try:
            payload = self.read_json_body()
            if parsed.path.startswith("/trades/"):
                trade_id = unquote(parsed.path.removeprefix("/trades/")).strip()
                self.send_json(200, patch_trade_payload(trade_id, payload))
                return
            if parsed.path.startswith("/reviews/"):
                review_id = unquote(parsed.path.removeprefix("/reviews/")).strip()
                self.send_json(200, patch_review_payload(review_id, payload))
                return
            self.send_json(404, {"ok": False, "error": "Not found"})
        except Exception as exc:
            self.send_json(200, {"ok": False, "error": str(exc)})

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path.startswith("/trades/"):
                trade_id = unquote(parsed.path.removeprefix("/trades/")).strip()
                self.send_json(200, delete_trade_payload(trade_id))
                return
            if parsed.path.startswith("/reviews/"):
                review_id = unquote(parsed.path.removeprefix("/reviews/")).strip()
                self.send_json(200, delete_review_payload(review_id))
                return
            if parsed.path.startswith("/replay/sessions/"):
                session_id = unquote(parsed.path.removeprefix("/replay/sessions/")).strip()
                self.send_json(200, delete_replay_session(session_id))
                return
            self.send_json(404, {"ok": False, "error": "Not found"})
        except Exception as exc:
            self.send_json(200, {"ok": False, "error": str(exc)})


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    start_ea_watcher()
    start_live_position_watcher()
    start_history_backfill_watcher()
    print(f"MT5 bridge listening on http://{HOST}:{PORT}")
    print("Open XM MT5 terminal and log in before calling /snapshot.")
    print(f"EA watcher interval: {EA_WATCH_INTERVAL_SECONDS}s")
    print(f"Live position watcher interval: {LIVE_WATCH_INTERVAL_SECONDS}s")
    print(f"History backfill interval: {HISTORY_BACKFILL_INTERVAL_SECONDS}s")
    server.serve_forever()
