# Phase 1W: failed-seed location diagnostic

Frozen before Phase-1W cross-tabs, 2026-09-26. Consumed development only.
V10 comparator diagnostic, not a CRT candidate generator or V12 trading rule.

Question: do repeated entry losses occur disproportionately inside a prior
failed seed's price footprint? No ML, fitted threshold, cooldown or new exit.

Sources: Phase 1V's hash-locked 1I/1K/1U inputs; Phase 1G child context with
event status; Phase 1U's verified raw M1 ending August 2026. Rebuild original
universe by streaming M1 and capture completed signal-H4 OHLC at decision.
Never open 2021 or post-consumed-cutoff history.

Unit: first actual entry of each existing funded FAST run, NOT a proven market
Journey. Later Children remain unchanged and separately reported. Previous
means immediate prior funded episode, not a hindsight-selected previous loser.
Previous first Child must have exited strictly BEFORE the current decision;
equal timestamps remain unavailable to avoid same-minute order assumptions.
Its R must be negative, whether from Hard SL or NHA exit.

Two predeclared, equally reported exclusion diagnostics:

1. H4_FOOTPRINT: current completed H4 close lies inside the inclusive high/low
   of the previous failed seed's completed signal H4 candle.
2. RISK_FOOTPRINT: same close lies inside the inclusive prior entry/Hard-SL band.

Record outside-in-current-direction versus outside-opposed, direction changes,
raw prices, interval overlap, and signed displacement / causal H4 ATR180.
No outcome field of the current episode may enter these records. Attach its
outcomes in a separate ledger after decisions are fixed. Missing/unresolved
references keep the episode. Shadow observes original attempts even if masked.

Report all episodes, not a tail-excluded pass gate: wins/losses, first stops,
seed-only unweighted R, original weighted episode R, profits removed per losses
removed, event-time realized-R drawdown, year/side splits and participation.
Tail counts distinguish any unweighted Child R>=5 from weighted Child R>=5.
Drawdown uses grouped original Child exit timestamps, not episode start dates;
it is not mark-to-market or monetary broker equity. Costs/weights are inherited;
no fill, spread, fee, feedback-refit or executable-policy claim is made.

No 90% tail-retention requirement, positive non-tail slope requirement, or
post-hoc winning condition is introduced. Both diagnostics may fail. No
statistical independence, future validation, causal treatment effect or sizing
authority follows from repeatability. Byte-identical reruns are reproducibility,
not independent validation.
