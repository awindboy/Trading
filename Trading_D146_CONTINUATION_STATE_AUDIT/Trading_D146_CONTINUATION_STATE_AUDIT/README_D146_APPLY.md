# D-146 CONTINUATION STATE AUDIT — apply / validate

Target repository state checked before packaging:

```text
repo: awindboy/Trading
branch authority: main
Git HEAD: f0a9be86d7d8af4e22b21e9b657669aae1245fbd
commit: docs: hand off D145 runner research to D146
```

This package prepares research build:

```text
1.92R1L8 / CONTINUATION_STATE_AUDIT_V1_SHADOW
strategy semantics = D134_EXECUTION_CORE_UNCHANGED
strategy authority = NONE
2021 = KEEP UNTOUCHED
```

D-146 does **not** change Entry, SL, TP, scenario authorization, position sizing, order lifecycle, map/structure authority, or exposure rules. Measurement logic is contained in `mt5/experts/EdgeAuditV1.mqh`; `MentorDeterministicV1EA.mq5` changes only its diagnostic description and `EA_START` research build/phase identity.

## Apply

The installer is fail-closed. It requires the exact Git HEAD and exact committed blob identities listed in `STATIC_QA.txt`, and refuses to run when any target file has local edits.

Recommended: extract the ZIP as a subfolder anywhere inside the Trading repository, then from any PowerShell location inside that repository run:

```powershell
python .\Trading_D146_CONTINUATION_STATE_AUDIT\tools\apply_d146_continuation_state_audit.py
```

If your Python launcher is `py`:

```powershell
py .\Trading_D146_CONTINUATION_STATE_AUDIT\tools\apply_d146_continuation_state_audit.py
```

After a successful apply, the repository receives/updates:

```text
mt5/experts/MentorDeterministicV1EA.mq5     diagnostic identity only
mt5/experts/EdgeAuditV1.mqh                 D-146 shadow measurement

docs/ea/HANDOFF.md
docs/ea/D146_CONTINUATION_STATE_AUDIT.md
docs/ea/STRATEGY_RESEARCH_STATE.md
docs/ea/BACKLOG.md
docs/ea/DECISIONS.md

tools/summarize_d146_continuation_state_audit.py
```

The extracted transport folder itself can be deleted after successful application.

## What D-146 measures

Population:

```text
actual filled EXTERNAL_CONTINUATION trade
+
first exact +1R reached before normalized SL
```

Observation window:

```text
T0 = first exact +1R touch
T1 = first exact +2R touch OR normalized-SL touch
```

At T0 it freezes the causally available M30 owner / protected / external / protected-to-external range state. The T0 external retains an immutable identity. Later M30 externals are recorded only as later causal refreshes and are never backfilled into the T0 snapshot.

Between T0 and T1 it observes:

```text
same-direction M30 INITIAL_BOS / BOS
outward external refresh
PROTECTED_BREAK
opposite directional event
existing-owner change/loss
scenario-direction trend loss
exact-tick delivery of the original T0 external
post-1R MFE / MAE
```

Rows remain in the existing unified event ledger:

```text
EDGE_AUDIT_D146_1R_STATE
EDGE_AUDIT_D146_M30_EVENT
EDGE_AUDIT_D146_ORIGINAL_EXTERNAL_DELIVERED
EDGE_AUDIT_D146_TERMINAL
EDGE_AUDIT_D146_CENSORED
```

No fitted progress threshold or strategy score is introduced.

## Required local validation

### 1. MetaEditor compile

Compile:

```text
mt5/experts/MentorDeterministicV1EA.mq5
```

Required:

```text
0 errors
```

This package was statically checked, but MetaEditor is not available in the packaging environment, so compile success must be established locally before testing.

### 2. GOLD short audit OFF/ON parity

Use identical settings for both runs. Recommended smoke fixture:

```text
Symbol: GOLD
Period: 2025-01-01 through 2025-01-31
Model: Every tick based on real ticks
InpRegimeResearchMode: V1_REGIME_BASELINE_NO_GATE
InpStopLossModel: V1_SL_ROOT_OB_DISTAL_20
InpPositionSizingMode: V1_SIZE_FIXED_RISK_MONEY
InpFixedRiskMoneyPerTrade: 100
InpEventLogMode: V1_LOG_RESEARCH_COMPACT
```

Run A:

```text
InpEnableEdgeAudit = false
InpEventCsvFile = GOLD_D146_OFF.csv
```

Run B:

```text
InpEnableEdgeAudit = true
InpEventCsvFile = GOLD_D146_ON.csv
```

Then run:

```powershell
python tools\compare_unified_audit_parity.py GOLD_D146_OFF.csv GOLD_D146_ON.csv
```

Required:

```text
PARITY PASS
```

Parity means that after removing `EDGE_AUDIT_*` rows, all remaining strategy/event rows match exactly. Any difference invalidates D-146 evidence.

### 3. GOLD 2025 full-year Audit ON

After parity, run GOLD 2025 with the same strategy settings and Audit ON. Use a unique event filename, then run:

```powershell
python tools\summarize_d146_continuation_state_audit.py <GOLD_2025_D146_LEDGER.csv>
```

Required before interpretation:

```text
D146 EVENT INTEGRITY: PASS
```

The validator checks, among other things:

- one D-146 T0 snapshot per armed runner;
- exactly one terminal or right-censor state;
- no M30 event timestamp before T0;
- terminal outcome consistency with the existing exact 2R runner label;
- event-counter consistency;
- original-external-delivery row consistency;
- `EDGE_AUDIT_STOP` row-count consistency.

### 4. Development panel only after integrity

As needed:

```text
GOLD 2023
GOLD 2024
GOLD 2025
BTCUSD 2025
SILVER 2025
CADJPY 2025
```

Analyze relationship direction by market and LONG/SHORT. Do not optimize a pooled M30-progress threshold.

`2021` remains untouched.

## Interpretation boundary

D-146 is evidence collection only. Even a strong result does not authorize:

```text
fixed 1R TP
fixed 2R TP
progress < X hold
progress > X close
remaining-room threshold
M30 maturity Entry veto
runner score
LONG/SHORT-specific threshold
```

A strategy variant is considered only after post-+1R causal M30 state transitions survive the development panel and are documented as a plausible mechanism.
