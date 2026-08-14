# TRIGGER contract
- Preconditions: frozen objective/scope/root/child/invalidation and actual refined-OB touch.
- Required chain after touch: liquidity existed before the final excursion; at least one completed reaction made it a live stop pool; later price sweeps it and recovers; M1 body close breaks the live swing governing the correction; that displacement owns an execution OB.
- As soon as the execution OB exists and its first retest has not happened, return ORDER with all five barIds. ORDER means place a pending limit now; the local engine waits for and fills the first later retest. Never WAIT merely because the retest is still in the future.
- WAIT is allowed only while a required event through execution-OB formation is genuinely incomplete. If the first retest already passed before the decision, reject the stale trigger rather than placing it retrospectively.
- Reject a wick break, same-leg newborn high/low, micro pivot, M1-only bounce against M5 delivery, stale trigger, passed retest, or through-delivery that crosses entry and invalidation together.
- Initial entry is the directional proximal boundary of the final causal execution OB. FVG only confirms displacement and cannot replace missing root/child.
- SL must be outside execution/child distal, protected swing, confirmed sweep extreme, and actual scenario invalidation. Buffer is at least actual spread, broker stops level, and one tick; short SL includes Ask spread.
- TP is the frozen objective wick. No RR fallback, R cap, time exit, breakeven move, partial exit, or TP extension.
