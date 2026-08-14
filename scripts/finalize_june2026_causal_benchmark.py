"""Finalize the outcome-selected June 2026 causal benchmark."""

from __future__ import annotations

import csv
import glob
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "output" / "mentor_june2026_causal_benchmark"


def load_jsonl(pattern: str) -> list[dict]:
    output: list[dict] = []
    for path in glob.glob(str(RUN / pattern)):
        with open(path, encoding="utf-8") as handle:
            output.extend(json.loads(line) for line in handle if line.strip())
    return output


def physical_key(item: dict) -> tuple[str, str, str, str]:
    result = item["result"]
    trade = result.get("trade") or result.get("replacement") or {}
    return (
        str(trade.get("filledAtUtc") or trade.get("entryAtUtc")),
        str(trade.get("entry")), str(trade.get("stop")),
        str(item["scenario"]["direction"]),
    )


def main() -> int:
    current = load_jsonl("formal_scenarios.part*.jsonl")
    closed = [item for item in current if item["result"]["status"] in {"TP", "SL"}]
    physical = {physical_key(item) for item in closed}

    june15 = next(
        item for item in closed
        if item["scenario"]["semanticHash"] == "305819f7e240e2e30c6318bb042e212f9ce11aa305c1453a5996c6f9caf9163a"
    )
    legacy_manifest = json.loads(
        (RUN / "semantic_trade_audit" / "manifest.json").read_text(encoding="utf-8")
    )
    june30_record = next(
        item for item in legacy_manifest
        if item["scenario"]["semanticHash"] == "1efb9f430c2eff852e8dd7e860ee5235b3ba7ae3973252034911b4d543c762bd"
    )
    june30 = {"scenario": june30_record["scenario"], "result": june30_record["result"]}
    selected = [june15, june30]

    trades: list[dict] = []
    for number, item in enumerate(selected, 1):
        scenario, result = item["scenario"], item["result"]
        raw = result.get("trade") or result.get("replacement")
        trades.append({
            "tradeId": f"J26-GT-{number:03d}",
            "decisionAtUtc": scenario["frozenAtUtc"],
            "entryAtUtc": raw.get("entryAtUtc") or raw.get("filledAtUtc"),
            "exitAtUtc": raw.get("exitAtUtc") or raw.get("closedAtUtc"),
            "direction": scenario["direction"], "scope": scenario["scope"],
            "executionModel": raw["model"] if "model" in raw else "DELIVERY_FVG_REPLACEMENT",
            "rootTf": scenario["root"]["tf"], "rootObBarId": scenario["root"]["obBarId"],
            "rootLow": scenario["root"]["low"], "rootHigh": scenario["root"]["high"],
            "childTf": scenario["finalChild"]["tf"], "childObBarId": scenario["finalChild"]["obBarId"],
            "childLow": scenario["finalChild"]["low"], "childHigh": scenario["finalChild"]["high"],
            "entry": raw["entry"], "stop": raw["stop"], "target": raw["target"],
            "objectiveBarId": scenario["objective"]["barId"],
            "result": "TP", "resultR": raw["resultR"],
            "semanticHash": scenario["semanticHash"],
            "auditStatus": "PROMOTED_ORACLE_CAUSAL",
        })

    fields = list(trades[0])
    with (RUN / "trades.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(trades)
    (RUN / "causal_benchmark.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in selected),
        encoding="utf-8",
    )

    promoted_candidates = {
        "J26-O-043": "J26-GT-001",
        "J26-O-088": "J26-GT-002",
    }
    with (RUN / "oracle_move_index.csv").open(encoding="utf-8-sig") as handle:
        candidates = list(csv.DictReader(handle))
    audit_rows = []
    for candidate in candidates:
        trade_id = promoted_candidates.get(candidate["candidateId"], "")
        audit_rows.append({
            "candidateId": candidate["candidateId"],
            "direction": candidate["direction"],
            "pivotTimeUtc": candidate["pivotTimeUtc"],
            "grossMove": candidate["grossMove"],
            "decision": "PROMOTED" if trade_id else "NOT_PROMOTED",
            "tradeId": trade_id,
            "reason": (
                "FULL_AGENTS_CHAIN_AND_CAUSAL_ASOF_EVIDENCE"
                if trade_id else
                "NO_UNIQUE_COMPLETE_AGENTS_CHAIN_AFTER_DEDUP_AND_OVERLAP_AUDIT"
            ),
        })
    with (RUN / "candidate_audit.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(audit_rows[0]))
        writer.writeheader(); writer.writerows(audit_rows)

    total_r = sum(float(item["resultR"]) for item in trades)
    summary = {
        "benchmarkType": "OUTCOME_SELECTED_ORACLE_CAUSAL_UPPER_BOUND",
        "period": "2026-06-01 through 2026-06-30 UTC",
        "historyStartUtc": "2023-12-01T01:00:00Z",
        "grossMoveCandidatesAudited": len(candidates),
        "formalScenarioOptions": sum(
            len(json.loads(path.read_text(encoding="utf-8")))
            for path in RUN.glob("formal_scenario_index_v2_pretouch.part*.json")
        ),
        "cleanChildTouchFormalCandidates": sum(
            sum(1 for row in csv.DictReader(path.open(encoding="utf-8-sig")) if row["status"] == "KEEP")
            for path in RUN.glob("event_race_prefilter_v2_pretouch.part*.csv")
        ),
        "formalClosedRecords": len(closed),
        "physicalClosedCandidates": len(physical),
        "promotedTrades": len(trades),
        "wins": len(trades), "losses": 0, "winRatePercent": 100.0,
        "totalR": total_r, "expectancyR": total_r / len(trades),
        "profitFactor": None, "maxDrawdownR": 0.0,
        "selectionBiasWarning": (
            "This benchmark used future outcomes only to select the best rule-compliant scenarios. "
            "It is an in-sample upper bound, not a blind/live performance estimate."
        ),
    }
    (RUN / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = f"""# 2026-06 Mentor Oracle/Causal Benchmark

## 결론

- 분류: **결과 참조형 in-sample 상한 정답지**
- 승격 거래: **{len(trades)}건**
- 합계: **+{total_r:.4f}R**
- 승률: **100% (2/2)**
- Profit Factor: **정의 불가(확정 손실 0건)**
- 최대 낙폭: **0R**

이 결과는 블라인드 기대수익이 아니다. 월 전체 결과를 이용해 수익 가능 구간을 찾은 뒤,
각 시점으로 되감아 `AGENTS.md`의 root OB, causal child, objective, trigger, SL/TP 계약을
모두 만족한 경우만 승격한 **설명 가능한 최적 상한**이다.

## 승격 거래

| ID | 진입 UTC | 방향/범위 | 실행 | Entry | SL | TP | 결과 |
|---|---|---|---|---:|---:|---:|---:|
| J26-GT-001 | {trades[0]['entryAtUtc']} | LONG / EXTERNAL_CONTINUATION | DELIVERY_FVG_REPLACEMENT | {float(trades[0]['entry']):.2f} | {float(trades[0]['stop']):.2f} | {float(trades[0]['target']):.2f} | +{float(trades[0]['resultR']):.4f}R |
| J26-GT-002 | {trades[1]['entryAtUtc']} | SHORT / EXTERNAL_CONTINUATION | HTF_OB_REACTION | {float(trades[1]['entry']):.2f} | {float(trades[1]['stop']):.2f} | {float(trades[1]['target']):.2f} | +{float(trades[1]['resultR']):.4f}R |

## 엄격 감사 범위

- 원본 M1 2023-12-01부터 연결하여 6월 이전 HTF 구조와 과거 유동성을 포함했다.
- 6월 양방향 gross move 94개를 빠짐없이 후보화했다.
- 후보 시점은 결과 pivot 이후가 아니라 pivot 직전으로 되감아 시나리오를 재구성했다.
- 형식 시나리오 504개 중 clean child touch 126개를 M1 사건 순서로 재생했다.
- 형식상 종료 49건, 중복 제거 후 물리적 체결 30개를 분리했다.
- 동일 entry에 objective만 바뀐 중복, 동시 포지션, 근거가 불완전한 Delivery FVG는 승격하지 않았다.
- 6월 신규 진입만 허용하고, 6월 말 포지션의 종료만 이후 데이터로 추적했다.

## 해석 경계

정답지의 100% 승률은 전략의 실전 승률이 아니다. 결과를 알고 가장 좋은 두 시나리오를 선택했기
때문이다. 다음 재현성 검증의 질문은 Gemini가 미래 정보 없이 이 두 시나리오를 선택하는지,
그리고 불완전 후보를 얼마나 거절하는지다.
"""
    (RUN / "FINAL_REPORT.md").write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
