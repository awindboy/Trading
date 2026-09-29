# V13 result receipts

Current status (`2026-09-29`): Baseline 0 remains frozen and SA-1 remains the
ordinary-quality actual-tick reference. LTF-route Reconstruction A has a frozen
ledger and exact actual-tick parity, but is not promoted because stronger payoff
and net came with worse loss frequency, win rate, streak and exposure.

## Current receipt

- `V13_LTF_ROUTE_Q75_Q50_RESEARCH_RECEIPT_20260929.md` — full result/decision
  summary for the final LTF destination branch, including explicit separation
  of saved evidence, session-reported numbers and remaining parity work.
- `V13_LTF_ROUTE_POLICY_REPLAY_EA_COMPILE_RECEIPT_20260929.md` — replay EA
  source/EX5 hashes and zero-error/zero-warning MetaEditor compile evidence.
- `V13_LTF_ROUTE_Q75_Q50_ACTUAL_TICK_REPLAY_RECEIPT_20260929.md` — Reconstruction
  A ledger identity, 2,954/2,954 Journal parity, actual-tick economics, blocks,
  tail robustness, closed-market retry evidence and non-promotion decision.

## Historical HA-9 receipts

- `V13_HA9_ADDON_PROOF_LOCK_RECEIPT_20260928.md` — causal M1/H4 action audit.
  Primary result: losses `2,427 -> 1,685`, non-flat win rate `37.08% -> 56.07%`,
  trade-sequence DD `3,756.99 -> 1,283.65` while total net falls to `+3,946.06`.
- `V13_HA9_TRADE_MODE_PHASE1_RECEIPT_20260928.md` — actual MT5 Child-ledger
  reconstruction and observational decomposition of the 4–8h timeout-loss pile
  and sub-4h winners. It changes no action rule.
- `V13_HA9_COUNTERFACTUAL_EXIT_MATRIX_RECEIPT_20260928.md` — fixed-entry H1,
  FAST-H4 and standard-H4 exits plus a one-H1 timeout extension. The extension
  looked favorable on consumed data but failed the short post-cutoff
  quasi-holdout and is rejected.
- `V13_HA9_INFORMATION_REARM_RECEIPT_20260928.md` — failed-Child re-entry gates
  based on extreme, raw swing, H1 path and delta information. All variants
  removed at least as many winners as losses and the narrow two-failure version
  failed the post-cutoff check.
- `V13_HA9_RUNNER_TACTICAL_ROLE_RECEIPT_20260928.md` — first/rolling proven
  runner conversion and suppression of new add-ons while a runner lives. Net
  can rise through right tails, but losing Children and streak burden increase;
  the H1-acceptance version also failed post-cutoff.

## Historical receipts

Existing HA-0..HA-8A, X1 and X2 receipts remain historical evidence. Their
right-tail diagnostics are still factual, but the current evaluation priority is
controlled by `../V13_OBJECTIVE_AND_EVALUATION_UPDATE_20260928.md`.

Do not reinterpret an old exploratory receipt as authority for a new action.
