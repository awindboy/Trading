# D-145 mixed-state recovery

Target GitHub `main` checked: `72c0d4c35affaaa671407188dc5c18fb41550a96` (`docs: middle save`).

This package repairs the mixed D-145 state discovered after the intermediate commit. It **does not modify strategy semantics**.

It verifies that `EdgeAuditV1.mqh` is already D-145 `1.92R1L7`, then synchronizes:

- EA research build/phase identity to `1.92R1L7 / RUNNER_MARKET_CONTEXT_AUDIT_V1_LIGHTWEIGHT`;
- HANDOFF / BACKLOG / STRATEGY_RESEARCH_STATE / EDGE_AUDIT_V1 / BASE_EDGE_AUDIT_2025;
- missing D-144 and D-145 decision records;
- D-144 GOLD exact-tick result and D-145 transition in TEST_RESULTS.

## Apply

Extract anywhere **inside the Trading repository**, or extract directly into the repository root. The installer no longer assumes its own parent folder is the Git root.

From any directory inside the Trading repository:

```powershell
python tools/apply_d145_recovery.py
```

If you extracted the ZIP into a subfolder instead, run the script by that path while your terminal is anywhere inside the Trading repo, for example:

```powershell
python .\Trading_D145_RECOVERY\tools\apply_d145_recovery.py
```

The script searches for the Git root, requires exact HEAD `72c0d4c35affaaa671407188dc5c18fb41550a96`, and aborts on local edits to every target tracked file.

## Validate

Compile `mt5/experts/MentorDeterministicV1EA.mq5` in MetaEditor. Required: `0 errors`.

Then GOLD 2025-01 smoke with identical settings:

```text
Every tick based on real ticks
BASELINE_NO_REGIME_GATE
FIXED_RISK_MONEY = 100
ROOT_OB_DISTAL_20
```

Run OFF and ON with separate `InpEventCsvFile` names and use `tools/compare_unified_audit_parity.py`. Required: `PARITY PASS`.

After parity, compare D-145 wall-clock runtime with D-144. Then run GOLD 2025 full-year Audit ON for runner-context analysis.
