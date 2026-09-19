# V10 Next Research Contract — R7G EA Actual-Tick Validation

Date: `2026-09-20`  
Status: `ACTIVE EXECUTION VALIDATION CONTRACT / RESEARCH ONLY`  
Market: `GOLD# ONLY`

## 1. Frozen objects

Do not retune the R4/R5/R7G core while running this contract.

Frozen decision semantics:

```text
R4 base action
-> R5 EV context
-> R7G 180-completed-H4 prior-exited feedback overlay
```

Do not add a new threshold, cooldown, no-chase rule, direction exclusion, retry count, minimum-R filter, or campaign cap simply because an actual-tick run looks better with it.

## 2. Validation order

Run in this order:

1. compile `V10R7G_ExactActualTickReplayEA.mq5`;
2. run GOLD# with `Every tick based on real ticks` over the embedded historical interval;
3. export tester trades/deals and compare entry, stop, exit, position count and PnL with the frozen action ledger;
4. compile `V10R7G_FullEmbeddedML_EA.mq5`;
5. run the same historical interval with `FIXED_LOT_PER_UNIT`, `InpLotPerUnit=0.01`;
6. compare row-level R4 weight, R5 EV sign, R7G feedback and final weight against the frozen reference;
7. only after action parity, evaluate equity-risk sizing and broker-specific money PnL;
8. preserve all discrepancies as execution/model parity evidence rather than tuning them away.

## 3. Required outputs

Persist at minimum:

- MetaEditor compile log;
- Strategy Tester report;
- deal/order export;
- EA diagnostic CSV;
- exact replay parity report;
- full embedded action parity report;
- spread/commission/slippage summary;
- maximum simultaneous Children and units;
- account-currency PnL under the exact chosen sizing setting.

## 4. Pass/fail interpretation

The exact replay EA is the execution reference. A failure there is an MT5 execution/timestamp/SL handling issue, not an ML issue.

The full embedded EA is a decision-runtime reference. A discrepancy there must be classified into:

```text
feature parity
rank-history parity
model-inference parity
prior-quarter threshold parity
R7 feedback availability parity
execution timing/fill parity
```

Do not conflate them.

## 5. Forward boundary

All data through 2026-08-28 are consumed development/replay evidence.

Do not infer a new forward training rule from the same history. The 2026-08-28+ live/future model-freeze contract must be explicitly defined before using post-cutoff data for evaluation.

`GOLD# 2021` remains sealed unless separately released under a frozen validation contract.
