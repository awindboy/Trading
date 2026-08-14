from __future__ import annotations

import argparse
from bisect import bisect_left
from concurrent.futures import ProcessPoolExecutor
import copy
import hashlib
import json
import os
from pathlib import Path
import random
import sys
from typing import Any, Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mentor_replay_v4_core import (
    PIPELINE_VERSION,
    MarketData,
    V4ContractError,
    _confirmed_liquidity_swings,
    build_plan_packet,
    canonical_hash,
    external_authority_from_scenario,
    freeze_plan_batch,
    mechanical_root_candidates,
    parse_utc,
    resolved_external_authority,
    split_bar_id,
    utc_text,
)


DEFAULT_DATASET = ROOT / "output" / "datasets" / "GOLD_M1_2023-12-01_2026-08-12.npz"
DEFAULT_OUTPUT = ROOT / "output" / "ground_truth_v2_june2026"
CONTRACTS_MANIFEST = ROOT / "mentor_context_pack" / "api_contracts" / "v4_manifest.json"
BAR_PREFIXES = ("H1:", "M30:", "M15:", "M5:", "M1:")
_DISCOVERY_MARKET: MarketData | None = None


def init_discovery_worker(
    dataset: str,
    warmup_start: int,
    replay_end: int,
    point: float,
) -> None:
    global _DISCOVERY_MARKET
    _DISCOVERY_MARKET = MarketData.from_npz(
        Path(dataset), warmup_start, replay_end, point
    )


def build_discovery_packet_worker(
    job: tuple[int, str, tuple[str, ...], str],
) -> dict[str, Any]:
    if _DISCOVERY_MARKET is None:
        raise RuntimeError("discovery worker market is not initialized")
    as_of, event_reason, focus_root_ids, symbol = job
    return build_plan_packet(
        _DISCOVERY_MARKET,
        as_of,
        symbol,
        focus_root_bar_ids=set(focus_root_ids),
        candidate_context=[{
            "rootBarIds": list(focus_root_ids),
            "discoveryEvent": event_reason,
            "eventAtUtc": utc_text(as_of),
            "replayRelevantAtUtc": utc_text(as_of),
        }],
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]


def verify_hash_chain(path: Path, expected_audit_type: str) -> list[dict[str, Any]]:
    rows = read_jsonl(path)
    previous = "GENESIS"
    for index, row in enumerate(rows):
        if row.get("auditType") != expected_audit_type:
            raise V4ContractError(
                f"{path.name} audit type mismatch at row {index}"
            )
        if row.get("previousHash") != previous:
            raise V4ContractError(f"{path.name} hash chain is broken at row {index}")
        body = dict(row)
        recorded = str(body.pop("recordHash", ""))
        if canonical_hash(body) != recorded:
            raise V4ContractError(f"{path.name} record hash is invalid at row {index}")
        previous = recorded
    return rows


def validate_no_trade_audit_conclusion(row: dict[str, Any]) -> None:
    conclusion = str(row.get("conclusion", "")).strip()
    if not conclusion:
        raise V4ContractError("daily no-trade audit conclusion is missing")
    if conclusion != "NO_MISSED_PROTOCOL_COMPLETE_FAMILY":
        raise V4ContractError(
            "daily no-trade audit found a potentially missed protocol-complete family: "
            + str(row.get("dayUtc", "UNKNOWN_DAY"))
        )


class HashChainWriter:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.previous = "GENESIS"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")

    def append(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.append_many([body])[0]

    def append_many(
        self, bodies: Iterable[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for body in bodies:
            record = {**body, "previousHash": self.previous}
            record["recordHash"] = canonical_hash(record)
            self.previous = str(record["recordHash"])
            records.append(record)
        if not records:
            return records
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            for record in records:
                handle.write(
                    json.dumps(
                        record,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ) + "\n"
                )
        return records

def nested_bar_ids(value: Any) -> set[str]:
    output: set[str] = set()
    if isinstance(value, str) and value.startswith(BAR_PREFIXES):
        output.add(value)
    elif isinstance(value, dict):
        for item in value.values():
            output.update(nested_bar_ids(item))
    elif isinstance(value, list):
        for item in value:
            output.update(nested_bar_ids(item))
    return output


def packet_bar_ids(packet: dict[str, Any]) -> set[str]:
    return {
        str(row[0])
        for rows in (packet.get("bars") or {}).get("data", {}).values()
        for row in rows
        if row
    }


def with_lossless_role_evidence(
    packet: dict[str, Any], market: MarketData, as_of: int
) -> dict[str, Any]:
    """Attach every PLAN role candle and a small as-of context window."""
    required = {
        role_id
        for family in packet.get("physicalLineageFamilies", [])
        for role_id in nested_bar_ids(family)
        if split_bar_id(role_id)[0] in {"H1", "M30", "M15", "M5"}
    }
    rows_by_tf: dict[str, dict[str, dict[str, Any]]] = {
        timeframe: {} for timeframe in ("H1", "M30", "M15", "M5")
    }
    for role_id in sorted(required):
        role = market.bar(role_id, as_of)
        timeframe = str(role["tf"])
        series = market.frames[timeframe]
        left = max(0, int(role["index"]) - 3)
        right = min(len(series.time), int(role["index"]) + 5)
        for index in range(left, right):
            if int(series.available_time[index]) > int(as_of):
                continue
            candidate_id = f"{timeframe}:{int(series.time[index])}"
            rows_by_tf[timeframe][candidate_id] = market.bar(
                candidate_id, as_of
            )
    bars = {
        "columns": ["barId", "open", "high", "low", "close"],
        "data": {
            timeframe: [
                [
                    row["barId"],
                    round(float(row["open"]), 5),
                    round(float(row["high"]), 5),
                    round(float(row["low"]), 5),
                    round(float(row["close"]), 5),
                ]
                for row in sorted(values.values(), key=lambda item: item["time"])
            ]
            for timeframe, values in rows_by_tf.items()
        },
    }
    supplied = {
        str(row[0]) for rows in bars["data"].values() for row in rows
    }
    missing = sorted(required - supplied)
    if missing:
        raise V4ContractError(
            "lossless Ground Truth packet omitted role IDs: "
            + ",".join(missing[:12])
        )
    return {
        **packet,
        "bars": bars,
        "roleEvidenceAudit": {
            "requiredRoleIds": sorted(required),
            "suppliedRoleIdsHash": canonical_hash(sorted(supplied)),
            "missingRoleIds": [],
        },
    }


def event_times(
    market: MarketData, warmup_start: int, replay_end: int
) -> list[int]:
    roots = mechanical_root_candidates(market, replay_end, maximum=None)
    liquidity = _confirmed_liquidity_swings(market, replay_end)
    values = {
        market.bar(str(item["displacementBarId"]), replay_end)["available"]
        for item in roots
    }
    values.update(parse_utc(str(item["matureAtUtc"])) for item in liquidity)
    return sorted(
        value for value in values
        if warmup_start <= int(value) < replay_end
    )


class M1FirstTouchIndex:
    def __init__(self, rates: np.ndarray) -> None:
        self.rates = rates
        size = 1
        while size < len(rates):
            size <<= 1
        self.size = size
        self.low_tree = np.full(size * 2, np.inf, dtype=np.float64)
        self.high_tree = np.full(size * 2, -np.inf, dtype=np.float64)
        self.low_tree[size:size + len(rates)] = rates["low"]
        self.high_tree[size:size + len(rates)] = rates["high"]
        level = size
        while level > 1:
            parent = level // 2
            self.low_tree[parent:level] = np.minimum(
                self.low_tree[level:level * 2:2],
                self.low_tree[level + 1:level * 2:2],
            )
            self.high_tree[parent:level] = np.maximum(
                self.high_tree[level:level * 2:2],
                self.high_tree[level + 1:level * 2:2],
            )
            level = parent

    def _first(
        self,
        left: int,
        right: int,
        threshold: float,
        *,
        low_search: bool,
    ) -> int | None:
        tree = self.low_tree if low_search else self.high_tree

        def visit(node: int, node_left: int, node_right: int) -> int | None:
            if node_right <= left or right <= node_left:
                return None
            impossible = (
                tree[node] > threshold
                if low_search else tree[node] < threshold
            )
            if impossible:
                return None
            if node_right - node_left == 1:
                return node_left if node_left < len(self.rates) else None
            middle = (node_left + node_right) // 2
            first = visit(node * 2, node_left, middle)
            return first if first is not None else visit(
                node * 2 + 1, middle, node_right
            )

        return visit(1, 0, self.size)

    def low_at_or_below(
        self, left: int, right: int, threshold: float
    ) -> int | None:
        return self._first(left, right, threshold, low_search=True)

    def high_at_or_above(
        self, left: int, right: int, threshold: float
    ) -> int | None:
        return self._first(left, right, threshold, low_search=False)


def first_root_proximal_touch_at(
    market: MarketData,
    candidate: dict[str, Any],
    replay_end: int,
    touch_index: M1FirstTouchIndex | None = None,
) -> int | None:
    root = market.bar(str(candidate["rootBarId"]), replay_end)
    displacement = market.bar(str(candidate["displacementBarId"]), replay_end)
    rows = market.rates
    left = int(np.searchsorted(
        rows["time"], int(displacement["available"]), side="left"
    ))
    right = int(np.searchsorted(
        rows["time"], int(replay_end), side="left"
    ))
    if right <= left:
        return None
    index = touch_index or M1FirstTouchIndex(rows)
    if str(candidate["direction"]) == "LONG":
        hit = index.low_at_or_below(left, right, float(root["high"]))
    else:
        hit = index.high_at_or_above(left, right, float(root["low"]))
    if hit is None:
        return None
    return int(rows["time"][hit]) + 60


def family_local_packet(
    packet: dict[str, Any],
    family: dict[str, Any],
    market: MarketData,
    as_of: int,
) -> dict[str, Any]:
    local = copy.deepcopy(packet)
    local["physicalLineageFamilies"] = [copy.deepcopy(family)]
    required = nested_bar_ids(family)
    local["swingCandidates"] = [
        item for item in local.get("swingCandidates", [])
        if str(item.get("barId")) in required
    ]
    local["familyLocalEvidence"] = True
    local["familyLocalId"] = str(family["familyId"])
    return with_lossless_role_evidence(local, market, as_of)


def compact_root_event(item: dict[str, Any]) -> dict[str, Any]:
    return {
        key: item.get(key)
        for key in (
            "direction", "timeframe", "rootBarId", "rootTimeUtc",
            "displacementBarId", "displacementTimeUtc",
            "displacementEpisodeStartBarId", "displacementEpisodeEndBarId",
        )
    }


def compact_liquidity_event(item: dict[str, Any]) -> dict[str, Any]:
    return {
        key: item.get(key)
        for key in (
            "barId", "timeframe", "side", "kind", "price", "matureAtUtc",
            "consumedAtUtc", "invalidatedAtUtc",
        )
    }


def stable_plan_option_key(option: dict[str, Any]) -> str:
    """Match the runtime's semantic option identity.

    Intermediate-liquidity lists may change while the actual owner, objective,
    and lineage stay the same. Those changes must not manufacture a new PLAN
    event. A newly mature objective or lineage, however, is a new knowable
    scenario and needs its own Ground Truth snapshot.
    """
    return canonical_hash({
        "direction": option.get("direction"),
        "scope": option.get("scope"),
        "objectiveBarId": (option.get("objective") or {}).get("barId"),
        "objectiveSide": (option.get("objective") or {}).get("side"),
        "lineagePathSelectionId": option.get("lineagePathSelectionId"),
        "ownerBreakTargetBarId": option.get("ownerBreakTargetBarId"),
        "ownerBreakBarId": option.get("ownerBreakBarId"),
    })


def snapshot_family(
    family: dict[str, Any],
) -> tuple[str, str, dict[str, Any]]:
    """Give every distinct knowable family state a stable audit identity."""
    physical_id = str(family["familyId"])
    option_keys = sorted({
        stable_plan_option_key(item)
        for item in family.get("scenarioOptions", [])
    })
    snapshot_id = canonical_hash({
        "physicalFamilyId": physical_id,
        "semanticOptionKeys": option_keys,
    })[:12]
    frozen = copy.deepcopy(family)
    frozen["physicalFamilyId"] = physical_id
    frozen["familySnapshotId"] = snapshot_id
    frozen["familyId"] = snapshot_id
    return snapshot_id, physical_id, frozen


def map_roots_with_possible_child(
    market: MarketData,
    map_roots: list[dict[str, Any]],
    roots: list[dict[str, Any]],
    as_of: int,
) -> list[dict[str, Any]]:
    """Apply only necessary physical-lineage conditions before packet builds.

    This is not a quality filter. A family cannot exist unless a same-direction
    lower-timeframe root formed inside the parent's displacement episode and
    overlaps the parent price event. Removing roots that fail this necessary
    condition avoids thousands of provably empty packet constructions.
    """
    rank = {"H1": 0, "M30": 1, "M15": 2, "M5": 3}
    children_by_direction: dict[str, list[tuple[int, dict[str, Any]]]] = {
        "LONG": [], "SHORT": []
    }
    root_bars = {
        str(item["rootBarId"]): market.bar(str(item["rootBarId"]), as_of)
        for item in roots
    }
    for child in roots:
        child_bar = root_bars[str(child["rootBarId"])]
        children_by_direction[str(child["direction"])].append(
            (int(child_bar["time"]), child)
        )
    child_times: dict[str, list[int]] = {}
    for direction, items in children_by_direction.items():
        items.sort(key=lambda item: item[0])
        child_times[direction] = [item[0] for item in items]

    retained: list[dict[str, Any]] = []
    for parent in map_roots:
        direction = str(parent["direction"])
        parent_bar = root_bars[str(parent["rootBarId"])]
        episode_end = market.bar(
            str(parent["displacementEpisodeEndBarId"]), as_of
        )
        items = children_by_direction[direction]
        times = child_times[direction]
        left = bisect_left(times, int(parent_bar["time"]))
        right = bisect_left(times, int(episode_end["available"]))
        parent_rank = rank[str(parent_bar["tf"])]
        possible = False
        for _, child in items[left:right]:
            child_bar = root_bars[str(child["rootBarId"])]
            if rank[str(child_bar["tf"])] <= parent_rank:
                continue
            if (
                float(child_bar["high"]) >= float(parent_bar["low"])
                and float(child_bar["low"]) <= float(parent_bar["high"])
            ):
                possible = True
                break
        if possible:
            retained.append(parent)
    return retained


def discover(args: argparse.Namespace) -> int:
    dataset = Path(args.dataset).resolve()
    output = Path(args.output).resolve()
    if output.exists() and any(output.iterdir()):
        raise V4ContractError(
            f"Ground Truth V2 output is not empty: {output}"
        )
    output.mkdir(parents=True, exist_ok=True)
    packets_dir = output / "packets"
    packets_dir.mkdir(parents=True, exist_ok=True)
    warmup_start = parse_utc(args.warmup_start)
    replay_start = parse_utc(args.replay_start)
    replay_end = parse_utc(args.replay_end)
    market = MarketData.from_npz(
        dataset, warmup_start, replay_end, float(args.point)
    )
    roots: list[dict[str, Any]] = []
    for timeframe in ("H1", "M30", "M15", "M5"):
        roots.extend(
            mechanical_root_candidates(
                market,
                replay_end,
                maximum=None,
                timeframe_limits={timeframe: 1},
                active_only=False,
            )
        )
    map_roots = [
        item for item in roots
        if str(item["timeframe"]) in {"H1", "M30", "M15"}
    ]
    active_warmup_ids: set[str] = set()
    for timeframe in ("H1", "M30", "M15"):
        active_warmup_ids.update(
            str(item["rootBarId"])
            for item in mechanical_root_candidates(
                market,
                replay_start,
                maximum=None,
                timeframe_limits={timeframe: 1},
                active_only=True,
            )
        )
    map_roots = [
        item for item in map_roots
        if str(item["rootBarId"]) in active_warmup_ids
        or replay_start <= int(
            market.bar(str(item["displacementBarId"]), replay_end)["available"]
        ) < replay_end
    ]
    map_roots = map_roots_with_possible_child(
        market, map_roots, roots, replay_end
    )
    liquidity = _confirmed_liquidity_swings(market, replay_end)
    roots_by_time: dict[int, list[dict[str, Any]]] = {}
    for item in roots:
        known_at = int(
            market.bar(str(item["displacementBarId"]), replay_end)["available"]
        )
        roots_by_time.setdefault(known_at, []).append(item)
    liquidity_by_time: dict[int, list[dict[str, Any]]] = {}
    for item in liquidity:
        liquidity_by_time.setdefault(
            parse_utc(str(item["matureAtUtc"])), []
        ).append(item)

    event_ledger = HashChainWriter(output / "raw_event_ledger.jsonl")
    family_ledger = HashChainWriter(output / "family_ledger.jsonl")
    coverage_ledger = HashChainWriter(output / "packet_role_coverage.jsonl")
    first_known: dict[str, dict[str, Any]] = {}
    daily: dict[str, dict[str, Any]] = {
        utc_text(day)[:10]: {"families": 0, "engineMisses": 0}
        for day in range(replay_start, replay_end, 86400)
    }

    all_event_times = sorted({*roots_by_time.keys(), *liquidity_by_time.keys()})
    for as_of in (
        value for value in all_event_times
        if warmup_start <= int(value) < replay_end
    ):
        event_batch: list[dict[str, Any]] = []
        for root in roots_by_time.get(as_of, []):
            event_batch.append({
                "eventType": "ROOT_DISPLACEMENT_EPISODE",
                "knownAtUtc": utc_text(as_of),
                "payload": compact_root_event(root),
            })
        for item in liquidity_by_time.get(as_of, []):
            event_batch.append({
                "eventType": "LIQUIDITY_MATURED",
                "knownAtUtc": utc_text(as_of),
                "payload": compact_liquidity_event(item),
            })
        event_ledger.append_many(event_batch)
    print(
        "GROUND_TRUTH_V2_EVENTS_WRITTEN "
        f"roots={len(roots)} liquidity={len(liquidity)}",
        flush=True,
    )

    schedule: dict[int, dict[str, Any]] = {}
    touch_index = M1FirstTouchIndex(market.rates)
    for item in map_roots:
        known_at = int(
            market.bar(str(item["displacementBarId"]), replay_end)["available"]
        )
        root_bar_id = str(item["rootBarId"])
        touch_at = first_root_proximal_touch_at(
            market, item, replay_end, touch_index
        )
        if replay_start <= known_at < replay_end:
            event = schedule.setdefault(known_at, {
                "newRootIds": set(), "objectiveMatured": False,
                "touchRootIds": set(),
            })
            event["newRootIds"].add(root_bar_id)
        elif (
            touch_at is not None
            and replay_start - 86400 <= touch_at < replay_start
        ):
            event = schedule.setdefault(replay_start, {
                "newRootIds": set(), "objectiveMatured": False,
                "touchRootIds": set(),
            })
            event["touchRootIds"].add(root_bar_id)
        if touch_at is not None and replay_start <= touch_at < replay_end:
            event = schedule.setdefault(touch_at, {
                "newRootIds": set(), "objectiveMatured": False,
                "touchRootIds": set(),
            })
            event["touchRootIds"].add(root_bar_id)

    # A physical family is not semantically complete forever at its first
    # sighting. A child or objective can become knowable later while the root
    # is still fresh. Runtime V4.51 re-evaluates pending roots when destination
    # evidence matures; Ground Truth must follow the same event clock.
    for item in liquidity:
        if str(item.get("timeframe")) not in {"H1", "M30", "M15"}:
            continue
        mature_at = parse_utc(str(item["matureAtUtc"]))
        if replay_start <= mature_at < replay_end:
            event = schedule.setdefault(mature_at, {
                "newRootIds": set(), "objectiveMatured": False,
                "touchRootIds": set(),
            })
            event["objectiveMatured"] = True

    scheduled_root_count = sum(
        len(item["newRootIds"]) + len(item["touchRootIds"])
        for item in schedule.values()
    )
    print(
        "GROUND_TRUTH_V2_DISCOVERY_SCHEDULE "
        f"events={len(schedule)} rootEvents={scheduled_root_count}",
        flush=True,
    )
    pending_root_ids: set[str] = set()
    seen_snapshot_ids: set[str] = set()
    discovery_jobs: list[tuple[int, str, tuple[str, ...], str]] = []
    for as_of in sorted(schedule):
        event = schedule[as_of]
        new_root_ids = {str(item) for item in event["newRootIds"]}
        touch_root_ids = {str(item) for item in event["touchRootIds"]}
        pending_root_ids.update(new_root_ids)
        focus_root_ids = set(new_root_ids) | set(touch_root_ids)
        event_reason = "ROOT_FORMATION"
        if bool(event["objectiveMatured"]):
            if pending_root_ids:
                active = {
                    str(item["rootBarId"])
                    for item in mechanical_root_candidates(
                        market,
                        as_of,
                        maximum=None,
                        active_only=True,
                        focus_root_bar_ids=pending_root_ids,
                    )
                }
                pending_root_ids.intersection_update(active)
                focus_root_ids.update(pending_root_ids)
            event_reason = "NEW_CAUSAL_OPTION_MATURED"
        if touch_root_ids:
            event_reason = "ROOT_PROXIMAL_TOUCH"
        if not focus_root_ids:
            continue
        discovery_jobs.append(
            (as_of, event_reason, tuple(sorted(focus_root_ids)), str(args.symbol))
        )

    worker_count = max(1, min(6, int(os.cpu_count() or 1)))
    print(
        "GROUND_TRUTH_V2_DISCOVERY_JOBS "
        f"jobs={len(discovery_jobs)} workers={worker_count}",
        flush=True,
    )
    with ProcessPoolExecutor(
        max_workers=worker_count,
        initializer=init_discovery_worker,
        initargs=(str(dataset), warmup_start, replay_end, float(args.point)),
    ) as executor:
        packet_results = executor.map(
            build_discovery_packet_worker, discovery_jobs, chunksize=1
        )
        for processed_events, (job, packet) in enumerate(
            zip(discovery_jobs, packet_results), start=1
        ):
            as_of, event_reason, _, _ = job
            if processed_events == 1 or processed_events % 100 == 0:
                print(
                    "GROUND_TRUTH_V2_DISCOVERY_PROGRESS "
                    f"processedEvents={processed_events}/{len(discovery_jobs)} "
                    f"snapshots={len(first_known)}",
                    flush=True,
                )
            for raw_family in packet.get("physicalLineageFamilies", []):
                family_id, physical_family_id, family = snapshot_family(raw_family)
                if family_id in seen_snapshot_ids:
                    continue
                seen_snapshot_ids.add(family_id)
                local_packet = family_local_packet(packet, family, market, as_of)
                local_packet["physicalLineageFamilies"] = [copy.deepcopy(family)]
                local_packet["familyLocalId"] = family_id
                packet_path = packets_dir / f"{as_of}_{family_id}.json"
                packet_path.write_text(
                    json.dumps(
                        local_packet,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ) + "\n",
                    encoding="utf-8",
                    newline="\n",
                )
                supplied_ids = packet_bar_ids(local_packet)
                required_ids = {
                    role_id for role_id in nested_bar_ids(family)
                    if split_bar_id(role_id)[0] in {"H1", "M30", "M15", "M5"}
                }
                missing = sorted(required_ids - supplied_ids)
                coverage = coverage_ledger.append({
                    "familyId": family_id,
                    "physicalFamilyId": physical_family_id,
                    "firstKnownAtUtc": utc_text(as_of),
                    "replayRelevantAtUtc": utc_text(as_of),
                    "discoveryEvent": event_reason,
                    "requiredRoleIds": sorted(required_ids),
                    "missingRoleIds": missing,
                    "packetPath": packet_path.relative_to(ROOT).as_posix(),
                    "packetSha256": sha256_file(packet_path),
                })
                family_record = family_ledger.append({
                    "familyId": family_id,
                    "physicalFamilyId": physical_family_id,
                    "firstKnownAtUtc": utc_text(as_of),
                    "replayRelevantAtUtc": utc_text(as_of),
                    "discoveryEvent": event_reason,
                    "direction": family.get("direction"),
                    "rootBarId": family.get("rootBarId"),
                    "initialDisplacementBarId": family.get(
                        "initialDisplacementBarId"
                    ),
                    "scenarioOptions": family.get("scenarioOptions", []),
                    "lineagePathOptions": family.get("lineagePathOptions", []),
                    "firstKnownPacketPath": packet_path.relative_to(ROOT).as_posix(),
                    "firstKnownRequiredRoleIds": sorted(required_ids),
                    "packetRoleCoverageHash": coverage["recordHash"],
                    "status": (
                        "ENGINE_CANDIDATE_MISS"
                        if missing else "AWAITING_SEMANTIC_AUDIT"
                    ),
                })
                first_known[family_id] = family_record
                day = utc_text(as_of)[:10]
                day_row = daily.setdefault(
                    day, {"families": 0, "engineMisses": 0}
                )
                day_row["families"] += 1
                day_row["engineMisses"] += int(bool(missing))

    family_rows = list(first_known.values())
    queue = [
        {
            "familyId": item["familyId"],
            "firstKnownAtUtc": item["firstKnownAtUtc"],
            "status": item["status"],
        }
        for item in family_rows
    ]
    (output / "chronological_audit_queue.json").write_text(
        json.dumps(queue, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    shuffled = list(queue)
    random.Random(202606).shuffle(shuffled)
    (output / "counterfactual_audit_queue.json").write_text(
        json.dumps(shuffled, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    chronological_queue_hash = canonical_hash(queue)
    counterfactual_queue_hash = canonical_hash(shuffled)
    no_trade_queue = []
    for day in sorted(daily):
        day_start = parse_utc(day + "T00:00:00Z")
        day_end = day_start + 86400
        no_trade_queue.append({
            "dayUtc": day,
            "familyCount": int(daily[day]["families"]),
            "engineCandidateMissCount": int(daily[day]["engineMisses"]),
            "requiredH1BarIds": [
                row["barId"] for row in market.bars("H1", day_end, 32)
                if day_start < int(row["available"]) <= day_end
            ],
            "requiredM30BarIds": [
                row["barId"] for row in market.bars("M30", day_end, 64)
                if day_start < int(row["available"]) <= day_end
            ],
            "requiredM5TransferBarIds": [
                str(item["displacementBarId"])
                for item in roots
                if str(item["timeframe"]) == "M5"
                and day_start < int(
                    market.bar(str(item["displacementBarId"]), replay_end)["available"]
                ) <= day_end
            ],
        })
    (output / "no_trade_audit_queue.json").write_text(
        json.dumps(no_trade_queue, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    trigger_queue = [
        {
            "familyId": item["familyId"],
            "firstKnownAtUtc": item["firstKnownAtUtc"],
            "requiredFutureRoles": [
                "sweepBarId", "chochBreakBarId", "executionObBarId"
            ],
        }
        for item in queue
    ]
    (output / "trigger_role_audit_queue.json").write_text(
        json.dumps(trigger_queue, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    no_trade_lines = [
        "# Ground Truth V2 No-Trade Audit Queue",
        "",
        "No automated candidate is a trade. Each UTC day requires an H1/M30 map review,",
        "all M5 structure-transfer interval review, and an explicit no-trade conclusion.",
        "",
        "| UTC day | families | engine candidate misses | audit status |",
        "| --- | ---: | ---: | --- |",
    ]
    for day in sorted(daily):
        item = daily[day]
        no_trade_lines.append(
            f"| {day} | {item['families']} | {item['engineMisses']} | PENDING |"
        )
    (output / "NO_TRADE_AUDIT.md").write_text(
        "\n".join(no_trade_lines) + "\n", encoding="utf-8", newline="\n"
    )
    manifest = {
        "pipelineVersion": PIPELINE_VERSION,
        "mode": "RAW_M1_NO_ORACLE_GROUND_TRUTH_V2",
        "status": "BLOCKED_AWAITING_FOUR_INDEPENDENT_AUDITS",
        "groundTruthComplete": False,
        "dataset": str(dataset),
        "datasetSha256": sha256_file(dataset),
        "period": {
            "warmupStartUtc": args.warmup_start,
            "replayStartUtc": args.replay_start,
            "replayEndUtc": args.replay_end,
        },
        "familyCount": len(family_rows),
        "engineCandidateMissCount": sum(
            item["status"] == "ENGINE_CANDIDATE_MISS" for item in family_rows
        ),
        "requiredAudits": [
            "CHRONOLOGICAL",
            "COUNTERFACTUAL_SHUFFLED",
            "NO_TRADE_DAILY_MTF",
            "TRIGGER_PACKET_ROLE_EVIDENCE",
            "STATEFUL_PLAN_SEQUENCE",
        ],
        "auditQueueHashes": {
            "chronological": chronological_queue_hash,
            "counterfactual": counterfactual_queue_hash,
            "noTrade": canonical_hash(no_trade_queue),
            "triggerRole": canonical_hash(trigger_queue),
        },
        "forbiddenImports": ["oracle_move_index", "legacy trade candidates"],
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    blocked_report = [
        "# Ground Truth V2 - BLOCKED",
        "",
        "This directory contains candidate discovery evidence, not an approved ground truth.",
        "",
        f"- Pipeline: `{manifest['pipelineVersion']}`",
        f"- Candidate families: `{manifest['familyCount']}`",
        f"- Engine candidate misses: `{manifest['engineCandidateMissCount']}`",
        "- Ground truth complete: `false`",
        "",
        "Completion is blocked until every family has exactly one semantic decision and",
        "the chronological, shuffled-counterfactual, and daily no-trade MTF audits all pass.",
        "Do not use this directory as a profitability benchmark or Gemini parity target.",
    ]
    (output / "BLOCKED_REPORT.md").write_text(
        "\n".join(blocked_report) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        "GROUND_TRUTH_V2_DISCOVERY_BLOCKED "
        f"families={manifest['familyCount']} "
        f"engineMisses={manifest['engineCandidateMissCount']} output={output}"
    )
    return 2


def validate_selected_trade(
    market: MarketData,
    family: dict[str, Any],
    decision: dict[str, Any],
    execution: dict[str, Any],
) -> dict[str, Any]:
    required = {
        "executionId", "decisionAtUtc", "executionModel", "entry", "stop",
        "target", "orderCreatedAtUtc", "evidenceFrozenBeforeOrder",
        "evidencePacketPath", "evidencePacketSha256",
    }
    missing_fields = sorted(required - set(execution))
    if missing_fields:
        raise V4ContractError(
            "accepted execution is incomplete: " + ",".join(missing_fields)
        )
    if execution["evidenceFrozenBeforeOrder"] is not True:
        raise V4ContractError("accepted trade evidence was not frozen before order")
    options = {
        str(item["scenarioSelectionId"]): item
        for item in family.get("scenarioOptions", [])
    }
    selected_id = str(decision["selectedScenarioSelectionId"])
    if selected_id not in options:
        raise V4ContractError("selected scenario was not in the first-known packet")
    selected = options[selected_id]
    lineage_options = {
        str(item["pathSelectionId"]): item
        for item in family.get("lineagePathOptions", [])
    }
    lineage_id = str(selected.get("lineagePathSelectionId", ""))
    if lineage_id not in lineage_options:
        raise V4ContractError("selected lineage path was not in the first-known packet")
    selected_lineage = lineage_options[lineage_id]
    as_of = parse_utc(str(execution["decisionAtUtc"]))
    order_at = parse_utc(str(execution["orderCreatedAtUtc"]))
    if order_at < as_of:
        raise V4ContractError("order precedes its frozen semantic decision")
    model = str(execution["executionModel"])
    if model == "HTF_OB_REACTION":
        model_fields = {"sweepBarId", "chochBreakBarId", "executionObBarId"}
    elif model == "DELIVERY_FVG_REPLACEMENT":
        model_fields = {
            "deliveryFvgBarId", "deliveryCausalObBarId",
            "deliveryProtectedSwingBarId",
        }
    else:
        raise V4ContractError(f"unsupported accepted execution model: {model}")
    missing_model = sorted(model_fields - set(execution))
    if missing_model:
        raise V4ContractError(
            "accepted execution role evidence is incomplete: " + ",".join(missing_model)
        )
    role_ids = nested_bar_ids(selected) | nested_bar_ids(selected_lineage) | {
        str(execution[key]) for key in model_fields
    }
    for role_id in role_ids:
        market.bar(role_id, as_of)
    objective_family = (selected.get("objectiveFamily") or {}).get(
        "orderedMembers", []
    )
    targets = []
    direction = str(family["direction"])
    for member in objective_family:
        row = market.bar(str(member["barId"]), as_of)
        targets.append(float(row["high"] if direction == "LONG" else row["low"]))
    if not any(abs(float(execution["target"]) - item) <= market.point / 2.0 for item in targets):
        raise V4ContractError("target is not an exact frozen objective-family wick")
    if direction == "LONG" and not float(execution["stop"]) < float(execution["entry"]) < float(execution["target"]):
        raise V4ContractError("accepted long geometry is invalid")
    if direction == "SHORT" and not float(execution["target"]) < float(execution["entry"]) < float(execution["stop"]):
        raise V4ContractError("accepted short geometry is invalid")
    return {
        "familyId": str(decision["familyId"]),
        "selectedScenarioSelectionId": selected_id,
        "auditorId": str(decision["auditorId"]),
        **execution,
        "selectedScenario": selected,
        "selectedLineagePath": selected_lineage,
        "rootObBarId": str(selected_lineage["root"]["obBarId"]),
        "finalChildObBarId": str(
            selected_lineage["refinements"][-1]["obBarId"]
        ),
        "objectiveBarId": str(selected["objective"]["barId"]),
        "scope": str(selected["scope"]),
        "roleIds": sorted(role_ids),
        "decisionHash": canonical_hash({"decision": decision, "execution": execution}),
    }


def validate_global_risk_exposure(executions: list[dict[str, Any]]) -> None:
    """Reject forged audit ledgers that bypass the frozen three-slot contract."""
    ordered = sorted(
        executions,
        key=lambda item: (
            parse_utc(str(item["orderCreatedAtUtc"])),
            str(item["executionId"]),
        ),
    )
    active: list[dict[str, Any]] = []
    for execution in ordered:
        created = parse_utc(str(execution["orderCreatedAtUtc"]))
        if not execution.get("closedAtUtc"):
            raise V4ContractError("accepted execution is missing closedAtUtc")
        active = [
            item for item in active
            if parse_utc(str(item["closedAtUtc"])) > created
        ]
        if len(active) >= 3:
            raise V4ContractError("accepted ledger exceeds three concurrent risk slots")
        if any(
            str(item["direction"]) != str(execution["direction"])
            for item in active
        ):
            raise V4ContractError("accepted ledger contains opposite concurrent risk")
        active.append(execution)


def validate_stateful_plan_sequence(
    *,
    market: MarketData,
    output: Path,
    families: dict[str, dict[str, Any]],
    queue: list[dict[str, Any]],
    plan_decisions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Replay PLAN approvals against the one persisted external-owner timeline."""
    expected_ids = [str(item["familyId"]) for item in queue]
    actual_ids = [str(item.get("familyId")) for item in plan_decisions]
    if actual_ids != expected_ids:
        raise V4ContractError(
            "chronological PLAN decisions do not match the frozen family queue"
        )
    authority: dict[str, Any] | None = None
    accepted_hashes: set[str] = set()
    rows: list[dict[str, Any]] = []
    valid: dict[str, dict[str, Any]] = {}
    timeline: list[dict[str, Any]] = []
    for queue_item, decision in zip(queue, plan_decisions):
        family_id = str(queue_item["familyId"])
        family = families[family_id]
        as_of_text = str(family["firstKnownAtUtc"])
        as_of = parse_utc(as_of_text)
        if str(decision.get("firstKnownAtUtc")) != as_of_text:
            raise V4ContractError(
                f"PLAN decision timestamp differs from first-known packet: {family_id}"
            )
        authority = resolved_external_authority(market, authority, as_of)
        before = copy.deepcopy(authority)
        base = {
            "auditType": "STATEFUL_PLAN_SEQUENCE",
            "auditorId": "engine-stateful-plan-validator",
            "auditSessionId": "gtv2-stateful-plan-v451",
            "familyId": family_id,
            "firstKnownAtUtc": as_of_text,
            "semanticVerdict": str(decision.get("verdict", "")),
            "authorityBefore": before,
        }
        if decision.get("verdict") != "PLAN_APPROVED":
            rows.append({
                **base,
                "statefulVerdict": "SEMANTIC_REJECT",
                "selectedScenarioSelectionId": None,
                "scenarioHash": None,
                "reason": str(decision.get("reason") or "PLAN_REJECTED"),
                "authorityAfter": copy.deepcopy(authority),
            })
            timeline.append({"at": as_of, "authority": copy.deepcopy(authority)})
            continue
        packet_path = ROOT / str(family["firstKnownPacketPath"])
        packet = json.loads(packet_path.read_text(encoding="utf-8-sig"))
        packet_family = next(
            (
                item for item in packet.get("physicalLineageFamilies", [])
                if str(item.get("familyId")) == family_id
            ),
            None,
        )
        if packet_family is None:
            raise V4ContractError(
                f"first-known packet omitted its family during stateful audit: {family_id}"
            )
        stateful_packet = {
            **packet,
            "externalMapAuthority": copy.deepcopy(authority),
            "physicalLineageFamilies": [packet_family],
        }
        payload = {
            "schemaVersion": "5.0.0",
            "decisions": [{
                "familyId": family_id,
                "action": "PLAN",
                "scenarioSelectionId": decision.get(
                    "selectedScenarioSelectionId"
                ),
                "semanticAudit": decision.get("semanticAudit") or {},
                "reason": str(decision.get("reason", "")),
            }],
        }
        try:
            frozen = freeze_plan_batch(
                payload,
                market,
                as_of,
                stateful_packet,
                accepted_hashes,
            )
            if len(frozen) != 1:
                raise V4ContractError(
                    "stateful PLAN approval did not freeze exactly one scenario"
                )
            scenario = frozen[0]
            next_authority = external_authority_from_scenario(
                scenario, authority
            )
        except V4ContractError as exc:
            rows.append({
                **base,
                "statefulVerdict": "STATEFUL_REJECT",
                "selectedScenarioSelectionId": decision.get(
                    "selectedScenarioSelectionId"
                ),
                "scenarioHash": None,
                "reason": str(exc),
                "authorityAfter": copy.deepcopy(authority),
            })
            timeline.append({"at": as_of, "authority": copy.deepcopy(authority)})
            continue
        accepted_hashes.add(str(scenario["scenarioHash"]))
        authority = next_authority
        valid[family_id] = {
            "scenario": scenario,
            "authorityAtPlan": before,
            "authorityAfterPlan": copy.deepcopy(authority),
        }
        rows.append({
            **base,
            "statefulVerdict": "PASS",
            "selectedScenarioSelectionId": decision.get(
                "selectedScenarioSelectionId"
            ),
            "scenarioHash": str(scenario["scenarioHash"]),
            "reason": "PLAN_FROZEN_ON_PERSISTED_OWNER_TIMELINE",
            "authorityAfter": copy.deepcopy(authority),
        })
        timeline.append({"at": as_of, "authority": copy.deepcopy(authority)})
    return rows, valid, timeline


def authority_at(
    market: MarketData,
    timeline: list[dict[str, Any]],
    as_of: int,
) -> dict[str, Any] | None:
    authority = None
    for item in timeline:
        if int(item["at"]) > int(as_of):
            break
        authority = copy.deepcopy(item.get("authority"))
    return resolved_external_authority(market, authority, as_of)


def validate_scenario_authority_at_order(
    scenario: dict[str, Any],
    authority: dict[str, Any] | None,
) -> None:
    scope = str(scenario.get("scope"))
    if scope == "INTERNAL_ROTATION":
        if authority and str(authority.get("status")) == "REMAP_REQUIRED":
            raise V4ContractError(
                "internal rotation order was created while external authority required remap"
            )
        return
    external_authority_from_scenario(scenario, authority)


def finalize(args: argparse.Namespace) -> int:
    output = Path(args.output).resolve()
    manifest_path = output / "manifest.json"
    if not manifest_path.exists():
        raise V4ContractError("run discover before finalize")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if int(manifest.get("engineCandidateMissCount", 0)):
        raise V4ContractError("ENGINE_CANDIDATE_MISS must be zero before finalization")
    audit_paths = {
        "chronological": Path(args.chronological_audit).resolve(),
        "counterfactual": Path(args.counterfactual_audit).resolve(),
        "noTrade": Path(args.no_trade_audit).resolve(),
        "triggerRole": Path(args.trigger_coverage_audit).resolve(),
        "statefulPlan": Path(args.stateful_plan_audit).resolve(),
    }
    audit_types = {
        "chronological": "CHRONOLOGICAL",
        "counterfactual": "COUNTERFACTUAL_SHUFFLED",
        "noTrade": "NO_TRADE_DAILY_MTF",
        "triggerRole": "TRIGGER_PACKET_ROLE_EVIDENCE",
        "statefulPlan": "STATEFUL_PLAN_SEQUENCE",
    }
    audits = {
        key: verify_hash_chain(path, audit_types[key])
        for key, path in audit_paths.items()
    }
    audit_identities: dict[str, tuple[str, str]] = {}
    for key, rows in audits.items():
        if not rows:
            raise V4ContractError(f"{key} audit ledger is empty")
        identities = {
            (str(row.get("auditorId", "")), str(row.get("auditSessionId", "")))
            for row in rows
        }
        if len(identities) != 1 or any(not value for value in next(iter(identities))):
            raise V4ContractError(f"{key} audit provenance is incomplete or mixed")
        audit_identities[key] = next(iter(identities))
    if len(set(audit_identities.values())) != len(audit_identities):
        raise V4ContractError("independent audits reused an auditor/session identity")
    file_hashes = [sha256_file(path) for path in audit_paths.values()]
    if len(file_hashes) != len(set(file_hashes)):
        raise V4ContractError("independent audit ledgers are byte-identical/reused")

    decisions = audits["chronological"]
    families = {
        str(item["familyId"]): item
        for item in read_jsonl(output / "family_ledger.jsonl")
    }
    response_ids = [str(item.get("familyId")) for item in decisions]
    if len(response_ids) != len(set(response_ids)) or set(response_ids) != set(families):
        raise V4ContractError("semantic audit must decide every family exactly once")
    chronological_queue = json.loads(
        (output / "chronological_audit_queue.json").read_text(encoding="utf-8-sig")
    )
    if canonical_hash(chronological_queue) != manifest["auditQueueHashes"]["chronological"]:
        raise V4ContractError("chronological queue hash changed after discovery")
    if response_ids != [str(item["familyId"]) for item in chronological_queue]:
        raise V4ContractError("chronological audit order does not match its frozen queue")

    counter_rows = audits["counterfactual"]
    counter_queue = json.loads(
        (output / "counterfactual_audit_queue.json").read_text(encoding="utf-8-sig")
    )
    if [str(item.get("familyId")) for item in counter_rows] != [
        str(item["familyId"]) for item in counter_queue
    ]:
        raise V4ContractError("counterfactual audit did not preserve shuffled queue order")
    if canonical_hash(counter_queue) != manifest["auditQueueHashes"]["counterfactual"]:
        raise V4ContractError("counterfactual queue hash changed after discovery")
    chronological_by_id = {str(item["familyId"]): item for item in decisions}
    for row in counter_rows:
        original = chronological_by_id.get(str(row.get("familyId")))
        if original is None:
            raise V4ContractError("counterfactual audit contains an unknown family")
        if row.get("verdict") != original.get("verdict"):
            raise V4ContractError("counterfactual verdict disagrees with chronological audit")
        if row.get("verdict") == "ACCEPT" and row.get(
            "selectedScenarioSelectionId"
        ) != original.get("selectedScenarioSelectionId"):
            raise V4ContractError("counterfactual scenario selection disagrees")
        if row.get("verdict") == "ACCEPT" and [
            str(item.get("executionId")) for item in row.get("executions", [])
        ] != [
            str(item.get("executionId")) for item in original.get("executions", [])
        ]:
            raise V4ContractError("counterfactual execution set disagrees")

    no_trade_queue = json.loads(
        (output / "no_trade_audit_queue.json").read_text(encoding="utf-8-sig")
    )
    if canonical_hash(no_trade_queue) != manifest["auditQueueHashes"]["noTrade"]:
        raise V4ContractError("no-trade queue hash changed after discovery")
    expected_days = [str(item["dayUtc"]) for item in no_trade_queue]
    no_trade_rows = audits["noTrade"]
    if [str(item.get("dayUtc")) for item in no_trade_rows] != expected_days:
        raise V4ContractError("daily no-trade audit has missing, duplicate, or reordered days")
    for row in no_trade_rows:
        if not isinstance(row.get("reviewedH1BarIds"), list) or not isinstance(
            row.get("reviewedM30BarIds"), list
        ) or not isinstance(row.get("reviewedM5TransferIntervals"), list):
            raise V4ContractError("daily no-trade MTF evidence is incomplete")
        validate_no_trade_audit_conclusion(row)
        expected = next(
            item for item in no_trade_queue
            if str(item["dayUtc"]) == str(row["dayUtc"])
        )
        if set(map(str, row["reviewedH1BarIds"])) != set(
            map(str, expected["requiredH1BarIds"])
        ):
            raise V4ContractError("daily H1 no-trade audit coverage is incomplete")
        if set(map(str, row["reviewedM30BarIds"])) != set(
            map(str, expected["requiredM30BarIds"])
        ):
            raise V4ContractError("daily M30 no-trade audit coverage is incomplete")
        reviewed_m5 = {
            str(item.get("barId") if isinstance(item, dict) else item)
            for item in row["reviewedM5TransferIntervals"]
        }
        if reviewed_m5 != set(map(str, expected["requiredM5TransferBarIds"])):
            raise V4ContractError("daily M5 transfer no-trade audit coverage is incomplete")
        evidence_images = row.get("evidenceImages")
        if not isinstance(evidence_images, list) or len(evidence_images) < 4:
            raise V4ContractError("daily no-trade visual evidence is incomplete")
        checkpoints = {str(item.get("asOfUtc")) for item in evidence_images}
        day_start = parse_utc(str(row["dayUtc"]) + "T00:00:00Z")
        expected_checkpoints = {
            utc_text(day_start + hours * 3600) for hours in (6, 12, 18, 24)
        }
        if checkpoints != expected_checkpoints:
            raise V4ContractError("daily no-trade checkpoint coverage is incomplete")
        for image in evidence_images:
            image_path = Path(str(image.get("path", "")))
            if not image_path.is_absolute():
                image_path = ROOT / image_path
            if not image_path.exists() or sha256_file(image_path) != str(
                image.get("sha256", "")
            ):
                raise V4ContractError(
                    "daily no-trade evidence image is missing or changed"
                )
    dataset = Path(manifest["dataset"])
    market = MarketData.from_npz(
        dataset,
        parse_utc(manifest["period"]["warmupStartUtc"]),
        parse_utc(manifest["period"]["replayEndUtc"]),
        float(args.point),
    )
    plan_decisions = read_jsonl(
        Path(args.chronological_plan_decisions).resolve()
    )
    expected_stateful_rows, stateful_valid, authority_timeline = (
        validate_stateful_plan_sequence(
            market=market,
            output=output,
            families=families,
            queue=chronological_queue,
            plan_decisions=plan_decisions,
        )
    )
    recorded_stateful_rows = audits["statefulPlan"]
    if len(recorded_stateful_rows) != len(expected_stateful_rows):
        raise V4ContractError("stateful PLAN audit row count is incomplete")
    for expected, recorded in zip(expected_stateful_rows, recorded_stateful_rows):
        body = {
            key: value
            for key, value in recorded.items()
            if key not in {"previousHash", "recordHash"}
        }
        if body != expected:
            raise V4ContractError(
                "stateful PLAN audit differs from deterministic owner replay"
            )
    accepted: list[dict[str, Any]] = []
    for decision in decisions:
        if decision.get("verdict") == "REJECT":
            if not decision.get("reason"):
                raise V4ContractError("rejected family requires an explicit reason")
            continue
        if decision.get("verdict") != "ACCEPT":
            raise V4ContractError("verdict must be ACCEPT or REJECT")
        family = families[str(decision["familyId"])]
        stateful = stateful_valid.get(str(decision["familyId"]))
        if stateful is None:
            raise V4ContractError(
                "accepted execution belongs to a PLAN rejected by stateful owner replay"
            )
        executions = decision.get("executions")
        if not isinstance(executions, list) or not executions:
            raise V4ContractError("accepted family requires at least one execution")
        first_packet_path = ROOT / str(family["firstKnownPacketPath"])
        first_packet = json.loads(first_packet_path.read_text(encoding="utf-8-sig"))
        first_supplied = packet_bar_ids(first_packet)
        selected_id = str(decision["selectedScenarioSelectionId"])
        selected_scenario = next(
            item for item in family.get("scenarioOptions", [])
            if str(item["scenarioSelectionId"]) == selected_id
        )
        selected_scenario_roles = nested_bar_ids(selected_scenario)
        if not selected_scenario_roles <= first_supplied:
            raise V4ContractError(
                "accepted Ground Truth role was absent at first judgment time"
            )
        for execution in executions:
            order_as_of = parse_utc(str(execution["orderCreatedAtUtc"]))
            order_authority = authority_at(
                market, authority_timeline, order_as_of
            )
            validate_scenario_authority_at_order(
                stateful["scenario"], order_authority
            )
            accepted.append(validate_selected_trade(market, family, decision, execution))
    validate_global_risk_exposure(accepted)
    accepted_ids = {str(item["executionId"]) for item in accepted}
    trigger_rows = audits["triggerRole"]
    trigger_queue = json.loads(
        (output / "trigger_role_audit_queue.json").read_text(encoding="utf-8-sig")
    )
    if canonical_hash(trigger_queue) != manifest["auditQueueHashes"]["triggerRole"]:
        raise V4ContractError("trigger-role queue hash changed after discovery")
    if {str(item.get("executionId")) for item in trigger_rows} != accepted_ids:
        raise V4ContractError("trigger role audit must cover every accepted execution exactly once")
    if len(trigger_rows) != len(accepted_ids):
        raise V4ContractError("trigger role audit contains duplicate families")
    accepted_by_id = {str(item["executionId"]): item for item in accepted}
    for row in trigger_rows:
        execution_id = str(row["executionId"])
        packet_path = Path(str(row.get("triggerPacketPath", "")))
        if not packet_path.is_absolute():
            packet_path = ROOT / packet_path
        if not packet_path.exists() or sha256_file(packet_path) != row.get(
            "triggerPacketSha256"
        ):
            raise V4ContractError("trigger packet is missing or its hash changed")
        packet = json.loads(packet_path.read_text(encoding="utf-8-sig"))
        supplied = packet_bar_ids(packet) | nested_bar_ids(packet)
        accepted_execution = accepted_by_id[execution_id]
        required_keys = (
            ("sweepBarId", "chochBreakBarId", "executionObBarId")
            if accepted_execution["executionModel"] == "HTF_OB_REACTION"
            else (
                "deliveryFvgBarId", "deliveryCausalObBarId",
                "deliveryProtectedSwingBarId",
            )
        )
        required_trigger_ids = {
            str(accepted_execution[key]) for key in required_keys
        }
        if not required_trigger_ids <= supplied:
            raise V4ContractError("accepted trigger role was absent from its as-of packet")
        packet_as_of_text = packet.get("asOfUtc") or packet.get("decisionAtUtc")
        if not packet_as_of_text:
            raise V4ContractError("trigger packet has no decision timestamp")
        packet_as_of = parse_utc(str(packet_as_of_text))
        if any(
            market.bar(role_id, packet_as_of)["available"] > packet_as_of
            for role_id in required_trigger_ids
        ):
            raise V4ContractError("trigger packet references a future role candle")
    writer = HashChainWriter(output / "accepted_ground_truth.jsonl")
    for item in sorted(accepted, key=lambda value: parse_utc(value["decisionAtUtc"])):
        writer.append(item)
    manifest.update({
        "status": "FROZEN_GROUND_TRUTH_V2",
        "groundTruthComplete": True,
        "acceptedTradeCount": len(accepted),
        "auditLedgerSha256": {
            key: sha256_file(path) for key, path in audit_paths.items()
        },
        "auditProvenance": {
            key: {"auditorId": value[0], "auditSessionId": value[1]}
            for key, value in audit_identities.items()
        },
        "acceptedLedgerTipHash": writer.previous,
        "agentsSha256": sha256_file(ROOT / "AGENTS.md"),
        "contractsManifestSha256": sha256_file(CONTRACTS_MANIFEST),
        "statefulPlanPassCount": len(stateful_valid),
    })
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    blocked_report = output / "BLOCKED_REPORT.md"
    if blocked_report.exists():
        blocked_report.unlink()
    (output / "COMPLETION_REPORT.md").write_text(
        "\n".join([
            "# Ground Truth V2 - COMPLETE",
            "",
            f"- Pipeline: `{manifest['pipelineVersion']}`",
            f"- Candidate families: `{manifest['familyCount']}`",
            f"- Stateful PLAN passes: `{len(stateful_valid)}`",
            f"- Accepted executions: `{len(accepted)}`",
            "- Ground truth complete: `true`",
            "",
            "Completion requires deterministic chronological owner replay,",
            "independent semantic audits, trigger-role coverage, and risk-slot validation.",
        ]) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"GROUND_TRUTH_V2_FROZEN trades={len(accepted)} output={output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build raw-M1 Ground Truth V2 without oracle or legacy candidates"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    discover_parser = sub.add_parser("discover")
    discover_parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    discover_parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    discover_parser.add_argument("--symbol", default="GOLD")
    discover_parser.add_argument("--point", type=float, default=0.01)
    discover_parser.add_argument("--warmup-start", default="2023-12-01T00:00:00Z")
    discover_parser.add_argument("--replay-start", default="2026-06-01T00:00:00Z")
    discover_parser.add_argument("--replay-end", default="2026-07-01T00:00:00Z")
    discover_parser.set_defaults(func=discover)
    finalize_parser = sub.add_parser("finalize")
    finalize_parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    finalize_parser.add_argument("--chronological-audit", required=True)
    finalize_parser.add_argument("--counterfactual-audit", required=True)
    finalize_parser.add_argument("--no-trade-audit", required=True)
    finalize_parser.add_argument("--trigger-coverage-audit", required=True)
    finalize_parser.add_argument("--stateful-plan-audit", required=True)
    finalize_parser.add_argument("--chronological-plan-decisions", required=True)
    finalize_parser.add_argument("--point", type=float, default=0.01)
    finalize_parser.set_defaults(func=finalize)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return int(args.func(args))
    except (OSError, ValueError, V4ContractError) as exc:
        print(f"GROUND_TRUTH_V2_FAILED: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
