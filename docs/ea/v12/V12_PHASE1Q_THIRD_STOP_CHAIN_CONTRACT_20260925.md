# V12 Phase 1Q — third-and-later stop-chain contract

Status: **frozen before evaluation / consumed-development only**  
Frozen: `2026-09-25`

Phase 1P removes roughly one third of repeat stops but does not always reduce
the rare maximum chain. Phase 1Q directly studies the user's stronger target:
after two causally completed consecutive stopped `k=1` candidates, can the
third or later stopped candidate be identified?

H2, H1, M30, and M15 are all included so no clock is selected after Phase-1P
results. The same ten fixed model ablations and train-only top-risk quintile are
used. Only candidates whose known prior stop streak is at least two can be
excluded; every other candidate remains unchanged.

Success requires repeat-risk improvement, at least 30% pooled and 15% per-fold
third-plus-stop removal, at least 90% overall participation, at least 95%
pooled and 90% per-fold tail-R retention, a pooled maximum-stop-streak reduction
without fold deterioration, and preserved equal-stop-budget economics.

This is not a cooldown or permission to skip every third attempt. All evidence
is consumed and grants no trade or sizing authority.
