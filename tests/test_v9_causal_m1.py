#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "v9_causal_m1.py"
HEADER = "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>\n"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_source(path: Path, n: int = 40) -> None:
    start = datetime(2025, 2, 20, 9, 0)
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write(HEADER)
        for i in range(n):
            ts = start + timedelta(minutes=i)
            p = 2940.0 + i * 0.1
            f.write(
                f"{ts:%Y.%m.%d}\t{ts:%H:%M:%S}\t{p:.2f}\t{p+0.2:.2f}\t{p-0.2:.2f}\t{p+0.1:.2f}\t10\t0\t20\n"
            )


class CausalHarnessTest(unittest.TestCase):
    def run_cli(self, *args: str, expect: int = 0):
        cp = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
        self.assertEqual(cp.returncode, expect, msg=cp.stdout + "\n" + cp.stderr)
        return cp

    def test_init_and_advance_are_cutoff_exact(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            src, out, state = d / "source.tsv", d / "revealed.tsv", d / "state.json"
            make_source(src)
            h = sha(src)
            self.run_cli(
                "init", "--source", str(src), "--expected-sha256", h,
                "--history-start", "2025-02-20 09:05:00",
                "--cutoff", "2025-02-20 09:10:00",
                "--output", str(out), "--state", str(state),
            )
            text = out.read_text(encoding="utf-8")
            self.assertIn("09:10:00", text)
            self.assertNotIn("09:11:00", text)
            s1 = json.loads(state.read_text(encoding="utf-8"))
            self.assertEqual(s1["cutoff"], "2025-02-20 09:10:00")

            self.run_cli(
                "advance", "--source", str(src), "--expected-sha256", h,
                "--cutoff", "2025-02-20 09:15:00",
                "--output", str(out), "--state", str(state),
            )
            text = out.read_text(encoding="utf-8")
            self.assertIn("09:15:00", text)
            self.assertNotIn("09:16:00", text)
            s2 = json.loads(state.read_text(encoding="utf-8"))
            self.assertGreater(s2["resume_offset"], s1["resume_offset"])

    def test_wrong_hash_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            src = d / "source.tsv"
            make_source(src)
            cp = self.run_cli("verify", "--source", str(src), "--expected-sha256", "0" * 64, expect=2)
            self.assertIn("SHA256 mismatch", cp.stderr)

    def test_modified_revealed_file_blocks_advance(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            src, out, state = d / "source.tsv", d / "revealed.tsv", d / "state.json"
            make_source(src)
            h = sha(src)
            self.run_cli(
                "init", "--source", str(src), "--expected-sha256", h,
                "--history-start", "2025-02-20 09:05:00",
                "--cutoff", "2025-02-20 09:10:00",
                "--output", str(out), "--state", str(state),
            )
            out.write_text(out.read_text(encoding="utf-8") + "#tamper\n", encoding="utf-8")
            cp = self.run_cli(
                "advance", "--source", str(src), "--expected-sha256", h,
                "--cutoff", "2025-02-20 09:15:00",
                "--output", str(out), "--state", str(state), expect=2,
            )
            self.assertIn("modified", cp.stderr)


if __name__ == "__main__":
    unittest.main()
