# V10 R7G EA Implementation Checkpoint — 2026-09-20

Date: `2026-09-20`  
Status: `EA SOURCE IMPLEMENTATION COMPLETE / RESEARCH-TESTER ONLY / ACTUAL-TICK VALIDATION PENDING`  
Market: `GOLD# ONLY`  
Base GitHub `main`: `ac001391c377341a0f9fa3513d02672c061060d3` (`update V10 ML`)

## 1. Scope of this checkpoint

This checkpoint records the research and implementation work completed after the 2026-09-17 R7G sizing checkpoint.

The main objective was not to retune R7G. It was to turn the already-consumed R4/R5/R7G research into a reproducible executable MT5 research artifact while preserving the causal contract.

Frozen research chain:

```text
raw M1
-> causal H4/M15/M30/H1 state
-> R4 base participation / 0-1-3 sizing
-> R5 STOP + conditional-R EV
-> R7G recent realized-feedback overlay
-> Child execution / Hard SL
-> first opposite FAST H4 HA campaign exit
```

No future run length, future Child outcome, future HA state, post-stop resurrection, hidden cooldown, no-chase rule, minimum-R rule, forced direction balance, or post-hoc `no-k3p-SHORT` exclusion was added.

## 2. Raw-M1 universe reproduction

The official GOLD M1 source used by the R3/R4/R5/R7 research was reprocessed from raw M1.

```text
source rows                    1,648,545
source SHA256                  626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2
causal opportunity rows        6,770
resolved FAST runs             2,139
2022 / 2023 / 2024 / 2025 / 2026
                               1320 / 1488 / 1496 / 1486 / 980
```

The feature clock remains one chronological raw-M1 pass with completed bars only. Future answer-sheet fields are attached only after FAST-run resolution.

## 3. R4 reproduction

R4 preprocessing/model specialization was recovered from commit `aa7685b9e243ddff058f0dbcdb8e416260b41244`.

The final model pipeline keeps stage x direction specialization:

```text
k1 LONG
k1 SHORT
k2 LONG
k2 SHORT
k3+ LONG
k3+ SHORT
```

with the previously selected LightGBM / XGBoost / CatBoost families, preprocessing family, recency treatment, feature pruning, and distributional score head.

Final action parity against the frozen R7 research population:

```text
rows compared      2,840
matched actions    2,840
mismatches             0
```

The R4 `0 / 1 / 3` action uses the prior-quarter, same-stage x direction score distribution and its q50/q75 references. No same-quarter future distribution is used.

## 4. R5 reproduction

R5 retains the hurdle interpretation:

```text
P(STOP)
+
E[R | non-stop]

EV = -P(STOP) + (1-P(STOP)) * E[R | non-stop]
```

Native Python reproduction on the R7G-relevant 1-unit population:

```text
rows                    926
EV max abs error         2.22e-16
EV > 0 Boolean match     926 / 926
```

This confirms that the original research pipeline itself is reproducible.

## 5. R7G runtime state reproduction

Frozen R7G semantics remain:

```text
current R4 weight == 1
AND current R5 EV > 0
AND mean realized R of prior eligible, already-exited Children
    over the latest 180 completed H4 indices > 0
-> 1 unit -> 3 units

otherwise preserve R4
```

Availability rule:

```text
prior Child exit_time < current decision_time
```

Lifecycle for committed-risk accounting:

```text
[entry_time, exit_time)
CLOSE before OPEN at an identical timestamp
```

Runtime reconstruction parity:

```text
feedback rows compared      926 / 926
max feedback abs error      2.22e-16
final sizing rows          2840 / 2840
weight mismatches             0
```

## 6. M1-verified economics retained

The existing M1 audit remains the economic reference for the consumed historical sample.

| Policy | Units | Structural R | PF_R | DD_R | Raw GOLD price-PnL | Spread-adjusted price-PnL |
|---|---:|---:|---:|---:|---:|---:|
| R4 | 3,095 | +485.07R | 1.583 | 50.32R | +23,234.65 | +22,590.76 |
| R7G | 3,881 | +741.01R | 1.682 | 59.71R | **+30,883.72** | **+30,074.67** |

R7G active Child count is 1,649. The frozen historical Child win/loss count is 635 / 1,014, or 38.51% Child win rate.

R7G changes exposure, not the underlying selected Child set; its edge is primarily larger participation in persistent right-tail FAST runs rather than a high win-rate effect.

The raw price-PnL column is GOLD price movement multiplied by research units. Under the fixed interpretation `1 unit = 0.01 lot` and a 100 oz/lot GOLD contract, this maps numerically to account USD before broker-specific cost differences. Exact live account money still depends on the broker contract specification and execution.

## 7. Risk / concurrency state

Explicit committed-risk reconstruction preserved the known maxima:

```text
R4    max simultaneous units = 40
R7G   max simultaneous units = 48
```

No campaign cap is promoted from consumed data.

The full EA therefore exposes sizing as a runtime mode rather than silently promoting one account-risk percentage:

```text
FIXED_LOT_PER_UNIT
-> default 0.01 lot per unit

EQUITY_RISK_PER_UNIT
-> lot derived from account equity, Child stop distance, broker value and OrderCalcProfit()
```

The equity-risk mode rounds volume downward to the broker volume step. `InpRiskPctPerUnit` remains a tester/user input, not strategy authority.

## 8. Final feature registry and frozen model artifacts

The final embedded implementation registry is:

```text
38 raw causal features
33 engineered features
13 stage x direction causal-rank features
-------------------------------------------
84 total model feature coordinates
```

The earlier intermediate `73 feature` count is superseded by this final implementation registry.

Frozen historical model snapshots:

```text
R4 selected-score models          18
R5 STOP models                    18
R5 conditional-R models           18
------------------------------------
Total                             54
```

Snapshots cover causal historical replay for model years 2024-2026.

## 9. EA implementation status

### 9.1 Exact frozen historical replay EA — complete

File:

`mt5/experts/V10R7G_ExactActualTickReplayEA.mq5`

Purpose:

- executable actual-tick reference for the frozen historical action ledger;
- 1,649 embedded active Child actions;
- historical interval beginning 2024-10-01 through the 2026-08-28 cutoff;
- default `1 unit = 0.01 lot`, therefore 3-unit actions use 0.03 lot;
- no external CSV/model file required;
- each Child keeps its embedded Hard SL;
- frozen reference exit timing is embedded for execution comparison.

This EA is the cleanest execution-fidelity reference because it does not depend on re-generating the ML decision online.

SHA256:

`1efa21a96c000b53c7b72d1769ad56dddb30bf5280d2c2d817fbed6a243aff59`

### 9.2 Full embedded R4/R5/R7G ML EA — source implementation complete

File:

`mt5/experts/V10R7G_FullEmbeddedML_EA.mq5`

Purpose:

- chart-native causal feature reconstruction;
- 360-opportunity stage x direction prior-rank history;
- embedded 54 historical tree-model snapshots;
- R4 score + prior q50/q75 action;
- R5 STOP / conditional-R EV;
- R7G prior-exited 180-H4 feedback state;
- persistent FAST-opposite campaign `EXIT_PENDING` behavior;
- fixed-lot-per-unit and equity-risk-per-unit sizing modes;
- no Python/model runtime dependency.

Default tester window in the source is the frozen historical replay window:

```text
InpTradeFrom  = 2024-10-01
InpTradeUntil = 2026-08-29
```

SHA256:

`419d41992979034567954e1e57e7cc78b9d842661b9ddda395e8c84bea7ff710`

## 10. Remaining validation boundary

`EA source implementation complete` does **not** mean `production authority` or `final actual-tick validation complete`.

The current environment does not provide MetaEditor/terminal compilation and MT5 Strategy Tester execution. Therefore the next external validation is:

```text
MetaEditor compile
-> exact replay EA actual-tick run
-> fill/stop/exit parity audit
-> full embedded EA actual-tick run
-> decision/action parity against frozen reference
-> broker-cost/account-money audit
```

There is also one implementation-level model-export caveat to retain explicitly:

```text
native Python R5 EV sign parity on R7 population: 926 / 926
current generic tree-export snapshot after conversion correction: 925 / 926
```

The full embedded EA is therefore source-complete but remains a validation candidate until this last exported-inference discrepancy and MetaEditor/Strategy-Tester behavior are checked. Do not hide or retune around the single mismatch on consumed data.

The exact replay EA remains the execution benchmark while this final inference-parity item is audited.

## 11. Current authority conclusion

Supported:

```text
R4/R5 native research pipeline is reproducible.
R7G causal feedback/action state is reproducible.
Raw-M1 economic audit is reproduced and retained.
Exact frozen replay EA is implemented.
Full embedded R4/R5/R7G EA source is implemented.
```

Not promoted:

```text
R7G as production strategy authority
180 H4 as permanent live threshold
1% risk/unit
any campaign risk cap
post-hoc no-k3p-SHORT
2021 reserve use
2026-08-28+ live model-training rule
```

The immediate task is no longer another consumed-data model scan. It is **MT5 compile + actual-tick execution parity of the completed EA artifacts**, then future-only shadow evidence with the research rule frozen before observation.
