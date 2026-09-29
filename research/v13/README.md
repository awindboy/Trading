# V13 research code

## Current 2026-09-29 boundary

The active LTF evidence is Reconstruction A of the route q75/q50 state machine
documented in `docs/ea/v13/V13_LTF_ROUTE_Q75_Q50_ACTION_CONTRACT_20260929.md`.
The interrupted session did not save its exact final q50 ledger, so its reported
economics remain distinct.

`v13_ltf_route_q75_q50_policy.py` now regenerates Reconstruction A, including
strict-prior OOF route admission, q50 repair, Child-#1 reference and frozen
policy ledgers. `validate_v13_policy_ledger.py` checks ledger invariants;
`parse_v13_policy_replay_journal.py` establishes ordered actual-tick parity and
derives per-event economics, blocks and tail robustness.

Reconstruction A passed 2,954/2,954 action parity but was not promoted because
its better payoff/net came with worse loss frequency and ordinary exposure than
SA-1. Do not present older hurdle/staged ledgers as this candidate and do not
rescue it with post-hoc ranks or sizing.

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

## HA-9 trade-mode phase 1

`ha9_trade_mode_phase1.py` reconstructs an actual MT5 report into Child-level
trades and joins it to the ideal HA-9, integrated-state and raw-swing ledgers.
It uses post-exit price only as a label to study the 4–8h timeout-loss and
sub-4h winner populations.

```powershell
python research/v13/ha9_trade_mode_phase1.py `
  --report '<path-to-ReportTester-318585216.xlsx>' `
  --m1 'data/GOLD#/GOLD#_M1_202201030100_202609222358.csv' `
  --h1 'data/GOLD#/GOLD#_H1_202201030100_202609222300.csv' `
  --h4 'data/GOLD#/GOLD#_H4_202201030000_202609230000.csv' `
  --ideal-ledger 'output/v13_ha9_proof_lock_20260928/child_ledger.csv' `
  --integrated-features 'output/v13_ha4c_integrated_20260927/decision_features.csv' `
  --raw-swing-features 'output/v13_ha5_raw_swing_20260927/decision_features.csv' `
  --output 'output/v13_ha9_trade_mode_phase1_20260928'
```

Read `docs/ea/v13/results/V13_HA9_TRADE_MODE_PHASE1_RECEIPT_20260928.md`
before interpreting its future-only recovery or continuation labels.

`ha9_counterfactual_exit_matrix.py` keeps actual entries fixed and compares
opposite H1, FAST-R25 H4, standard H4 and a natural one-H1 timeout extension.
`ha9_timeout_extension_holdout.py` applies the frozen extension mechanisms to
the short post-cutoff overlap between the supplied report and raw H1 data.

```powershell
python research/v13/ha9_counterfactual_exit_matrix.py `
  --trade-ledger 'output/v13_ha9_trade_mode_phase1_20260928/trade_mode_ledger.csv' `
  --h1 'data/GOLD#/GOLD#_H1_202201030100_202609222300.csv' `
  --h4 'data/GOLD#/GOLD#_H4_202201030000_202609230000.csv' `
  --output 'output/v13_ha9_counterfactual_exit_matrix_20260928'

python research/v13/ha9_timeout_extension_holdout.py `
  --report '<path-to-ReportTester-318585216.xlsx>' `
  --m1 'data/GOLD#/GOLD#_M1_202201030100_202609222358.csv' `
  --h1 'data/GOLD#/GOLD#_H1_202201030100_202609222300.csv' `
  --h4 'data/GOLD#/GOLD#_H4_202201030000_202609230000.csv' `
  --output 'output/v13_ha9_timeout_extension_holdout_20260928'
```

`ha9_information_rearm_audit.py` tests whether a failed tactical Child should
block later actual C2..C10 opportunities until a new causal information event.
It is a selection diagnostic; it does not synthesize replacement opportunities
beyond C10.

```powershell
python research/v13/ha9_information_rearm_audit.py `
  --trade-ledger 'output/v13_ha9_trade_mode_phase1_20260928/trade_mode_ledger.csv' `
  --output 'output/v13_ha9_information_rearm_20260928'
```

`ha9_runner_tactical_audit.py` designates a runner only after an actual proof
timestamp and compares FAST/standard H4 retention with and without suppressing
later actual tactical opportunities.

```powershell
python research/v13/ha9_runner_tactical_audit.py `
  --exit-ledger 'output/v13_ha9_counterfactual_exit_matrix_20260928/counterfactual_exit_ledger.csv' `
  --output 'output/v13_ha9_runner_tactical_20260928'
```
