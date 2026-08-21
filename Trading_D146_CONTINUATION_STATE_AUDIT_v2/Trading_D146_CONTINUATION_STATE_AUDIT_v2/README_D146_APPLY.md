# D-146 Continuation State Audit — v2 recovery installer

Base Git HEAD: `f0a9be86d7d8af4e22b21e9b657669aae1245fbd`
Target research build: `1.92R1L8 / CONTINUATION_STATE_AUDIT_V1_SHADOW`
Strategy authority: **NONE**

## Why v2 exists

The first D-146 installer rejected any modified target file on re-run. If an earlier run had already written one or more exact D-146 files and then stopped later, the second run could not recover from that valid partial state.

v2 is fail-closed **and** idempotent for exact D-146 partial states. Before writing anything it reconstructs the exact expected D-146 output from the committed GitHub HEAD and accepts each target only when the working file is either:

1. exact GitHub HEAD baseline, or
2. exact D-146 generated output.

Any third state remains rejected as an unexpected local edit.

## Apply / recover

From the Trading repository root:

```powershell
python .\Trading_D146_CONTINUATION_STATE_AUDIT_v2\tools\apply_d146_continuation_state_audit.py
```

If you extracted the package elsewhere, use the actual path to the script. The script discovers the Git repository automatically.

A successful recovery prints a preflight classification such as:

```text
D146_ALREADY_APPLIED mt5/experts/MentorDeterministicV1EA.mq5
BASELINE             mt5/experts/EdgeAuditV1.mqh
...
```

and then finishes all targets at the exact D-146 state.

## After application

1. Compile `mt5/experts/MentorDeterministicV1EA.mq5` in MetaEditor: require `0 errors`.
2. Run the same short GOLD fixture with `InpEnableEdgeAudit=false` and `true`.
3. Compare ledgers:

```powershell
python tools\compare_unified_audit_parity.py GOLD_D146_OFF.csv GOLD_D146_ON.csv
```

Require `PARITY PASS` after stripping `EDGE_AUDIT_*` rows.

4. Then run GOLD 2025 full-year Audit ON.
5. Validate D-146 events:

```powershell
python tools\summarize_d146_continuation_state_audit.py <GOLD_2025_D146_LEDGER.csv>
```

Require `D146 EVENT INTEGRITY: PASS` before using the research evidence.

`2021` remains untouched.
