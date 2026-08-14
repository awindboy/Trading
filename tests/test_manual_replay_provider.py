from __future__ import annotations

import json
from pathlib import Path
import tempfile
import threading
import time
import unittest

from scripts.manual_replay_provider import wait_for_manual_decision


class ManualReplayProviderTests(unittest.TestCase):
    def test_invalid_schema_decision_waits_for_corrected_file(self) -> None:
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["phase", "action"],
            "properties": {
                "phase": {"const": "MAP_SCOUT"},
                "action": {"enum": ["NO_CANDIDATE", "CANDIDATE"]},
            },
        }
        result: list[object] = []

        with tempfile.TemporaryDirectory() as temporary_directory:
            request_dir = Path(temporary_directory)

            def run_provider() -> None:
                try:
                    result.append(
                        wait_for_manual_decision(
                            request_dir=request_dir,
                            prompt="bounded prompt",
                            images=[],
                            response_schema=schema,
                            timeout_seconds=3,
                        )
                    )
                except BaseException as exc:  # Surface thread failures to the test.
                    result.append(exc)

            thread = threading.Thread(target=run_provider)
            thread.start()
            request_path = request_dir / "manual_request.json"
            deadline = time.monotonic() + 1
            while not request_path.exists() and time.monotonic() < deadline:
                time.sleep(0.01)

            request = json.loads(request_path.read_text(encoding="utf-8"))
            self.assertEqual(schema, request["responseSchema"])

            decision_path = request_dir / "manual_decision.json"
            decision_path.write_text(
                json.dumps({"phase": "MAP_SCOUT", "action": "INVALID"}),
                encoding="utf-8",
            )
            time.sleep(0.4)
            self.assertTrue(thread.is_alive())

            decision_path.write_text(
                json.dumps({"phase": "MAP_SCOUT", "action": "NO_CANDIDATE"}),
                encoding="utf-8",
            )
            thread.join(timeout=2)

        self.assertFalse(thread.is_alive())
        self.assertEqual(1, len(result))
        self.assertFalse(isinstance(result[0], BaseException), result[0])
        self.assertEqual("NO_CANDIDATE", result[0].payload["action"])


if __name__ == "__main__":
    unittest.main()
