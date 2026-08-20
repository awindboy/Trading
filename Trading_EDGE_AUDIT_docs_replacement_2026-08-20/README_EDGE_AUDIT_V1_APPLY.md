# Apply EDGE_AUDIT_V1 1.92R1L4

Target GitHub main checked:

```text
260d14e714bbd635448d466d12d848b9ef80ba39
```

## 1. Extract this package into the repository root

It adds/replaces:

```text
mt5/experts/EdgeAuditV1.mqh
tools/apply_edge_audit_v1.py
tools/compare_edge_audit_parity.py
docs/ea/EDGE_AUDIT_V1.md
docs/ea/HANDOFF.md
docs/ea/BACKLOG.md
docs/ea/STRATEGY_RESEARCH_STATE.md
docs/ea/BASE_EDGE_AUDIT_2025.md
```

## 2. Apply the exact EA + DECISIONS transformation

From repository root:

```powershell
python tools/apply_edge_audit_v1.py
```

or:

```powershell
py tools/apply_edge_audit_v1.py
```

The patcher verifies the exact Git `HEAD:<path>` blob identities and requires both target files to be locally clean before editing:

```text
EA = 33912d32d5861b1d2ccb7e77a9f6a09446db41ac
DECISIONS = 834ccb6929ead8a3729df14a2c547ed5a07920dc
```

Mismatch means abort. Do not force-apply.

The script creates the complete modified local EA and DECISIONS files, wires `EdgeAuditV1.mqh`, changes build identity to `1.92R1L4`, and appends D-141/D-142 to `DECISIONS.md`.

## 3. Compile before push

Compile:

```text
mt5/experts/MentorDeterministicV1EA.mq5
```

Required: `0 errors`.

## 4. First parity smoke

```text
GOLD
2025-01-01 ~ 2025-01-31
Every tick based on real ticks
BASELINE_NO_REGIME_GATE
FIXED_RISK_MONEY = 100
ROOT_OB_DISTAL_20
```

Run twice:

```text
A. InpEnableEdgeAudit = false
B. InpEnableEdgeAudit = true
```

Use different main event CSV filenames. B additionally writes `InpEdgeAuditCsvFile`.

Compare the two **main** event ledgers locally:

```powershell
python tools/compare_edge_audit_parity.py <OFF_MAIN.csv> <ON_MAIN.csv>
```

Required result:

```text
PARITY PASS
```

Then send:
- MetaEditor compile result
- OFF main event CSV
- ON main event CSV
- ON edge-audit CSV

Do not treat D-142A as validated until OFF/ON main-strategy parity passes. D-142B exact fill virtual barriers remain deferred.
