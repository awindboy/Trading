# V10 Research Guardrails

Date: `2026-09-16`
Status: `ACTIVE / RESEARCH DISCIPLINE`

## 1. Causality

At a decision timestamp, use only information finalized and known by that timestamp.

Future run length may define a research answer sheet but may never enter the live feature vector.

An accidental future reveal contaminates the interval. Do not repair the result by inserting hindsight trades.

## 2. Child death is final

If a Child hits its own structural Hard SL, it is dead.

Do not:
- resurrect it after later price recovery;
- re-price the stop after the fact;
- replace the stopped result with the later campaign exit.

## 3. Separate representation from policy

A representation can have high AUC without being a good trading policy.

Always separate:

```text
state / probability quality
from
entry / sizing / exit economics
```

Report both.

## 4. Separate Oracle-likeness from economic quality

Current evidence shows that:

```text
P(EARLY / RUNWAY)
```

and

```text
P(positive Child economics)
```

are different questions.

Do not assume a high early-run probability is automatically the highest-expectancy entry.

## 5. No threshold laundering

Values found from consumed-data scans remain research diagnostics.

This includes, but is not limited to:

- `m=2`, `m=3`, `m=4`, ... runway labels;
- probability quartiles;
- `0/0/1/3` maps;
- `0.01 / 0.02 / 0.03` ladders;
- any HA `(w, alpha)` pair;
- any AUC-selected feature family.

## 6. Exposure accounting

Every candidate report should include where applicable:

- raw PnL;
- PF;
- closed-sequence DD;
- structural-R;
- total lot-units;
- weighted position-hours;
- maximum single order size;
- maximum concurrent exposure units;
- right-tail concentration.

A raw PnL gain obtained only by multiplying exposure is not sufficient evidence.

## 7. Selection stability

At minimum preserve:

```text
2025 <- prior 2024
2026 <- prior 2024-2025
```

when a prior-only test is claimed.

If the feature family or rule is itself chosen from the same test years, label it as consumed-data / post-hoc.

## 8. Multi-timeframe rules

LTF bars must be completed before they contribute to state.

Do not use the unfinished tail of the current M15/M30/H1 bar.

Prefer semantically interpretable coordinates over a large feature soup.

## 9. Execution fidelity

Current V10 H1-stop research uses M1 first-touch screening.

That is stronger than H1-close screening, but it is **not yet a V10 actual-tick execution validation**.

Do not report V10 as actual-tick validated until a dedicated V10 executable replay is completed.

## 10. Promotion

Do not promote from a few examples or one high-AUC scan.

A promoted candidate must survive:
- fixed semantics;
- chronological selection controls;
- route-level bootstrap / regret;
- both directions;
- exposure/risk concentration review;
- actual-tick validation;
- forward-demo evidence.
