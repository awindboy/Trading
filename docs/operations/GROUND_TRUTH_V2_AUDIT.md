# Ground Truth V2 Audit

Candidate discovery alone never creates an approved Ground Truth.

## 1. Discover

```powershell
python scripts\build_ground_truth_v2.py discover `
  --output output\ground_truth_v2_june2026_v451
```

Discovery must end in a blocked audit state. `family_ledger.jsonl` is not a
trading benchmark.

## 2. Complete Five Audits

1. `CHRONOLOGICAL`: inspect each family using only evidence available at
   `firstKnownAtUtc`.
2. `COUNTERFACTUAL_SHUFFLED`: inspect the same families in fixed shuffled order
   with independent provenance.
3. `NO_TRADE_DAILY_MTF`: inspect every UTC day, including days with no family.
   The auditor receives four as-of chart sets at 06:00, 12:00, 18:00, and
   24:00 UTC. Their paths and SHA-256 hashes are part of the audit ledger.
4. `TRIGGER_ROLE`: verify every accepted execution role against the exact
   decision-time trigger or delivery packet.
5. `STATEFUL_PLAN_SEQUENCE`: replay every PLAN decision in chronological order
   against the one persisted external-owner timeline. A family that passed the
   semantic audit but conflicts with the live owner state is rejected here.

All audit ledgers are append-only hash chains. Missing families, duplicated
executions, reused auditor identity, absent role IDs, changed packet hashes,
future candles, or post-order evidence fail closed.
`POTENTIAL_MISSED_FAMILY` also fails finalization; a non-empty explanation is
not sufficient to pass the no-trade gate.

## 3. Finalize

```powershell
python scripts\build_ground_truth_v2.py finalize `
  --output output\ground_truth_v2_june2026_v451 `
  --chronological-audit output\ground_truth_v2_june2026_v451\audits\chronological.jsonl `
  --counterfactual-audit output\ground_truth_v2_june2026_v451\audits\counterfactual.jsonl `
  --no-trade-audit output\ground_truth_v2_june2026_v451\audits\no_trade.jsonl `
  --trigger-coverage-audit output\ground_truth_v2_june2026_v451\audits\trigger_role.jsonl `
  --stateful-plan-audit output\ground_truth_v2_june2026_v451\audits\stateful_plan.jsonl `
  --chronological-plan-decisions output\ground_truth_v2_june2026_v451\codex_audits\chronological\plan_decisions.jsonl
```

The finalizer recomputes the stateful PLAN ledger rather than trusting its PASS
strings. It also enforces maximum three concurrent risk slots and forbids
opposite-direction concurrent exposure.

## 4. Invalidated Result

- Path: `output/ground_truth_v2_june2026_v451` (`INVALIDATED`)
- Status: `BLOCKED_DYNAMIC_OBJECTIVE_LIFECYCLE`
- Trades: 2
- Former result: 1 TP, 1 SL, `+0.1293013556R`
- Do not use this result for parity. See `BLOCKED_REPORT.md`; dynamic objective
  updates were omitted after the first physical-family snapshot.

The previous four-trade ledger was superseded during the final stateful audit.
Two executions were removed because their PLANs conflicted with the external
owner state that existed at their actual first-known times.

This is a protocol benchmark. It is not a profitability claim.
