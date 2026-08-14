from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.gemini_replay_provider import GeminiReplayError
from scripts.mentor_ai_live_v4 import (
    CHECKPOINT_NAME,
    assert_demo_order_gate,
    merge_rates,
    local_wait_events,
    process_closed_bars,
    recover_interrupted_bar,
    resolve_broker_utc_offset,
    normalize_broker_time,
    reconcile_broker_snapshot,
    validate_feed_clock,
)
from scripts.mentor_replay_v4_core import MarketData, V4ContractError, new_runtime


DTYPE = np.dtype(
    [
        ("time", "<i8"),
        ("open", "<f8"),
        ("high", "<f8"),
        ("low", "<f8"),
        ("close", "<f8"),
        ("tick_volume", "<i8"),
        ("spread", "<i4"),
        ("real_volume", "<i8"),
    ]
)


def rates(start: int, count: int) -> np.ndarray:
    output = np.zeros(count, dtype=DTYPE)
    output["time"] = start + np.arange(count) * 60
    output["open"] = 100 + np.arange(count) * 0.1
    output["high"] = output["open"] + 0.2
    output["low"] = output["open"] - 0.2
    output["close"] = output["open"] + 0.05
    output["tick_volume"] = 10
    output["spread"] = 20
    return output


class FakeRunner:
    def __init__(self, root: Path, market: MarketData, state: str = "PLANNED") -> None:
        self.run_dir = root
        self.market = market
        self.runtime = new_runtime(0)
        self.runtime["state"] = state
        if state != "FLAT":
            self.runtime["scenario"] = {"placeholder": True}
        self.stats = {
            "semanticRequests": 0,
            "providerApiCalls": 0,
            "totalTokens": 0,
            "planRequests": 0,
            "flatZeroTokenBars": 0,
            "activeZeroTokenBars": 0,
        }
        self.processed: list[str] = []

    def process_bar(self, row: dict[str, object]) -> None:
        self.processed.append(str(row["barId"]))

    def advance_closed_m1_bar(
        self,
        row: dict[str, object],
        *,
        planning_enabled: bool,
        api_allowed: bool,
    ) -> dict[str, int]:
        self.process_bar(row)
        self.runtime["cursor"] = int(self.runtime["cursor"]) + 1
        if self.runtime["state"] == "FLAT":
            self.stats["flatZeroTokenBars"] += 1
        else:
            self.stats["activeZeroTokenBars"] += 1
        return {"planRequests": 0}

    def latest_h1_available(self, _: int) -> None:
        return None

    def schedule_flat_plan(self, _: int, *, api_allowed: bool = True) -> bool:
        if api_allowed:
            self.stats["planRequests"] += 1
            return True
        return False

    def schedule_event_driven_flat_plan(
        self, _: dict[str, object], *, api_allowed: bool = True
    ) -> bool:
        return False

    def save(self) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        (self.run_dir / "state.json").write_text(
            json.dumps(self.runtime), encoding="utf-8"
        )


def test_market_data_from_live_rates_and_append_only_merge() -> None:
    first = rates(1_700_000_000, 120)
    market = MarketData.from_rates(first, 0.01)
    assert len(market.frames["M1"]) == 120
    assert len(market.frames["H1"]) >= 2
    overlap = np.concatenate((first[-2:], rates(int(first[-1]["time"]) + 60, 2)))
    merged = merge_rates(first, overlap)
    assert len(merged) == 122
    assert np.array_equal(merged[:120], first)


def test_feed_staleness_and_demo_gate_fail_closed() -> None:
    assert validate_feed_clock(
        {"serverNow": 1_000}, local_now=1_020, stale_seconds=180,
        max_clock_skew_seconds=30,
    ) == (True, None)
    healthy, reason = validate_feed_clock(
        {"serverNow": 1_000}, local_now=1_500, stale_seconds=180,
        max_clock_skew_seconds=30,
    )
    assert not healthy and reason and reason.startswith("STALE_MARKET_DATA")
    assert_demo_order_gate(
        {"tradeMode": 1, "demoTradeMode": 0, "terminalConnected": True, "tradeAllowed": True},
        False,
    )
    try:
        assert_demo_order_gate(
            {"tradeMode": 1, "demoTradeMode": 0, "terminalConnected": True, "tradeAllowed": True},
            True,
        )
    except V4ContractError as exc:
        assert "not DEMO" in str(exc)
    else:
        raise AssertionError("real account was not rejected")


def test_broker_reconciliation_is_idempotent_and_fail_closed() -> None:
    runtime = new_runtime(0)
    assert reconcile_broker_snapshot(
        runtime, {"orders": [], "positions": []}
    )["status"] == "MATCHED"
    runtime["orders"] = [{
        "orderId": "one",
        "clientId": "MENTOR-one",
        "status": "PENDING",
        "brokerSubmitted": True,
    }]
    matched = reconcile_broker_snapshot(
        runtime,
        {
            "orders": [{"comment": "MENTOR-one", "ticket": 1}],
            "positions": [],
        },
    )
    assert matched["brokerMentorRecords"] == 1
    try:
        reconcile_broker_snapshot(
            runtime,
            {
                "orders": [{"comment": "MENTOR-unknown", "ticket": 2}],
                "positions": [],
            },
        )
    except V4ContractError as exc:
        assert "UNKNOWN_MENTOR_ORDER" in str(exc)
    else:
        raise AssertionError("unknown broker order did not fail closed")


def test_xm_server_clock_is_normalized_before_live_processing() -> None:
    local_now = 1_700_000_000
    offset = resolve_broker_utc_offset(
        raw_server_now=local_now + 3 * 3600,
        local_now=local_now,
        max_clock_skew_seconds=30,
    )
    assert offset == 3 * 3600
    raw = rates(local_now + 3 * 3600 - 120, 2)
    normalized, snapshot = normalize_broker_time(
        raw, {"serverNow": local_now + 3 * 3600}, offset
    )
    assert int(normalized[0]["time"]) == local_now - 120
    assert snapshot["serverNow"] == local_now
    assert validate_feed_clock(
        snapshot, local_now=local_now, stale_seconds=180,
        max_clock_skew_seconds=30,
    ) == (True, None)


def test_interrupted_bar_restores_state_and_truncates_partial_writes() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        ledger = root / "decision_ledger.jsonl"
        trades = root / "trades.jsonl"
        ledger.write_bytes(b"good\npartial\n")
        trades.write_bytes(b"trade\npartial\n")
        runtime = new_runtime(7)
        (root / CHECKPOINT_NAME).write_text(
            json.dumps(
                {
                    "runtimeBefore": runtime,
                    "ledgerBytes": len(b"good\n"),
                    "tradesBytes": len(b"trade\n"),
                }
            ),
            encoding="utf-8",
        )
        assert recover_interrupted_bar(root)
        assert ledger.read_bytes() == b"good\n"
        assert trades.read_bytes() == b"trade\n"
        assert json.loads((root / "state.json").read_text(encoding="utf-8"))["cursor"] == 7


def test_active_wait_processes_closed_m1_without_semantic_tokens() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        market = MarketData.from_rates(rates(1_700_000_000, 3), 0.01)
        runner = FakeRunner(root, market, "PLANNED")
        processed = process_closed_bars(
            runner, server_now=int(market.rates[-1]["time"]) + 60,
            daily_plan_limit=12,
        )
        assert processed == 3
        assert len(runner.processed) == 3
        assert runner.stats["semanticRequests"] == 0
        assert runner.stats["totalTokens"] == 0
        assert runner.stats["activeZeroTokenBars"] == 3
        assert runner.stats["planRequests"] == 0


def test_twelve_hour_active_wait_survives_restart_without_tokens() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        first_market = MarketData.from_rates(rates(1_700_000_000, 360), 0.01)
        first = FakeRunner(root, first_market, "PLANNED")
        assert process_closed_bars(
            first,
            server_now=int(first_market.rates[-1]["time"]) + 60,
            daily_plan_limit=12,
        ) == 360
        assert first.stats["semanticRequests"] == 0
        assert first.stats["providerApiCalls"] == 0
        assert first.stats["totalTokens"] == 0

        second_market = MarketData.from_rates(rates(1_700_000_000, 720), 0.01)
        second = FakeRunner(root, second_market, "PLANNED")
        second.runtime = json.loads((root / "state.json").read_text(encoding="utf-8"))
        second.stats = dict(first.stats)
        assert process_closed_bars(
            second,
            server_now=int(second_market.rates[-1]["time"]) + 60,
            daily_plan_limit=12,
        ) == 360
        assert second.runtime["cursor"] == 720
        assert second.stats["semanticRequests"] == 0
        assert second.stats["providerApiCalls"] == 0
        assert second.stats["totalTokens"] == 0
        assert second.stats["activeZeroTokenBars"] == 720
        assert local_wait_events("PLANNED").startswith("CHILD_TOUCH")


def test_provider_failure_keeps_same_bar_for_safe_retry() -> None:
    class FailingRunner(FakeRunner):
        def advance_closed_m1_bar(
            self,
            row: dict[str, object],
            *,
            planning_enabled: bool,
            api_allowed: bool,
        ) -> dict[str, int]:
            raise GeminiReplayError("Gemini HTTP 503", request_was_sent=True)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        market = MarketData.from_rates(rates(1_700_000_000, 2), 0.01)
        runner = FailingRunner(root, market, "PLANNED")
        try:
            process_closed_bars(
                runner, server_now=int(market.rates[-1]["time"]) + 60,
                daily_plan_limit=12,
            )
        except GeminiReplayError:
            pass
        else:
            raise AssertionError("provider failure did not propagate")
        assert runner.runtime["cursor"] == 0
        assert not (root / CHECKPOINT_NAME).exists()


def main() -> int:
    test_market_data_from_live_rates_and_append_only_merge()
    test_feed_staleness_and_demo_gate_fail_closed()
    test_broker_reconciliation_is_idempotent_and_fail_closed()
    test_xm_server_clock_is_normalized_before_live_processing()
    test_interrupted_bar_restores_state_and_truncates_partial_writes()
    test_active_wait_processes_closed_m1_without_semantic_tokens()
    test_twelve_hour_active_wait_survives_restart_without_tokens()
    test_provider_failure_keeps_same_bar_for_safe_retry()
    print("MENTOR_AI_LIVE_V4_TESTS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
