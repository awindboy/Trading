from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
LEGACY_JOURNAL = DATA_DIR / "journal.json"
CONTEXT_FILE = ROOT / "output" / "mentor_review" / "all" / "all_context.json"
MENTOR_DOC = ROOT / "output" / "mentor_review" / "all_trades_mentor_feedback.md"
JOURNAL_DB = Path(os.environ.get("TRADING_JOURNAL_DB", Path(os.environ["LOCALAPPDATA"]) / "TradingJournal" / "journal.db"))


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def parse_trade_sections(text: str) -> dict[int, tuple[str, list[str]]]:
    matches = list(re.finditer(r"^##\s+(\d+)\.\s+(.+)$", text, flags=re.MULTILINE))
    sections: dict[int, tuple[str, list[str]]] = {}
    for index, match in enumerate(matches):
        trade_index = int(match.group(1))
        title = match.group(2).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        paragraphs: list[str] = []
        for raw in re.split(r"\n\s*\n", body):
            paragraph = " ".join(line.strip() for line in raw.splitlines() if line.strip())
            if not paragraph or paragraph.startswith("이미지:"):
                continue
            if paragraph == "---" or paragraph.startswith("## "):
                continue
            paragraphs.append(paragraph)
        sections[trade_index] = (title, paragraphs)
    return sections


def mentor_feedback_by_trade_id() -> dict[str, dict[str, Any]]:
    context = load_json(CONTEXT_FILE)
    doc_text = MENTOR_DOC.read_text(encoding="utf-8")
    sections = parse_trade_sections(doc_text)
    result: dict[str, dict[str, Any]] = {}
    generated_at = now_iso()
    for item in context:
        if not isinstance(item, dict):
            continue
        index = int(item.get("index") or 0)
        trade_id = str(item.get("id") or "")
        if not index or not trade_id or index not in sections:
            continue
        title, paragraphs = sections[index]
        result[trade_id] = {
            "title": title,
            "generatedAt": generated_at,
            "source": str(MENTOR_DOC.relative_to(ROOT)).replace("\\", "/"),
            "paragraphs": paragraphs,
        }
    return result


def default_feedback(trade: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"mentor:{trade.get('id') or trade.get('externalId')}",
        "generatedAt": now_iso(),
        "mentor": "Codex / ICT 멘토",
        "version": "codex-mentor-review-v1",
        "usedBars": True,
        "analysisSource": "mt5-bars",
        "timeframes": [],
        "title": "심층 매매 피드백",
        "verdict": "거래별 MTF 구조와 손익 원인을 직접 복기한 피드백입니다.",
        "score": 3,
        "summary": "",
        "checklist": [],
        "feedback": [],
        "improvements": [],
        "nextRules": [],
        "journalNotes": [],
        "chartNotes": [],
    }


def attach_feedback(trade: dict[str, Any], mentor_review: dict[str, Any], updated_at: str) -> bool:
    feedback = trade.get("aiFeedback")
    if not isinstance(feedback, dict):
        feedback = default_feedback(trade)
    changed = feedback.get("mentorReview") != mentor_review
    feedback["mentorReview"] = mentor_review
    feedback["mentor"] = "Codex / ICT 멘토"
    feedback["title"] = "심층 매매 피드백"
    feedback["version"] = str(feedback.get("version") or "codex-mentor-review-v1")
    feedback["generatedAt"] = str(feedback.get("generatedAt") or updated_at)
    trade["aiFeedback"] = feedback
    trade["updatedAt"] = updated_at
    return changed


def update_sqlite(feedback_map: dict[str, dict[str, Any]], updated_at: str) -> int:
    if not JOURNAL_DB.exists():
        return 0
    changed = 0
    connection = sqlite3.connect(JOURNAL_DB, timeout=30)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA busy_timeout=30000")
        connection.execute("BEGIN IMMEDIATE")
        rows = connection.execute("SELECT id, external_id, sort_time, data FROM trades").fetchall()
        for row in rows:
            trade = json.loads(row["data"])
            key = str(trade.get("id") or row["id"] or "")
            external_key = str(trade.get("externalId") or row["external_id"] or "")
            mentor_review = feedback_map.get(key) or feedback_map.get(external_key)
            if not mentor_review:
                continue
            if attach_feedback(trade, mentor_review, updated_at):
                changed += 1
            connection.execute(
                """
                UPDATE trades
                SET updated_at=?, sort_time=?, data=?
                WHERE id=?
                """,
                (updated_at, str(row["sort_time"] or updated_at), json.dumps(trade, ensure_ascii=False), row["id"]),
            )
        connection.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('updatedAt', ?)", (updated_at,))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return changed


def update_legacy_json(feedback_map: dict[str, dict[str, Any]], updated_at: str) -> int:
    if not LEGACY_JOURNAL.exists():
        return 0
    payload = load_json(LEGACY_JOURNAL)
    trades = payload.get("trades") if isinstance(payload, dict) else []
    if not isinstance(trades, list):
        return 0
    changed = 0
    for trade in trades:
        if not isinstance(trade, dict):
            continue
        mentor_review = feedback_map.get(str(trade.get("id") or "")) or feedback_map.get(str(trade.get("externalId") or ""))
        if not mentor_review:
            continue
        if attach_feedback(trade, mentor_review, updated_at):
            changed += 1
    payload["updatedAt"] = updated_at
    backup = LEGACY_JOURNAL.with_suffix(f".mentor-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json")
    shutil.copy2(LEGACY_JOURNAL, backup)
    tmp = LEGACY_JOURNAL.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    tmp.replace(LEGACY_JOURNAL)
    return changed


def main() -> int:
    feedback_map = mentor_feedback_by_trade_id()
    if not feedback_map:
        raise SystemExit("No mentor feedback sections were matched.")
    updated_at = now_iso()
    sqlite_changed = update_sqlite(feedback_map, updated_at)
    legacy_changed = update_legacy_json(feedback_map, updated_at)
    print(f"MENTOR_FEEDBACK_IMPORT_OK matched={len(feedback_map)} sqliteChanged={sqlite_changed} legacyChanged={legacy_changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
