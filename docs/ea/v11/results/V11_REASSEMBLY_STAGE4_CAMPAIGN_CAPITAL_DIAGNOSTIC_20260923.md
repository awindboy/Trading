# V11 reassembly stage-4 campaign-capital diagnostic

Date: `2026-09-23`

Status: `ONE-SLOT ARCHITECTURE REJECTED / CONSUMED DEVELOPMENT EVIDENCE / NO TRADE, RELEASE, SIZING, LEVERAGE, EA, EXECUTION, OR PRODUCTION AUTHORITY`

Interpretation note: the later Stage-5 request-level audit supersedes any inference that lower absolute R alone rejects this structure. The decisive finding is that the slot blocked `550` requests with only `5.27%` stop incidence and `+243.02R`, so it removed safer profitable mature-run capital rather than selectively identifying rotation.

## Question

Can V10 be fundamentally reassembled so every selected Child receives one participation unit while the extra two-unit conviction capital belongs to the FAST journey rather than being recreated independently at every selected HA?

The mechanism gives one shared two-unit slot to each `rid`. When the slot is occupied, later extra-capital requests are blocked but their one-unit Child still participates. Two causal same-decision conventions were compared: the surviving k1 continuation receives priority, or the independent new Child receives priority.

## Complete portfolio frontier

| Policy | Stopped units | 3-unit full stops | Combined R | R retention | Max gross units | Equal-DD ending equity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| original full R7G | 486 | 127 | +741.01R | 100% | 48 | 204.82x |
| k1 ladder, unlimited later allocations | 390 | 79 | +682.15R | 92.06% | 48 | 211.25x |
| every Child one unit only | 232 | 0 | +284.37R | 38.38% | 16 | 136.08x |
| one journey slot, k1 priority | 320 | 44 | +421.71R | 56.91% | 18 | 147.13x |
| one journey slot, new-Child priority | 332 | 50 | +439.13R | 59.26% | 18 | 153.10x |

Both one-slot policies keep all `1,649` Children and all `232` Hard-SL Children. They materially reduce stopped units, full-size stops, and peak gross exposure. They also delete too much scalable right-tail capital: `970` extra-capital requests exist, only `420` are funded, and `550` are blocked by an occupied slot.

Changing priority does not repair the architecture. New-Child priority is less destructive than k1 priority, but its equal-drawdown ending equity remains below original R7G and the simpler k1-ladder comparator.

## Decision

A fixed single conviction slot per journey is rejected. It proves that campaign-level ownership can directly control repeated full-size losses and peak exposure, but it is too coarse: it treats all simultaneous persistent-run opportunities as redundant even when repeated deployment is what monetizes the right tail.

The retained design problem is therefore not `one slot versus unlimited slots`. It is an **elastic capital inventory** problem:

1. every selected Child keeps one-unit participation;
2. additional capital is not recreated automatically for every HA;
3. the journey may earn, retain, transfer, or retire extra inventory causally;
4. release evidence must improve on both boundaries: unlimited k2+ pyramiding and the rejected one-slot cap;
5. stop count, stopped units, right-tail R, concurrent exposure, direction symmetry, and equal-drawdown performance must be judged together.

No existing R5 head, STD/SLOW state, Wave coordinate, liquidity label, or fixed waiting time currently grants that inventory authority.

## Reproduction

- script: `research/v11/analyze_v11_reassembly_stage4_campaign_capital.py`;
- ignored output: `output/v11_reassembly_stage4_20260923/`;
- summary SHA-256: `9c3ead157dcb435f9c717807b2becb694266e1f2fc02230e2d53eae77e4a8a0e`;
- allocation ledger SHA-256: `a93ed1c6a6d75d2604bed43bfa73c1e89129270a7945d27ecc00ea96a9e53e96`;
- tranche ledger SHA-256: `7033c3d83e5002c2d1249ee101ca995a12908f55f368d029d71b7eb6477e3fad`.
