# V13 research code

V13 historical audit scripts remain observation/action evidence for their named
contracts. The current action audit is:

`ha9_addon_proof_lock_audit.py`

It reconstructs frozen Baseline 0 from raw H4, checks canonical structural
parity, then uses raw M1 only to evaluate Child #2..#10 proof/lock/timeout
management.

Example from repository root:

```powershell
python research/v13/ha9_addon_proof_lock_audit.py `
  --h4 'data/GOLD#/GOLD#_H4_202201030000_202608282000.csv' `
  --m1 'data/GOLD#/GOLD#_M1_202201030100_202608282357.csv' `
  --output 'output/v13_ha9_proof_lock_20260928'
```

Expected Baseline parity before interpreting HA-9:

```text
965 closed Journeys
3,858 closed Children
+8,147.11 idealized GOLD price points
```

The audit writes:

- `child_ledger.csv` — Child-level baseline/action outcomes;
- `summary.json` — loss count, win rate, PF/net, chronological DD, loss streak,
  year slices, trade-block quality and Top-N profitable-Journey trimming.

The Python audit is not an official MT5 backtest. Actual-tick execution authority
belongs to the Strategy Tester after event parity.
