# D-143 FRONT-END CAUSAL AUDIT — apply/test

Target GitHub state checked before packaging:

```text
repo: awindboy/Trading
commit: 418471c7a0c9bc9e45bb075f43e1d726daef4ebf
EA Git blob: 3c6abf7434c389a133615ef40101caace1a7c504
EdgeAuditV1.mqh Git blob: 149020c4f989da18a71699c05610a636db7310ca
```

The package is fail-closed. It refuses to patch if the checked EA/include/docs have moved or have local uncommitted edits.

## Apply

Extract this ZIP into the repository root, then run:

```powershell
python tools/apply_front_end_causal_audit.py
```

or:

```powershell
py tools/apply_front_end_causal_audit.py
```

On success the transport-only `payload/` directory deletes itself.

Compile:

```text
mt5/experts/MentorDeterministicV1EA.mq5
```

Required: `0 errors`.

## What changed

Research build/phase:

```text
1.92R1L5
FRONT_END_CAUSAL_AUDIT_V1_UNIFIED_LEDGER
```

Strategy semantics remain D134 execution core unchanged.

D-143 adds shadow checkpoints for:

```text
H1/M30 INITIAL_BOS
H1/M30 continuation BOS
H1/M30 PROTECTED_BREAK
hourly MAP
all H1/M30/M15 ROOT_CREATED
PLAN
all physical Root contacts including NO_PREPLAN
preplanned ROOT_CONTACT
SWEEP
CHOCH
FVG
ACTUAL_FILL identity
```

It records direction-owner age/refresh, Root ordinal/age, PLAN ordinal and Root/PLAN/contact timing so the direction → Root relationship can be studied from the beginning.

## One CSV only

There is no `InpEdgeAuditCsvFile` anymore.

Everything goes to:

```text
InpEventCsvFile
```

Research-only rows use:

```text
EDGE_AUDIT_*
```

So each Strategy Tester run produces one event CSV.

## Required parity smoke

Use identical settings twice on GOLD 2025-01-01 through 2025-01-31:

```text
Every tick based on real ticks
BASELINE_NO_REGIME_GATE
FIXED_RISK_MONEY = 100
ROOT_OB_DISTAL_20
```

Run A:

```text
InpEnableEdgeAudit = false
InpEventCsvFile = GOLD_D143_OFF.csv
```

Run B:

```text
InpEnableEdgeAudit = true
InpEventCsvFile = GOLD_D143_ON.csv
```

Then:

```powershell
python tools/compare_unified_audit_parity.py GOLD_D143_OFF.csv GOLD_D143_ON.csv
python tools/summarize_front_end_audit.py GOLD_D143_ON.csv
```

Required:

```text
PARITY PASS
AUDIT STRUCTURE CHECK PASS
```

The parity script removes only `EDGE_AUDIT_*` rows, then requires every remaining CSV row to match exactly.

## After parity

Run audit ON for 2025 on:

```text
BTCUSD
CADJPY
GBPCAD
GOLD
SILVER
USDJPY
```

Use one unique event filename per symbol. Only **six CSV files total** are needed.

Send those six unified CSVs back for analysis.

## Current research boundary

Do not change strategy rules from this build. In particular D-143 does not add:

```text
owner-age cutoff
Root-count cutoff
SHORT veto
RR cutoff
PD veto
CHOCH-reference gate
exact-fill virtual exits
```

Those are deferred until the front-end direction/Root audit is interpreted. `2021` remains untouched.
