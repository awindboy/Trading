# V9 Next Research Contract — Execution Freeze and Hidden Gate

Date: `2026-09-14`
Status: `ACTIVE NEXT CONTRACT`
Base checkpoint: `V9_CHALLENGE_EXIT_EXPOSURE_COST_RUNTIME_CHECKPOINT_20260914.md`
Base freeze candidate: `V9_MECHANICAL_POLICY_FREEZE_CANDIDATE_20260914.md`
Future-hidden: `2025-07 LOCKED`
Untouched reserve: `2021`

## Objective

Do not search for a new edge.
Freeze the exact execution contract for the already-surviving mechanical candidate and decide whether the future-hidden gate is actually satisfied.

## Required sequence

```text
1. Freeze exact research fill semantics for:
   - immediate Arrival entry;
   - CHALLENGED full exit;
   - Hard-SL execution;
   - gap-cross cases;
   - same-M1 ambiguous cases.

2. Freeze the source-range manifest and runtime/script hashes.

3. Freeze ONE_POSITION as the baseline exposure convention.
   Keep REPLACE_CHILD as a secondary research comparator only.

4. Decide how observed spread is applied in the official hidden comparator.
   Do not mine a spread threshold.

5. Re-run consumed blocks from the authoritative full-M1 byte ranges
   and require exact ledger/hash parity.

6. Produce one mechanical-policy freeze manifest containing:
   - authority docs;
   - source SHA/ranges;
   - runtime SHA;
   - policy version;
   - ledger hashes;
   - cost convention;
   - ambiguity convention.

7. Only after all above are explicitly PASS:
   review whether 2025-07 may be opened once.

8. If the hidden gate is opened:
   no parameter retuning after seeing it.
   A failure remains a failure.

9. 2021 remains untouched final reserve regardless of the 2025-07 result.
```

## Prohibited

Do not add or retune:

- Entry filters;
- SAME_NEAREST thresholds;
- fixed numeric SL;
- fixed TP;
- LTF triggers;
- cooldown/retry caps;
- trade quotas;
- duration thresholds;
- AI selection.

## Completion criterion

The contract is complete only when a single deterministic command can reproduce the frozen consumed ledgers from the authoritative source ranges and every execution/fill ambiguity is explicitly handled before hidden data is opened.
