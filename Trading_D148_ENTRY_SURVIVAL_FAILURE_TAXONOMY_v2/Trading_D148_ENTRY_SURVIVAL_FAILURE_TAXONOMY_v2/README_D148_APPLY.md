# D-148 ENTRY SURVIVAL FAILURE TAXONOMY v2 — apply / validate

Target repository:

```text
repo: awindboy/Trading
required HEAD: 1889f9d5c53bc37e6061b9e309fa11b1534c1123
target build: 1.94R1L10 / ENTRY_SURVIVAL_FAILURE_TAXONOMY_V1_SHADOW
strategy authority: NONE
```

This package adds a **shadow-only** taxonomy for EXTERNAL_CONTINUATION fills that hit the original normalized SL before first +1R. It does not change Entry, original SL, structural TP, position sizing, scenario authorization, map state, broker lifecycle, or D-147 exit behavior. For D-148 research runs, select `V1_EXIT_ORIGINAL`.

`AGENTS.md` and `EA_SPEC.md` are not modified. `2021` remains untouched.

## Apply

Extract this folder anywhere inside the Trading repository, then from the repository root run:

```powershell
python .\Trading_D148_ENTRY_SURVIVAL_FAILURE_TAXONOMY_v2\tools\apply_d148_entry_survival_failure_taxonomy.py
```

If your launcher is `py`:

```powershell
py .\Trading_D148_ENTRY_SURVIVAL_FAILURE_TAXONOMY_v2\tools\apply_d148_entry_survival_failure_taxonomy.py
```

The installer is fail-closed and idempotent. For every tracked file it accepts only:

```text
exact committed HEAD content
or
exact generated D-148 content
```

Any third state aborts. It also checks the committed Git blob identity for every tracked target before the first write.

Applied/created repository files:

```text
mt5/experts/MentorDeterministicV1EA.mq5
mt5/experts/EdgeAuditV1.mqh

docs/ea/HANDOFF.md
docs/ea/STRATEGY_RESEARCH_STATE.md
docs/ea/BACKLOG.md
docs/ea/DECISIONS.md
docs/ea/TEST_RESULTS.md
docs/ea/D147_EXIT_ARCHITECTURE_RESEARCH.md
docs/ea/D148_ENTRY_SURVIVAL_FAILURE_TAXONOMY.md

tools/summarize_d148_entry_survival_failure_taxonomy.py
```

The D-147 document/result ledger updates only record the already-completed GOLD 2025 three-mode evidence and the future smart-partial idea; they do not change code semantics.

## D-148 taxonomy

Primary population:

```text
actual filled EXTERNAL_CONTINUATION
+
original normalized SL reached before first +1R
```

After exact SL-first, the real strategy position remains closed normally while D-148 privately observes a counterfactual path until:

```text
ORIGINAL_1R_RECOVERED_BEFORE_MAP_SUPPORT_LOSS
or
MAP_SUPPORT_NOT_SAME_AT_SL
or
MAP_SUPPORT_LOST_AFTER_SL
or
RIGHT_CENSORED_AFTER_SL
```

The original frozen PLAN-owner protected break and Root invalidation are context events, not automatic directional-failure terminals. Current H1/M30 map support is evaluated separately.

There is no post-SL time cutoff and no fitted threshold.

## Required local validation

### 1. Compile

Compile:

```text
mt5/experts/MentorDeterministicV1EA.mq5
```

Required:

```text
0 errors
```

MetaEditor is not available in the packaging environment, so this must be established locally.

### 2. Short GOLD audit OFF/ON parity

Use identical Strategy Tester settings:

```text
Symbol: GOLD
Model: Every tick based on real ticks
short fixture: e.g. 2025-01-01 through 2025-01-31

InpRegimeResearchMode = V1_REGIME_BASELINE_NO_GATE
InpStopLossModel = V1_SL_ROOT_OB_DISTAL_20
InpPositionSizingMode = V1_SIZE_FIXED_RISK_MONEY
InpFixedRiskMoneyPerTrade = 100
InpEventLogMode = V1_LOG_RESEARCH_COMPACT
InpExitManagementMode = V1_EXIT_ORIGINAL
```

Run A:

```text
InpEnableEdgeAudit = false
InpEventCsvFile = GOLD_D148_OFF.csv
```

Run B:

```text
InpEnableEdgeAudit = true
InpEventCsvFile = GOLD_D148_ON.csv
```

Compare:

```powershell
python tools\compare_unified_audit_parity.py GOLD_D148_OFF.csv GOLD_D148_ON.csv
```

Required:

```text
PARITY PASS
```

Do not interpret D-148 if non-audit strategy rows differ.

### 3. GOLD 2025 full audit ON

With the same strategy settings and `V1_EXIT_ORIGINAL`:

```text
InpEnableEdgeAudit = true
InpEventCsvFile = GOLD_2025_D148.csv
```

Then:

```powershell
python tools\summarize_d148_entry_survival_failure_taxonomy.py GOLD_2025_D148.csv
```

Required before interpretation:

```text
D148 EVENT INTEGRITY: PASS
```

The analyzer cross-checks the D-148 +1R/SL classification against the existing exact 1R runner outcome, enforces one post-SL terminal/censor per failure, checks causal timestamps and post-SL map-loss identity, and reconciles stop counters.

## Interpretation boundary

D-148 does **not** authorize:

```text
wider SL
later Entry
extra M1 confirmation
M30/PB filter
owner-turnover veto
FVG-size threshold
Root-depth threshold
regime score
```

First establish the failure taxonomy. If a large share recovers original +1R while map support remains intact, the next measurement should focus on correction completion / local reaction / SL sensitivity. If support fails before recovery, focus on directional authority/regime reliability.

The future `SMART_PARTIAL_WITH_CONTINUATION_STATE` idea is recorded only in project docs and is not implemented here.

## v2 installer correction

The original transport package had three Python patch anchors encoded with a literal `\\n` sequence instead of a real newline. The first failure surfaced as:

```text
ERROR: D148 dormant D146 arm: expected exactly one anchor, found 0
```

v2 corrects all three affected anchors together:

```text
D148 dormant D146 arm
D148 continuation-only prefill scope
D148 continuation-only runner population
```

The failure occurs while expected output is being generated, before the installer writes tracked repository files. If the original package stopped on that error, no rollback is required; run the v2 installer directly.
