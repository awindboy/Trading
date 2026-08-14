from __future__ import annotations

import argparse
import json
from pathlib import Path

from .data import load_m1_npz, parse_utc
from .engine import MentorScenarioEngine
from .models import EngineConfig
from .regression import validate_q1_regression
from .reporting import write_artifacts


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay the Mentor Scenario Engine")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2025-12-31.npz",
    )
    parser.add_argument("--warmup-from", default="2024-10-01T00:00:00+00:00")
    parser.add_argument("--trade-from", default="2025-01-01T00:00:00+00:00")
    parser.add_argument("--to", default="2025-04-01T00:00:00+00:00")
    parser.add_argument(
        "--casebook",
        type=Path,
        default=ROOT / "research" / "mentor-youtube" / "MENTOR_CASEBOOK.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "output" / "mentor_engine" / "GOLD_2025_Q1",
    )
    parser.add_argument("--no-charts", action="store_true")
    parser.add_argument(
        "--q1-fixtures",
        type=Path,
        default=ROOT
        / "research"
        / "mentor-youtube"
        / "Q1_SCENARIO_REVIEW_FIXTURES.json",
    )
    parser.add_argument("--skip-q1-regression", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    warmup_from = parse_utc(args.warmup_from)
    trade_from = parse_utc(args.trade_from)
    trade_to = parse_utc(args.to)
    m1, metadata = load_m1_npz(args.dataset, warmup_from, trade_to)
    engine = MentorScenarioEngine(
        m1,
        EngineConfig(trade_from=trade_from, trade_to=trade_to),
    )
    summary = engine.run()
    casebook = engine.validate_casebook(args.casebook)
    q1_regression = None
    if not args.skip_q1_regression:
        q1_regression = validate_q1_regression(
            engine.orders, engine.scenarios, args.q1_fixtures
        )
    artifacts = write_artifacts(
        engine,
        args.output,
        casebook,
        q1_regression=q1_regression,
        charts=not args.no_charts,
    )
    print("MENTOR_ENGINE_REPLAY_OK")
    print(f"dataset={metadata.get('symbol')} bars={len(m1)}")
    print(json.dumps(summary["funnel"], ensure_ascii=False))
    print(json.dumps(summary["economics"], ensure_ascii=False))
    print(f"casebookSemanticCoverage={casebook['semanticCoverage']:.4f}")
    print(f"casebookReplayEligible={casebook['replayEligibleCases']}")
    if q1_regression is not None:
        print(f"q1RegressionPassed={q1_regression['passed']}")
        print(f"q1RegressionViolations={len(q1_regression['violations'])}")
    print(f"summary={artifacts['summary'].resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
