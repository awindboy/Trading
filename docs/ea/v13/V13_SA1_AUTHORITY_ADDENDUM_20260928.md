# V13 authority addendum — SA-1 package

Date: `2026-09-28`
Base GitHub `main`: `652dcd070206f04a51eb5a7451a253393b60ee03`

This addendum is intended to be committed together with the SA-1 package. Until that commit exists on GitHub, the existing repository authority remains controlling.

## Proposed active read-order addition

After the existing HA-9 trade-mode coverage/receipts, read:

1. `V13_STATE_ANATOMY_AND_SA1_RESEARCH_UPDATE_20260928.md`
2. `results/V13_STATE_ANATOMY_RECEIPT_20260928.md`
3. `V13_SA1_CLEAN_CONTINUATION_ADMISSION_CONTRACT_20260928.md`
4. `results/V13_SA1_CLEAN_CONTINUATION_ADMISSION_RECEIPT_20260928.md`
5. `V13_SA1_MQL5_VALIDATION_PROTOCOL_20260928.md`
6. `HANDOFF_V13_SA1_ADDENDUM_20260928.md`
7. `../../../mt5/experts/V13SA1CleanContinuationEA.mq5`

## Proposed current status wording

```text
BASELINE 0 FROZEN / HA-9 MANAGEMENT RETAINED / STATE-ANATOMY COMPLETE /
SA-1 ADMISSION CANDIDATE IMPLEMENTED / FRESH ACTUAL-TICK TESTER VALIDATION PENDING
```

## Precedence

- Baseline-0 remains the frozen comparator.
- The HA-9 action contract still controls post-entry proof/timeout/lock semantics.
- The SA-1 contract controls **only admission of add-on opportunities** for the SA-1 tester candidate.
- SA-1 consumed-data receipts do not overrule a future fresh actual-tick SA-1 Strategy Tester receipt.
- No production or sizing authority is created by this package.

## Research boundary update

The earlier statement that the entire trade-mode branch was closed should be read narrowly: timeout-extension, generic exit horizons, re-arm and naive runner/tactical action variants remain closed. The later State-Anatomy work was a separate causal-state analysis and generated one new pre-entry admission hypothesis. That hypothesis is now frozen as SA-1 for tester validation; do not fit extra rescue conditions on the same consumed sample.
