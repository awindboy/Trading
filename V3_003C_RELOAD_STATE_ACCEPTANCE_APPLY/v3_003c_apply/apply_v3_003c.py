#!/usr/bin/env python3
from pathlib import Path
import shutil
import subprocess
import sys

EXPECTED_HEAD = "8d2971c369df5564d41fa4fe2499ed894f5dedb6"
ROOT = Path(__file__).resolve().parent
PAYLOAD = ROOT / "payload"


def fail(msg: str):
    print("FAIL-CLOSED:", msg, file=sys.stderr)
    raise SystemExit(2)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


if not (Path.cwd() / ".git").exists():
    fail("run from the Trading repository root")

head = git("rev-parse", "HEAD")
if head != EXPECTED_HEAD:
    fail(f"unexpected Git HEAD {head}; expected {EXPECTED_HEAD}. Re-check latest GitHub first.")

status = git("status", "--porcelain")
if status:
    fail("working tree is not clean; commit/stash/review local changes before applying")

handoff = Path("docs/ea/v3/HANDOFF_V3.md")
backlog = Path("docs/ea/v3/BACKLOG_V3.md")
decisions = Path("docs/ea/DECISIONS.md")
for p in (handoff, backlog, decisions):
    if not p.exists():
        fail(f"missing expected file: {p}")

ht = handoff.read_text(encoding="utf-8-sig")
bt = backlog.read_text(encoding="utf-8-sig")
dt = decisions.read_text(encoding="utf-8-sig")

if "V3-002 / V3-003 routing update" not in ht:
    fail("HANDOFF missing expected V3-003 routing marker")
if "V3-003C routing update" in ht:
    fail("V3-003C HANDOFF update already present")
if "## V3-003" not in bt:
    fail("BACKLOG missing V3-003 section")
if "## V3-003C" in bt:
    fail("V3-003C backlog already present")
if "## D-159" not in dt:
    fail("DECISIONS missing D-159")
if "## D-160" in dt:
    fail("D-160 already exists; re-read latest project state")

for rel in [
    Path("docs/ea/v3/V3_003C_RELOAD_STATE_ACCEPTANCE_RESULTS.md"),
    Path("scripts/v3_003c_reload_state_acceptance_probe.py"),
]:
    src = PAYLOAD / rel
    dst = Path(rel)
    if not src.exists():
        fail(f"package payload missing: {src}")
    if dst.exists():
        fail(f"refusing to overwrite existing file: {dst}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

ht = ht.replace("Last updated: `2026-08-24`", "Last updated: `2026-08-26`", 1)
ht = ht.replace(
    "Current phase: `V3-001 RAW DATA LAB BOOTSTRAP`",
    "Current phase: `V3-003 GOLD AUCTION-STATE RECONSTRUCTION`",
    1,
)
ht += r"""

## V3-003C routing update — 2026-08-26

Read:

```text
V3_003C_RELOAD_STATE_ACCEPTANCE_RESULTS.md
```

V3-003C produced the first fully reproducible reload-continuation development candidate in
this V3 line.

Reference interaction:

```text
active higher delivery state
+
intermediate persistent-liquidity reaction
+
decisive local M5 acceptance
```

where decisive acceptance means:

```text
acceptance beyond the actually broken M5 structure level
>
source-liquidity penetration beyond the swept level
```

Reference M15-k2 Level-A results:

```text
2023 40 / 60.0%
2024 29 / 65.5%
2025 27 / 63.0%
```

Exact mirrors are materially weaker in all three years.

Important authority boundary:
- delivery state alone is not promoted;
- local acceptance alone is not promoted;
- the observed development edge is the interaction;
- no production Entry/SL/TP/EA change is authorized;
- no quarter/session/direction/objective-room veto is authorized;
- forced reversal remains unapproved.

Freeze the exact reference as:

```text
V3_RELOAD_CANDIDATE_A
```

for future comparison. New correction-completion ideas must be separate variants and must
not rewrite Candidate A.

2022 remains closed until independent validation is intentionally run under the frozen
candidate. 2021 remains untouched.
"""

bt += r"""

## V3-003C — reload state × local acceptance

- [x] Reconstruct a reproducible intermediate-liquidity M5-acceptance control from raw GOLD.
- [x] Reuse the frozen structural-expansion meaning `recent4/prior4 > 1.0` without P/L retuning.
- [x] Add explicit M30/H1 BOS-owner delivery agreement as an alternative delivery-state fact.
- [x] Show that delivery state alone is incomplete.
- [x] Define natural local acceptance dominance: broken-structure acceptance distance > sweep penetration distance.
- [x] Show that local acceptance alone is not an edge.
- [x] Demonstrate the state × acceptance interaction on 2023/2024/2025.
- [x] Compare exact mirror direction.
- [x] Check long/short breadth and quarter composition without creating calendar gates.
- [x] Separate local-trigger invalidation from dynamic delivery-state loss.
- [x] Check zero-spread counterfactual; friction does not explain the interaction.
- [x] Check natural M15/M30 source-scale sensitivity; do not optimize `k` from P/L.
- [x] Keep objective-room context non-authoritative.
- [x] Freeze `V3_RELOAD_CANDIDATE_A` as a development benchmark.
- [ ] Do not modify Candidate A while testing correction-completion / acceptance-persistence variants.
- [ ] Prepare independent 2022 validation contract; open 2022 only under frozen definitions.
- [ ] Reject rather than retune if 2022 reverses the relationship.
- [ ] If independent validation survives, promote to exact-tick replay before MT5 implementation.
- [ ] Keep 2021 untouched.
"""

dt += r"""

## D-160 — Freeze the V3 reload state × local-acceptance interaction as Candidate A

Status: `ACTIVE RESEARCH DECISION / 2026-08-26`

Decision:
- V3-003C establishes `V3_RELOAD_CANDIDATE_A` as the first fully reproducible reload-continuation development benchmark in the current GOLD V3 line.
- Candidate A is **not** production strategy authority and does not modify V1/V2 or any EA source.
- The relevant observation is an interaction: active higher delivery state **and** decisive local structure acceptance. Neither component receives independent Entry authority.
- Higher delivery state is represented by either the already-frozen M30 recent4/prior4 structural expansion ratio `> 1.0` or explicit same-direction M30+H1 BOS-owner agreement at the sweep.
- Decisive local acceptance is defined geometrically: the M5 trigger close accepts beyond the actually broken M5 structure level by more distance than the source liquidity was penetrated during the sweep.
- Do not add FVG hard gates, objective-room vetoes, quarter/session gates, direction vetoes, generic SL widening, or forced reversal from this result.
- The exact historical V3-002 `38/46/43` selective-continuation implementation was not committed and is not falsely claimed as reproduced; Candidate A is independently reproducible from raw data.
- New correction-completion / acceptance-persistence ideas are separate variants and may not rewrite Candidate A after seeing their results.
- 2022 remains the independent validation vault. When intentionally opened, Candidate A must be run without threshold movement; failure means reject/demote rather than retune.
- 2021 remains untouched.
"""

handoff.write_text(ht, encoding="utf-8")
backlog.write_text(bt, encoding="utf-8")
decisions.write_text(dt, encoding="utf-8")

record = Path("docs/ea/v3/V3_003C_APPLY_RECORD.txt")
record.write_text(
    "Applied: 2026-08-26\n"
    f"Required base HEAD: {EXPECTED_HEAD}\n"
    "Package: V3_003C_RELOAD_STATE_ACCEPTANCE_APPLY\n"
    "No EA source modified.\n"
    "2022 validation vault remains closed.\n"
    "2021 remains untouched.\n",
    encoding="utf-8",
)

subprocess.run(["git", "diff", "--check"], check=True)
print("Applied V3-003C research package successfully.")
print("Review with: git diff -- docs/ea scripts/v3_003c_reload_state_acceptance_probe.py")
