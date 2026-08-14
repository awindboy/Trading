from __future__ import annotations

import unittest

from scripts.mentor_ai_replay import bounded_map_review_prompt, load_stage_contract
from scripts.mentor_replay_v2 import map_review_prompt


class MapReviewPromptBoundsTest(unittest.TestCase):
    def test_compacts_previous_candidate_and_bounds_packet_metadata(self) -> None:
        contract, _ = load_stage_contract("MAP")
        candidates = [
            {
                "candidateId": f"MAP-CANDIDATE-{index}",
                "direction": "SHORT",
                "rootBarId": f"M30:{1000 + index}",
                "objectiveBarId": f"M15:{2000 + index}",
                "objectiveSide": "SSL",
                "resolvedRootOhlc": {
                    "barId": f"M30:{1000 + index}",
                    "o": 3930.95,
                    "h": 3936.22,
                    "l": 3921.55,
                    "c": 3932.45,
                },
                "resolvedObjectiveOhlc": {
                    "barId": f"M15:{2000 + index}",
                    "o": 3897.06,
                    "h": 3903.90,
                    "l": 3886.29,
                    "c": 3897.33,
                },
                "objectiveStructure": {
                    "tf": "M15",
                    "side": "SSL",
                    "prominencePrice": 24.65,
                    "reactionExcursionPrice": 24.65,
                    "barsSinceConfirmed": index,
                },
            }
            for index in range(1, 4)
        ]
        previous = {
            **candidates[0],
            "reason": "stale previous-candidate prose " * 300,
            "rootCausality": "not reviewer evidence " * 300,
        }
        packet = {
            "symbol": "GOLD",
            "asOfUtc": "2025-10-28T12:33:00Z",
            "phase": "MAP",
            "lastClosedM1": {
                "openTimeUtc": "2025-10-28T12:32:00Z",
                "open": 3909.25,
                "high": 3913.34,
                "low": 3908.86,
                "close": 3911.97,
            },
            "spreadPrice": 0.30,
            "brokerStopsLevelPrice": 0.0,
            "candleEvidence": [],
            "localTriggerWakeup": {
                "kind": "LOCAL_FLAT_DELIVERY_CANDIDATE",
                "screeningOnly": True,
                "candidateRootBarId": "M15:1761651900",
                "warning": "Timing alarm only; independently prove map causality.",
            },
            "futureHidden": True,
            "contractHashes": {
                "common": "a" * 1800,
                "map": "b" * 1800,
            },
        }
        raw_prompt = map_review_prompt(contract, packet, candidates, previous)
        self.assertGreater(len(raw_prompt.encode("utf-8")), 8000)
        self.assertNotIn("stale previous-candidate prose", raw_prompt)

        prompt, metrics = bounded_map_review_prompt(
            contract,
            packet,
            candidates,
            previous,
            {"maximumMapReviewPromptBytes": 8000},
        )

        self.assertLessEqual(metrics["promptBytes"], 8000)
        self.assertEqual(metrics["maximumPromptBytes"], 8000)
        self.assertNotIn("contractHashes", prompt)
        for candidate in candidates:
            self.assertIn(candidate["candidateId"], prompt)
            self.assertIn(candidate["rootBarId"], prompt)
            self.assertIn(candidate["objectiveBarId"], prompt)


if __name__ == "__main__":
    unittest.main()
