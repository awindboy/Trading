from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
import json
from pathlib import Path
import random
import shutil
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_ground_truth_v2 import (
    HashChainWriter,
    authority_at,
    read_jsonl,
    sha256_file,
    validate_scenario_authority_at_order,
    validate_stateful_plan_sequence,
)
from scripts.codex_replay_provider import generate_codex_decision
from scripts.mentor_ai_replay_v4 import (
    CodexCliProvider,
    DEFAULTS,
    ScriptedProvider,
    V4Runner,
    prompt_for,
    render_images,
)
from scripts.mentor_replay_v4_core import (
    MarketData,
    V4ContractError,
    external_authority_from_scenario,
    freeze_plan_batch,
    new_runtime,
    parse_utc,
    plan_schema,
    trigger_watch_schema,
    delivery_review_schema,
    utc_text,
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def semantic_signature(phase: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Compare only fields that authorize or reject a semantic transition."""
    if phase == "PLAN":
        decisions = []
        for decision in payload.get("decisions", []):
            decisions.append({
                "familyId": str(decision.get("familyId", "")),
                "action": str(decision.get("action", "")),
                "scenarioSelectionId": decision.get("scenarioSelectionId"),
                "semanticAudit": decision.get("semanticAudit") or {},
            })
        return {"decisions": sorted(decisions, key=lambda item: item["familyId"])}
    if phase == "TRIGGER_WATCH":
        return {
            key: payload.get(key)
            for key in (
                "action", "matureLiquidityBarId", "m5CorrectionSwingBarId",
                "chochReferenceBarId", "chochBreakBarId",
                "sourceUpgradeSelectionId",
            )
        }
    if phase == "DELIVERY_REVIEW":
        return {
            key: payload.get(key)
            for key in (
                "candidateId", "action", "sourceEpisodeContinuity",
                "ownerObjectiveContinuity", "meaningfulStructureTransfer",
                "causalFvgAndOb", "firstRetestEligibility",
            )
        }
    raise V4ContractError(f"unsupported stateful semantic phase: {phase}")


def schema_for_phase(phase: str, packet: dict[str, Any]) -> dict[str, Any]:
    if phase == "PLAN":
        return plan_schema(packet)
    if phase == "TRIGGER_WATCH":
        return trigger_watch_schema(packet)
    if phase == "DELIVERY_REVIEW":
        return delivery_review_schema(packet)
    raise V4ContractError(f"unsupported stateful semantic phase: {phase}")


def run_stateful_repeat_audit(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    summary = read_json(run_dir / "summary.json")
    if summary.get("completed") is not True:
        raise V4ContractError("stateful source run is not complete")
    ledger_rows = read_jsonl(run_dir / "decision_ledger.jsonl")
    sequence_by_request: dict[str, int] = {}
    for row in ledger_rows:
        details = row.get("details") or {}
        request_id = details.get("requestId")
        if not request_id and isinstance(details.get("review"), dict):
            request_id = details["review"].get("requestId")
        if request_id:
            sequence_by_request[str(request_id)] = int(row.get("sequence", 0))

    requests: list[dict[str, Any]] = []
    for request_dir in (run_dir / "requests").iterdir():
        if not request_dir.is_dir():
            continue
        request_path = request_dir / "request.json"
        packet_path = request_dir / "packet.json"
        response_path = request_dir / "response.json"
        if not (request_path.exists() and packet_path.exists() and response_path.exists()):
            continue
        request = read_json(request_path)
        phase = str(request.get("phase", ""))
        if phase not in {"PLAN", "TRIGGER_WATCH", "DELIVERY_REVIEW"}:
            continue
        request_id = str(request["requestId"])
        requests.append({
            "requestId": request_id,
            "phase": phase,
            "asOfUtc": str(request["asOfUtc"]),
            "sequence": sequence_by_request.get(request_id, 10**12),
            "requestDir": request_dir,
            "request": request,
        })
    requests.sort(key=lambda item: (item["sequence"], item["requestId"]))
    audit_type = str(args.audit_type)
    if audit_type == "COUNTERFACTUAL_SHUFFLED":
        random.Random(int(args.seed)).shuffle(requests)
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    result_dir = output / "results"
    result_dir.mkdir(parents=True, exist_ok=True)

    def repeat(item: dict[str, Any]) -> dict[str, Any]:
        request_dir = Path(item["requestDir"])
        packet = read_json(request_dir / "packet.json")
        source = read_json(request_dir / "response.json")["payload"]
        images: list[Path] = []
        for image in item["request"].get("images", []):
            path = Path(str(image["path"]))
            if not path.exists():
                raise V4ContractError(
                    f"stateful audit image is missing: {item['requestId']}:{path}"
                )
            if sha256_file(path) != str(image.get("sha256", "")):
                raise V4ContractError(
                    f"stateful audit image hash changed: {item['requestId']}:{path}"
                )
            images.append(path)
        repeated = generate_codex_decision(
            request_dir=result_dir / item["requestId"],
            prompt=prompt_for(item["phase"], packet),
            images=images,
            schema=schema_for_phase(item["phase"], packet),
            model="gpt-5.6-sol",
            reasoning_effort=str(args.reasoning_effort),
            timeout_seconds=1800,
        ).payload
        source_signature = semantic_signature(item["phase"], source)
        repeated_signature = semantic_signature(item["phase"], repeated)
        return {
            "auditType": audit_type,
            "auditorId": str(args.auditor_id),
            "auditSessionId": str(args.audit_session_id),
            "requestId": item["requestId"],
            "sourceSequence": item["sequence"],
            "asOfUtc": item["asOfUtc"],
            "phase": item["phase"],
            "sourceSignature": source_signature,
            "repeatedSignature": repeated_signature,
            "verdict": "MATCH" if source_signature == repeated_signature else "MISMATCH",
        }

    completed: dict[str, dict[str, Any]] = {}
    raw_path = output / "raw_results.jsonl"
    if raw_path.exists():
        completed = {
            str(item["requestId"]): item for item in read_jsonl(raw_path)
        }
    jobs = [item for item in requests if item["requestId"] not in completed]
    with ThreadPoolExecutor(max_workers=max(1, int(args.workers))) as pool:
        futures = {pool.submit(repeat, item): item for item in jobs}
        for future in as_completed(futures):
            result = future.result()
            completed[str(result["requestId"])] = result
            raw_path.write_text(
                "".join(
                    json.dumps(completed[item["requestId"]], ensure_ascii=False,
                               separators=(",", ":")) + "\n"
                    for item in requests if item["requestId"] in completed
                ),
                encoding="utf-8",
                newline="\n",
            )
    if len(completed) != len(requests):
        raise V4ContractError("stateful semantic repeat audit is incomplete")
    ledger_path = output / "semantic_repeat_audit.jsonl"
    writer = HashChainWriter(ledger_path)
    writer.append_many([completed[item["requestId"]] for item in requests])
    mismatches = [item for item in completed.values() if item["verdict"] != "MATCH"]
    report = {
        "auditType": audit_type,
        "sourceRun": str(run_dir),
        "requests": len(requests),
        "matches": len(requests) - len(mismatches),
        "mismatches": len(mismatches),
        "mismatchRequestIds": sorted(item["requestId"] for item in mismatches),
        "ledger": str(ledger_path),
        "ledgerSha256": sha256_file(ledger_path),
    }
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if mismatches:
        raise V4ContractError(
            f"stateful semantic repeat mismatch count={len(mismatches)}"
        )
    print(
        f"GROUND_TRUTH_V2_STATEFUL_REPEAT_OK type={audit_type} "
        f"requests={len(requests)} output={ledger_path}"
    )
    return 0


def audit_plan_page(
    request_dir: Path,
    packet: dict[str, Any],
    images: list[Path],
    reasoning_effort: str,
) -> dict[str, Any]:
    response = generate_codex_decision(
        request_dir=request_dir,
        prompt=prompt_for("PLAN", packet),
        images=images,
        schema=plan_schema(packet),
        model="gpt-5.6-sol",
        reasoning_effort=reasoning_effort,
        timeout_seconds=1800,
    )
    return response.payload


def selected_decisions(payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        decision
        for payload in payloads
        for decision in payload.get("decisions", [])
        if decision.get("action") == "PLAN"
        and decision.get("scenarioSelectionId")
        and all(
            verdict == "PASS"
            for verdict in (decision.get("semanticAudit") or {}).values()
        )
    ]


def audit_family(
    *,
    packet: dict[str, Any],
    family: dict[str, Any],
    runner: V4Runner,
    config: dict[str, Any],
    request_root: Path,
    shared_image_root: Path,
    reasoning_effort: str,
) -> dict[str, Any]:
    as_of = parse_utc(str(packet["asOfUtc"]))
    family_id = str(family["familyId"])
    request_root.mkdir(parents=True, exist_ok=True)
    image_dir = shared_image_root / str(as_of)
    image_dir.mkdir(parents=True, exist_ok=True)
    images = sorted(image_dir.glob("*.png"))
    if not images:
        images = render_images(config, "PLAN", as_of, image_dir)
    compact = runner.compact_plan_page(packet, [family], as_of)
    maximum = int(config.get("maximumPlanPromptBytes", 64000))
    if len(prompt_for("PLAN", compact).encode("utf-8")) <= maximum:
        pages = [compact]
    else:
        pages = runner.deterministic_plan_subpages(packet, family, as_of)
    payloads = [
        audit_plan_page(
            request_root / f"page_{index + 1:03d}",
            page,
            images,
            reasoning_effort,
        )
        for index, page in enumerate(pages)
    ]
    approved = selected_decisions(payloads)
    unique = {
        str(item["scenarioSelectionId"]): item for item in approved
    }
    if len(unique) > 1:
        finalists = set(unique)
        reviewer_family = dict(family)
        reviewer_family["scenarioOptions"] = [
            item for item in family.get("scenarioOptions", [])
            if str(item["scenarioSelectionId"]) in finalists
        ]
        reviewer_packet = runner.compact_plan_page(
            packet, [reviewer_family], as_of
        )
        reviewer = audit_plan_page(
            request_root / "final_review",
            reviewer_packet,
            images,
            reasoning_effort,
        )
        approved = selected_decisions([reviewer])
        unique = {
            str(item["scenarioSelectionId"]): item for item in approved
        }
    if len(unique) == 1:
        decision = next(iter(unique.values()))
        return {
            "familyId": family_id,
            "verdict": "PLAN_APPROVED",
            "selectedScenarioSelectionId": str(
                decision["scenarioSelectionId"]
            ),
            "semanticAudit": decision["semanticAudit"],
            "reason": str(decision.get("reason", "")),
            "firstKnownAtUtc": str(packet["asOfUtc"]),
            "pageCount": len(pages),
        }
    reasons = [
        str(item.get("reason", ""))
        for payload in payloads
        for item in payload.get("decisions", [])
        if str(item.get("reason", "")).strip()
    ]
    return {
        "familyId": family_id,
        "verdict": "REJECT",
        "selectedScenarioSelectionId": None,
        "reason": " | ".join(reasons) or "NO_PROTOCOL_COMPLETE_PLAN",
        "firstKnownAtUtc": str(packet["asOfUtc"]),
        "pageCount": len(pages),
    }


def run_plan_audit(args: argparse.Namespace) -> int:
    ground_truth = Path(args.ground_truth).resolve()
    manifest = read_json(ground_truth / "manifest.json")
    if manifest.get("groundTruthComplete") is True:
        raise V4ContractError("Ground Truth is already frozen")
    queue_name = (
        "chronological_audit_queue.json"
        if args.audit_type == "CHRONOLOGICAL"
        else "counterfactual_audit_queue.json"
    )
    queue = read_json(ground_truth / queue_name)
    if int(args.limit) > 0:
        queue = queue[: int(args.limit)]
    families = {
        str(item["familyId"]): item
        for item in read_jsonl(ground_truth / "family_ledger.jsonl")
    }
    config = {
        **DEFAULTS,
        "symbol": "GOLD",
        "dataset": manifest["dataset"],
        "datasetPath": manifest["dataset"],
        "warmupStartUtc": manifest["period"]["warmupStartUtc"],
        "maximumPlanPromptBytes": int(args.maximum_prompt_bytes),
    }
    market = MarketData.from_npz(
        Path(manifest["dataset"]),
        parse_utc(manifest["period"]["warmupStartUtc"]),
        parse_utc(manifest["period"]["replayEndUtc"]),
        float(args.point),
    )
    work = ground_truth / "codex_audits" / args.audit_type.lower()
    runner = V4Runner(
        config=config,
        market=market,
        run_dir=work / "runner",
        provider=ScriptedProvider([]),
        runtime=new_runtime(parse_utc(manifest["period"]["replayStartUtc"])),
    )
    partial_path = work / "plan_decisions.jsonl"
    completed: dict[str, dict[str, Any]] = {}
    if partial_path.exists():
        completed = {
            str(item["familyId"]): item for item in read_jsonl(partial_path)
        }
    work.mkdir(parents=True, exist_ok=True)
    shared_image_root = ground_truth / "codex_audits" / "shared_images"
    packet_times = {
        parse_utc(str(read_json(
            ROOT / str(families[str(item["familyId"])]["firstKnownPacketPath"])
        )["asOfUtc"]))
        for item in queue
    }

    def ensure_images(as_of: int) -> None:
        image_dir = shared_image_root / str(as_of)
        image_dir.mkdir(parents=True, exist_ok=True)
        if not list(image_dir.glob("*.png")):
            render_images(config, "PLAN", as_of, image_dir)

    with ThreadPoolExecutor(max_workers=max(1, int(args.workers))) as pool:
        list(pool.map(ensure_images, sorted(packet_times)))

    jobs: list[tuple[int, dict[str, Any]]] = []
    for index, item in enumerate(queue, start=1):
        family_id = str(item["familyId"])
        if family_id in completed:
            continue
        jobs.append((index, item))

    def perform(job: tuple[int, dict[str, Any]]) -> tuple[str, dict[str, Any]]:
        index, item = job
        family_id = str(item["familyId"])
        family_record = families[family_id]
        packet = read_json(ROOT / str(family_record["firstKnownPacketPath"]))
        packet_family = next(
            family for family in packet["physicalLineageFamilies"]
            if str(family["familyId"]) == family_id
        )
        print(
            f"[GT {args.audit_type}] {index}/{len(queue)} family={family_id}",
            flush=True,
        )
        result = audit_family(
            packet=packet,
            family=packet_family,
            runner=runner,
            config=config,
            request_root=work / "requests" / f"{index:04d}_{family_id}",
            shared_image_root=shared_image_root,
            reasoning_effort=args.reasoning_effort,
        )
        return family_id, result

    if jobs:
        with ThreadPoolExecutor(max_workers=max(1, int(args.workers))) as pool:
            futures = {pool.submit(perform, job): job for job in jobs}
            for future in as_completed(futures):
                family_id, result = future.result()
                completed[family_id] = result
                ordered_results = [
                    completed[str(item["familyId"])]
                    for item in queue
                    if str(item["familyId"]) in completed
                ]
                partial_path.write_text(
                    "".join(
                        json.dumps(
                            item,
                            ensure_ascii=False,
                            separators=(",", ":"),
                        ) + "\n"
                        for item in ordered_results
                    ),
                    encoding="utf-8",
                    newline="\n",
                )
    print(
        f"GROUND_TRUTH_V2_CODEX_PLAN_AUDIT_OK type={args.audit_type} "
        f"families={len(completed)} output={partial_path}",
        flush=True,
    )
    return 0


def read_decision_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]


def family_execution_result(
    *,
    family_id: str,
    decision: dict[str, Any],
    family_record: dict[str, Any],
    market: MarketData,
    config: dict[str, Any],
    output: Path,
    replay_start: int,
    replay_end: int,
    follow_end: int,
) -> dict[str, Any]:
    packet = read_json(ROOT / str(family_record["firstKnownPacketPath"]))
    as_of = parse_utc(str(packet["asOfUtc"]))
    family = next(
        item for item in packet["physicalLineageFamilies"]
        if str(item["familyId"]) == family_id
    )
    semantic = decision.get("semanticAudit") or {}
    payload = {
        "schemaVersion": "5.0.0",
        "decisions": [{
            "familyId": family_id,
            "action": "PLAN",
            "scenarioSelectionId": decision["selectedScenarioSelectionId"],
            "semanticAudit": semantic,
            "reason": decision.get("reason", ""),
        }],
    }
    family_packet = {**packet, "physicalLineageFamilies": [family]}
    scenarios = freeze_plan_batch(payload, market, as_of, family_packet)
    if len(scenarios) != 1:
        raise V4ContractError(f"approved family did not freeze exactly once: {family_id}")
    scenario = scenarios[0]
    run_dir = output / "execution_runs" / family_id
    if run_dir.exists():
        shutil.rmtree(run_dir)
    runtime = new_runtime(market.m1_index_at_or_after(as_of))
    runtime["acceptedScenarioHashes"] = [str(scenario["scenarioHash"])]
    runtime["apiCallsByScenario"][str(scenario["scenarioHash"])] = 1
    runtime["externalMapAuthority"] = external_authority_from_scenario(
        scenario, runtime.get("externalMapAuthority")
    )
    runner = V4Runner(
        config=config,
        market=market,
        run_dir=run_dir,
        provider=CodexCliProvider(config),
        runtime=runtime,
    )
    runner.append_scenario_slot(scenario, as_of)
    first = market.m1_index_at_or_after(as_of)
    runner.runtime["cursor"] = first
    for index in range(first, len(market.rates)):
        row = market.m1_row(index)
        if int(row["time"]) >= follow_end:
            break
        runner.runtime["cursor"] = index
        runner.advance_position_book(row)
        if int(row["time"]) >= replay_end:
            if runner._loaded_slot_id is not None:
                runner.unload_scenario_slot()
            runner.runtime["scenarioSlots"] = []
            if not runner.runtime.get("openPositions"):
                break
            runner.runtime["cursor"] = index + 1
            runner.runtime["lastClosedM1BarId"] = row["barId"]
            continue
        if runner._loaded_slot_id is None and runner.runtime.get("scenarioSlots"):
            slot = sorted(
                list(runner.runtime["scenarioSlots"]),
                key=runner.lane_arbitration_key,
            )[0]
            runner.load_scenario_slot(str(slot["slotId"]))
        if runner._loaded_slot_id is not None:
            runner.process_bar(row)
            if runner.runtime.get("state") == "FLAT":
                runner.unload_scenario_slot()
        runner.runtime["cursor"] = index + 1
        runner.runtime["lastClosedM1BarId"] = row["barId"]
        if (
            int(row["available"]) >= replay_end
            and not runner.runtime.get("scenarioSlots")
            and not runner.runtime.get("openPositions")
        ):
            break
    runner.save()
    events = read_decision_events(run_dir / "decision_ledger.jsonl")
    order_events: dict[str, dict[str, Any]] = {}
    for event in events:
        if event.get("event") not in {
            "ORDER_CREATED",
            "DELIVERY_FVG_REPLACEMENT_ORDER_CREATED",
            "DELIVERY_FVG_ADDON_ORDER_CREATED",
        }:
            continue
        details = event.get("details") or {}
        order = details.get("order") or {}
        if order.get("orderId"):
            order_events[str(order["orderId"])] = event
    request_packets: dict[tuple[str, str], Path] = {}
    for request_meta_path in (run_dir / "requests").glob("*/request.json"):
        request_meta = read_json(request_meta_path)
        packet_path = request_meta_path.with_name("packet.json")
        if packet_path.exists():
            request_packets[
                (str(request_meta["phase"]), str(request_meta["asOfUtc"]))
            ] = packet_path
    executions: list[dict[str, Any]] = []
    for trade in runner.trades:
        order_id = str(trade["orderId"])
        event = order_events.get(order_id)
        if event is None:
            raise V4ContractError(f"closed trade lacks its order event: {order_id}")
        details = event.get("details") or {}
        evidence = details.get("triggerEvidence") or {}
        order = details["order"]
        execution = {
            "executionId": order_id,
            "familyId": family_id,
            "selectedScenarioSelectionId": decision["selectedScenarioSelectionId"],
            "decisionAtUtc": str(event["asOfUtc"]),
            "orderCreatedAtUtc": str(event["asOfUtc"]),
            "executionModel": str(order["model"]),
            "entry": float(order["entry"]),
            "stop": float(order["stop"]),
            "target": float(order["target"]),
            "filledAtUtc": str(trade["entryAtUtc"]),
            "closedAtUtc": str(trade["exitAtUtc"]),
            "outcome": str(trade["outcome"]),
            "resultR": float(trade["resultR"]),
            "evidenceFrozenBeforeOrder": True,
        }
        if order["model"] == "HTF_OB_REACTION":
            execution.update({
                "sweepBarId": str(evidence["sweepBarId"]),
                "chochBreakBarId": str(evidence["chochBreakBarId"]),
                "executionObBarId": str(evidence["executionBarId"]),
            })
            evidence_phase = "TRIGGER_WATCH"
        else:
            candidate = details.get("candidate") or {}
            execution.update({
                "deliveryFvgBarId": str(
                    order.get("deliveryFvgBarId") or candidate.get("fvgBarId")
                ),
                "deliveryCausalObBarId": str(
                    candidate.get("causalObBarId") or order.get("executionObBarId")
                ),
                "deliveryProtectedSwingBarId": str(
                    candidate.get("protectedSwingBarId")
                ),
            })
            evidence_phase = "DELIVERY_REVIEW"
        packet_path = request_packets.get((evidence_phase, str(event["asOfUtc"])))
        if packet_path is None:
            raise V4ContractError(
                f"order lacks its frozen semantic packet: {order_id} phase={evidence_phase}"
            )
        execution["evidencePacketPath"] = str(packet_path.relative_to(ROOT))
        execution["evidencePacketSha256"] = sha256_file(packet_path)
        executions.append(execution)
    cancellation_reasons = [
        str((event.get("details") or {}).get("reason", ""))
        for event in events
        if event.get("event") in {"SCENARIO_CANCELED", "ORDER_CANCELED"}
    ]
    return {
        "familyId": family_id,
        "selectedScenarioSelectionId": decision["selectedScenarioSelectionId"],
        "firstKnownAtUtc": str(packet["asOfUtc"]),
        "executions": executions,
        "terminalReason": cancellation_reasons[-1] if cancellation_reasons else (
            "NO_FILLED_EXECUTION" if not executions else "EXECUTIONS_CLOSED"
        ),
        "runPath": str(run_dir.relative_to(ROOT)),
    }


def run_execution_audit(args: argparse.Namespace) -> int:
    ground_truth = Path(args.ground_truth).resolve()
    manifest = read_json(ground_truth / "manifest.json")
    plan_path = Path(args.plan_decisions).resolve()
    plan_rows = read_jsonl(plan_path)
    families = {
        str(item["familyId"]): item
        for item in read_jsonl(ground_truth / "family_ledger.jsonl")
    }
    config = {
        **DEFAULTS,
        "symbol": "GOLD",
        "dataset": manifest["dataset"],
        "datasetPath": manifest["dataset"],
        "warmupStartUtc": manifest["period"]["warmupStartUtc"],
        "codexModel": "gpt-5.6-sol",
        "codexReasoningEffort": args.reasoning_effort,
        "maximumApiCallsPerRun": 1000,
        "maximumTokensPerRun": 20_000_000,
        "enableSemanticDeliveryReview": True,
        "enableDeliveryAddons": False,
        "applyLiveLatencyClock": False,
        "brokerOrderLatencyMs": 0,
        "brokerStopsLevelPrice": float(args.broker_stops_level),
    }
    follow_end = parse_utc(args.follow_end)
    market = MarketData.from_npz(
        Path(manifest["dataset"]),
        parse_utc(manifest["period"]["warmupStartUtc"]),
        follow_end,
        float(args.point),
    )
    output = ground_truth / "codex_audits" / "execution"
    output.mkdir(parents=True, exist_ok=True)
    result_path = output / "execution_candidates.jsonl"
    completed = {
        str(item["familyId"]): item
        for item in read_jsonl(result_path)
    } if result_path.exists() else {}
    approved = [item for item in plan_rows if item.get("verdict") == "PLAN_APPROVED"]
    if args.counterfactual_plan_decisions:
        counter_rows = {
            str(item["familyId"]): item
            for item in read_jsonl(Path(args.counterfactual_plan_decisions).resolve())
        }
        approved = [
            item for item in approved
            if str(item["familyId"]) in counter_rows
            and counter_rows[str(item["familyId"])].get("verdict") == "PLAN_APPROVED"
            and counter_rows[str(item["familyId"])].get("selectedScenarioSelectionId")
            == item.get("selectedScenarioSelectionId")
        ]
    if int(args.limit) > 0:
        approved = approved[: int(args.limit)]
    for index, decision in enumerate(approved, start=1):
        family_id = str(decision["familyId"])
        if family_id in completed:
            continue
        print(f"[GT EXECUTION] {index}/{len(approved)} family={family_id}", flush=True)
        completed[family_id] = family_execution_result(
            family_id=family_id,
            decision=decision,
            family_record=families[family_id],
            market=market,
            config=deepcopy(config),
            output=output,
            replay_start=parse_utc(manifest["period"]["replayStartUtc"]),
            replay_end=parse_utc(manifest["period"]["replayEndUtc"]),
            follow_end=follow_end,
        )
        result_path.write_text(
            "".join(
                json.dumps(completed[str(item["familyId"])], ensure_ascii=False,
                           separators=(",", ":")) + "\n"
                for item in approved if str(item["familyId"]) in completed
            ),
            encoding="utf-8",
            newline="\n",
        )
    print(
        f"GROUND_TRUTH_V2_EXECUTION_AUDIT_OK families={len(completed)} "
        f"output={result_path}",
        flush=True,
    )
    return 0


def audit_no_trade_day(
    *,
    item: dict[str, Any],
    config: dict[str, Any],
    output: Path,
    reasoning_effort: str,
) -> dict[str, Any]:
    day = str(item["dayUtc"])
    day_start = parse_utc(day + "T00:00:00Z")
    checkpoints = [day_start + hours * 3600 for hours in (6, 12, 18, 24)]
    images: list[Path] = []
    evidence_images: list[dict[str, str]] = []
    for as_of in checkpoints:
        image_dir = output / "images" / day / utc_text(as_of).replace(":", "-")
        rendered = render_images(config, "PLAN", as_of, image_dir)
        images.extend(rendered)
        evidence_images.extend({
            "asOfUtc": utc_text(as_of),
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256_file(path),
        } for path in rendered)
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["conclusion", "reason"],
        "properties": {
            "conclusion": {
                "type": "string",
                "enum": [
                    "NO_MISSED_PROTOCOL_COMPLETE_FAMILY",
                    "POTENTIAL_MISSED_FAMILY",
                ],
            },
            "reason": {"type": "string", "minLength": 1},
        },
    }
    prompt = (
        "Review this UTC trading day only from the attached H1/M30/M15/M5 charts. "
        "Apply the frozen Mentor protocol: objective, causal root OB, causal child OB, "
        "child touch and later M1 trigger must all be knowable in order. Decide whether "
        "the engine family ledger could have missed a visibly protocol-complete map family. "
        "This is an independent no-trade audit, not a request to invent a trade.\n\n"
        + json.dumps(item, ensure_ascii=False, separators=(",", ":"))
    )
    response = generate_codex_decision(
        request_dir=output / "requests" / day,
        prompt=prompt,
        images=images,
        schema=schema,
        model="gpt-5.6-sol",
        reasoning_effort=reasoning_effort,
        timeout_seconds=1800,
    ).payload
    return {
        "dayUtc": day,
        "reviewedH1BarIds": list(item["requiredH1BarIds"]),
        "reviewedM30BarIds": list(item["requiredM30BarIds"]),
        "reviewedM5TransferIntervals": [
            {"barId": value} for value in item["requiredM5TransferBarIds"]
        ],
        "evidenceImages": evidence_images,
        "conclusion": str(response["conclusion"]),
        "reason": str(response["reason"]),
    }


def run_no_trade_audit(args: argparse.Namespace) -> int:
    ground_truth = Path(args.ground_truth).resolve()
    manifest = read_json(ground_truth / "manifest.json")
    queue = read_json(ground_truth / "no_trade_audit_queue.json")
    config = {
        **DEFAULTS,
        "symbol": "GOLD",
        "dataset": manifest["dataset"],
        "datasetPath": manifest["dataset"],
        "warmupStartUtc": manifest["period"]["warmupStartUtc"],
    }
    output = ground_truth / "codex_audits" / "no_trade"
    output.mkdir(parents=True, exist_ok=True)
    path = output / "daily_decisions.jsonl"
    completed = {
        str(item["dayUtc"]): item for item in read_jsonl(path)
    } if path.exists() else {}
    jobs = [item for item in queue if str(item["dayUtc"]) not in completed]
    with ThreadPoolExecutor(max_workers=max(1, int(args.workers))) as pool:
        futures = {
            pool.submit(
                audit_no_trade_day,
                item=item,
                config=config,
                output=output,
                reasoning_effort=args.reasoning_effort,
            ): item
            for item in jobs
        }
        for future in as_completed(futures):
            result = future.result()
            completed[str(result["dayUtc"])] = result
            path.write_text(
                "".join(
                    json.dumps(completed[str(item["dayUtc"])], ensure_ascii=False,
                               separators=(",", ":")) + "\n"
                    for item in queue if str(item["dayUtc"]) in completed
                ),
                encoding="utf-8",
                newline="\n",
            )
    print(f"GROUND_TRUTH_V2_NO_TRADE_AUDIT_OK days={len(completed)} output={path}")
    return 0


def run_assemble_audits(args: argparse.Namespace) -> int:
    ground_truth = Path(args.ground_truth).resolve()
    manifest = read_json(ground_truth / "manifest.json")
    replay_start = parse_utc(manifest["period"]["replayStartUtc"])
    replay_end = parse_utc(manifest["period"]["replayEndUtc"])
    chronological_queue = read_json(ground_truth / "chronological_audit_queue.json")
    counter_queue = read_json(ground_truth / "counterfactual_audit_queue.json")
    chrono_plan = {
        str(item["familyId"]): item
        for item in read_jsonl(Path(args.chronological_plan).resolve())
    }
    counter_plan = {
        str(item["familyId"]): item
        for item in read_jsonl(Path(args.counterfactual_plan).resolve())
    }
    execution_rows = {
        str(item["familyId"]): item
        for item in read_jsonl(Path(args.execution_candidates).resolve())
    }
    families = {
        str(item["familyId"]): item
        for item in read_jsonl(ground_truth / "family_ledger.jsonl")
    }
    market = MarketData.from_npz(
        Path(manifest["dataset"]),
        parse_utc(manifest["period"]["warmupStartUtc"]),
        parse_utc("2026-08-13T00:00:00Z"),
        0.01,
    )
    chronological_plan_rows = [
        chrono_plan[str(item["familyId"])] for item in chronological_queue
    ]
    stateful_rows, stateful_valid, authority_timeline = (
        validate_stateful_plan_sequence(
            market=market,
            output=ground_truth,
            families=families,
            queue=chronological_queue,
            plan_decisions=chronological_plan_rows,
        )
    )
    candidates: list[dict[str, Any]] = []
    base_reasons: dict[str, str] = {}
    for family_id in families:
        first = chrono_plan[family_id]
        second = counter_plan[family_id]
        if first.get("verdict") != second.get("verdict"):
            base_reasons[family_id] = "PLAN_AUDIT_VERDICT_DISAGREEMENT"
            continue
        if first.get("verdict") != "PLAN_APPROVED":
            base_reasons[family_id] = str(first.get("reason") or "PLAN_REJECTED")
            continue
        if first.get("selectedScenarioSelectionId") != second.get("selectedScenarioSelectionId"):
            base_reasons[family_id] = "PLAN_AUDIT_SELECTION_DISAGREEMENT"
            continue
        stateful = stateful_valid.get(family_id)
        if stateful is None:
            stateful_row = next(
                item for item in stateful_rows
                if str(item["familyId"]) == family_id
            )
            base_reasons[family_id] = (
                "STATEFUL_PLAN_REJECTED:"
                + str(stateful_row.get("reason") or "OWNER_TIMELINE_CONFLICT")
            )
            continue
        execution = execution_rows.get(family_id)
        if execution is None:
            base_reasons[family_id] = "EXECUTION_AUDIT_MISSING"
            continue
        live = [
            item for item in execution.get("executions", [])
            if replay_start <= parse_utc(str(item["orderCreatedAtUtc"])) < replay_end
            and replay_start <= parse_utc(str(item["filledAtUtc"])) < replay_end
        ]
        if not live:
            base_reasons[family_id] = str(execution.get("terminalReason") or "NO_JUNE_FILL")
            continue
        selected_id = str(first["selectedScenarioSelectionId"])
        selected = next(
            item for item in families[family_id]["scenarioOptions"]
            if str(item["scenarioSelectionId"]) == selected_id
        )
        lineage_path_id = str(selected["lineagePathSelectionId"])
        lineage_path = next(
            item for item in families[family_id]["lineagePathOptions"]
            if str(item["pathSelectionId"]) == lineage_path_id
        )
        for item in live:
            item = dict(item)
            try:
                validate_scenario_authority_at_order(
                    stateful["scenario"],
                    authority_at(
                        market,
                        authority_timeline,
                        parse_utc(str(item["orderCreatedAtUtc"])),
                    ),
                )
            except V4ContractError as exc:
                base_reasons[family_id] = (
                    "ORDER_AUTHORITY_REJECTED:" + str(exc)
                )
                continue
            item["direction"] = str(families[family_id]["direction"])
            item["rootTf"] = str(lineage_path["root"]["obBarId"]).split(":", 1)[0]
            item["sourceRecognizedAtUtc"] = str(first["firstKnownAtUtc"])
            candidates.append(item)
    root_rank = {"H1": 0, "M30": 1, "M15": 2}
    candidates.sort(key=lambda item: (
        parse_utc(str(item["orderCreatedAtUtc"])),
        root_rank.get(str(item["rootTf"]), 9),
        parse_utc(str(item["sourceRecognizedAtUtc"])),
        str(item["executionId"]),
    ))
    accepted_by_family: dict[str, list[dict[str, Any]]] = {}
    active: list[dict[str, Any]] = []
    capacity_reasons: dict[str, list[str]] = {}
    for execution in candidates:
        created = parse_utc(str(execution["orderCreatedAtUtc"]))
        active = [
            item for item in active
            if parse_utc(str(item["closedAtUtc"])) > created
        ]
        family_id = str(execution["familyId"])
        if any(str(item["direction"]) != str(execution["direction"]) for item in active):
            capacity_reasons.setdefault(family_id, []).append("OPPOSITE_RISK_ACTIVE")
            continue
        if len(active) >= 3:
            capacity_reasons.setdefault(family_id, []).append("MAXIMUM_3RISK_SLOTS")
            continue
        accepted_by_family.setdefault(family_id, []).append(execution)
        active.append(execution)

    def final_row(family_id: str, auditor: str, session: str) -> dict[str, Any]:
        plan = chrono_plan[family_id]
        executions = accepted_by_family.get(family_id, [])
        if executions:
            return {
                "auditType": "",
                "auditorId": auditor,
                "auditSessionId": session,
                "familyId": family_id,
                "verdict": "ACCEPT",
                "selectedScenarioSelectionId": plan["selectedScenarioSelectionId"],
                "executions": executions,
                "reason": "INDEPENDENT_PLAN_AND_EXECUTION_AUDITS_PASSED",
            }
        reason = base_reasons.get(family_id)
        if reason is None and capacity_reasons.get(family_id):
            reason = "|".join(capacity_reasons[family_id])
        return {
            "auditType": "",
            "auditorId": auditor,
            "auditSessionId": session,
            "familyId": family_id,
            "verdict": "REJECT",
            "selectedScenarioSelectionId": None,
            "executions": [],
            "reason": reason or "NO_ACCEPTED_EXECUTION",
        }

    audit_dir = ground_truth / "audits"
    audit_dir.mkdir(parents=True, exist_ok=True)
    chrono_path = audit_dir / "chronological.jsonl"
    counter_path = audit_dir / "counterfactual.jsonl"
    trigger_path = audit_dir / "trigger_role.jsonl"
    no_trade_path = audit_dir / "no_trade.jsonl"
    stateful_path = audit_dir / "stateful_plan.jsonl"
    chrono_writer = HashChainWriter(chrono_path)
    chrono_writer.append_many([
        {**final_row(str(item["familyId"]), "codex-sol-chrono", "gtv2-chrono-v451"),
         "auditType": "CHRONOLOGICAL"}
        for item in chronological_queue
    ])
    counter_writer = HashChainWriter(counter_path)
    counter_writer.append_many([
        {**final_row(str(item["familyId"]), "codex-sol-counter", "gtv2-counter-v451"),
         "auditType": "COUNTERFACTUAL_SHUFFLED"}
        for item in counter_queue
    ])
    trigger_writer = HashChainWriter(trigger_path)
    trigger_writer.append_many([
        {
            "auditType": "TRIGGER_PACKET_ROLE_EVIDENCE",
            "auditorId": "engine-role-auditor",
            "auditSessionId": "gtv2-trigger-v451",
            "executionId": str(execution["executionId"]),
            "familyId": str(execution["familyId"]),
            "triggerPacketPath": str(execution["evidencePacketPath"]),
            "triggerPacketSha256": str(execution["evidencePacketSha256"]),
        }
        for execution in sorted(
            (item for values in accepted_by_family.values() for item in values),
            key=lambda item: parse_utc(str(item["decisionAtUtc"])),
        )
    ])
    no_trade_rows = read_jsonl(Path(args.no_trade_decisions).resolve())
    no_trade_writer = HashChainWriter(no_trade_path)
    no_trade_writer.append_many([
        {
            **item,
            "auditType": "NO_TRADE_DAILY_MTF",
            "auditorId": "codex-sol-no-trade",
            "auditSessionId": "gtv2-no-trade-v451",
        }
        for item in no_trade_rows
    ])
    stateful_writer = HashChainWriter(stateful_path)
    stateful_writer.append_many(stateful_rows)
    required = list(manifest.get("requiredAudits") or [])
    if "STATEFUL_PLAN_SEQUENCE" not in required:
        required.append("STATEFUL_PLAN_SEQUENCE")
    manifest["requiredAudits"] = required
    (ground_truth / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"GROUND_TRUTH_V2_AUDITS_ASSEMBLED executions="
        f"{sum(len(value) for value in accepted_by_family.values())} "
        f"statefulPlans={len(stateful_valid)} dir={audit_dir}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--ground-truth", required=True)
    plan.add_argument(
        "--audit-type",
        choices=("CHRONOLOGICAL", "COUNTERFACTUAL_SHUFFLED"),
        required=True,
    )
    plan.add_argument(
        "--reasoning-effort",
        choices=("low", "medium", "high", "xhigh"),
        default="high",
    )
    plan.add_argument("--maximum-prompt-bytes", type=int, default=64000)
    plan.add_argument("--point", type=float, default=0.01)
    plan.add_argument("--limit", type=int, default=0)
    plan.add_argument("--workers", type=int, default=4)
    plan.set_defaults(func=run_plan_audit)
    execute = sub.add_parser("execute")
    execute.add_argument("--ground-truth", required=True)
    execute.add_argument("--plan-decisions", required=True)
    execute.add_argument("--counterfactual-plan-decisions")
    execute.add_argument(
        "--reasoning-effort",
        choices=("low", "medium", "high", "xhigh"),
        default="medium",
    )
    execute.add_argument("--point", type=float, default=0.01)
    execute.add_argument("--broker-stops-level", type=float, default=0.0)
    execute.add_argument("--follow-end", default="2026-08-13T00:00:00Z")
    execute.add_argument("--limit", type=int, default=0)
    execute.set_defaults(func=run_execution_audit)
    no_trade = sub.add_parser("no-trade")
    no_trade.add_argument("--ground-truth", required=True)
    no_trade.add_argument(
        "--reasoning-effort", choices=("low", "medium", "high", "xhigh"),
        default="medium",
    )
    no_trade.add_argument("--workers", type=int, default=4)
    no_trade.set_defaults(func=run_no_trade_audit)
    repeat = sub.add_parser("stateful-repeat")
    repeat.add_argument("--run-dir", required=True)
    repeat.add_argument("--output", required=True)
    repeat.add_argument(
        "--audit-type",
        choices=("CHRONOLOGICAL_REPEAT", "COUNTERFACTUAL_SHUFFLED"),
        required=True,
    )
    repeat.add_argument(
        "--reasoning-effort", choices=("low", "medium", "high", "xhigh"),
        default="medium",
    )
    repeat.add_argument("--auditor-id", required=True)
    repeat.add_argument("--audit-session-id", required=True)
    repeat.add_argument("--seed", type=int, default=451)
    repeat.add_argument("--workers", type=int, default=4)
    repeat.set_defaults(func=run_stateful_repeat_audit)
    assemble = sub.add_parser("assemble")
    assemble.add_argument("--ground-truth", required=True)
    assemble.add_argument("--chronological-plan", required=True)
    assemble.add_argument("--counterfactual-plan", required=True)
    assemble.add_argument("--execution-candidates", required=True)
    assemble.add_argument("--no-trade-decisions", required=True)
    assemble.set_defaults(func=run_assemble_audits)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return int(args.func(args))
    except (OSError, ValueError, V4ContractError) as exc:
        print(f"GROUND_TRUTH_V2_CODEX_AUDIT_FAILED: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
