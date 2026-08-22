# D-152 Results Documentation Update

This package records the completed D-152 GOLD25/BTCUSD25 SP V3 matrix and updates project state.

**No EA/source strategy code is modified.**

Expected repository HEAD before application:

```text
7cb26133235c45a3756492af951900f15213f8cb
```

## Apply

From the Trading repository root:

```powershell
python .\Trading_D152_RESULTS_DOC_UPDATE\tools\apply_d152_results_docs.py
```

The installer fails closed if the expected Git HEAD or any documentation blob it edits has changed.

## Updated / created

```text
docs/ea/v2/D152_SP_V3_RESULTS.md              NEW
docs/ea/v2/HANDOFF_V2.md                     REPLACE
docs/ea/v2/RESEARCH_STATE_V2.md              REPLACE
docs/ea/v2/BACKLOG_V2.md                     REPLACE
docs/ea/v2/D153_MT5_BATCH_AUTOMATION.md      REPLACE

docs/ea/HANDOFF.md                            safe in-place current-state update
docs/ea/STRATEGY_RESEARCH_STATE.md            safe in-place current-state update
docs/ea/BACKLOG.md                            append D-152 completion block
docs/ea/DECISIONS.md                          append D-152 decision
docs/ea/TEST_RESULTS.md                       append D-152 batch result
```

## Frozen interpretation

```text
V3E BANK_2R_LOCK_ONE = provisional SP reference
not baseline authority
V3A/V3B/V3C/V3D demoted for now
additional same-sample SP tuning paused
next primary bottleneck = Fill -> +1R Entry survival
```
