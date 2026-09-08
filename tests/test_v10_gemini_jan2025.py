from __future__ import annotations

import csv
import hashlib
import importlib.util
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "v10_gemini_jan2025.py"
SPEC = importlib.util.spec_from_file_location("v10_gemini_jan2025", SCRIPT)
assert SPEC and SPEC.loader
V10 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = V10
SPEC.loader.exec_module(V10)


class V10GeminiReplayTests(unittest.TestCase):
    def write_source(self, path: Path) -> None:
        start = datetime(2024, 1, 1, 0, 0)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerow(V10.EXPECTED_HEADER)
            for index in range(12):
                timestamp = start + timedelta(minutes=index)
                price = 2000 + index
                writer.writerow([
                    timestamp.strftime("%Y.%m.%d"), timestamp.strftime("%H:%M:%S"),
                    price, price + 1, price - 1, price + 0.5, 1, 0, 10,
                ])

    def test_revealed_rows_end_exactly_at_cutoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "m1.tsv"
            self.write_source(source)
            cutoff = datetime(2024, 1, 1, 0, 5)
            rows = V10.load_revealed_m1(source, cutoff)
            self.assertEqual(rows[-1].start, cutoff)
            self.assertEqual(len(rows), 6)

    def test_missing_exact_cutoff_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "m1.tsv"
            self.write_source(source)
            with self.assertRaises(V10.V10Error):
                V10.load_revealed_m1(source, datetime(2024, 1, 1, 1, 0))

    def test_incremental_cache_matches_full_rescan_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "m1.tsv"
            cache = Path(tmp) / "market_cache.json"
            self.write_source(source)
            expected_sha = hashlib.sha256(source.read_bytes()).hexdigest()
            first_cutoff = datetime(2024, 1, 1, 0, 5)
            second_cutoff = datetime(2024, 1, 1, 0, 10)

            _, first_cache, first_action = V10.load_or_advance_market_cache(
                source, first_cutoff, cache, expected_sha
            )
            frames, second_cache, second_action = V10.load_or_advance_market_cache(
                source, second_cutoff, cache, expected_sha
            )
            reused_frames, _, reused_action = V10.load_or_advance_market_cache(
                source, second_cutoff, cache, expected_sha
            )

            self.assertEqual(first_action, "initialized")
            self.assertEqual(second_action, "advanced")
            self.assertEqual(reused_action, "reused")
            self.assertEqual(first_cache["revealedRows"], 6)
            self.assertEqual(second_cache["revealedRows"], 11)
            self.assertEqual(frames["M1"][-1].start, second_cutoff)
            self.assertEqual(
                V10.serialize_frames(reused_frames), V10.serialize_frames(frames)
            )

            revealed = V10.load_revealed_m1(source, second_cutoff)
            legacy = {
                name: V10.aggregate(revealed, minutes)[-V10.FRAME_WINDOWS[name]:]
                for name, minutes in V10.FRAME_MINUTES.items()
            }
            self.assertEqual(V10.serialize_frames(frames), V10.serialize_frames(legacy))

    def test_incremental_cache_detects_source_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "m1.tsv"
            cache = Path(tmp) / "market_cache.json"
            self.write_source(source)
            expected_sha = hashlib.sha256(source.read_bytes()).hexdigest()
            cutoff = datetime(2024, 1, 1, 0, 5)
            V10.load_or_advance_market_cache(source, cutoff, cache, expected_sha)

            with source.open("a", encoding="utf-8") as handle:
                handle.write("tampered\n")

            with self.assertRaises(V10.V10Error):
                V10.load_or_advance_market_cache(source, cutoff, cache, expected_sha)

    def test_contract_does_not_contain_january_answers(self):
        contract = V10.CONTRACT.read_text(encoding="utf-8")
        forbidden = ["PAPER-001", "2653.74", "2649.32", "-1.04R", "C001"]
        for value in forbidden:
            self.assertNotIn(value, contract)

    def test_decision_rejects_hold_while_flat(self):
        decision = {
            "schemaVersion": "v10-1",
            "cutoff": "2025-01-02 12:00:00",
            "action": "HOLD",
            "direction": "LONG",
        }
        with self.assertRaises(V10.V10Error):
            V10.validate_decision(decision, datetime(2025, 1, 2, 12, 0), None)


if __name__ == "__main__":
    unittest.main()
