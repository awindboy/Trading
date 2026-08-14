# PLAN contract - Ground Truth V2

- `AGENTS.md` is the sole strategy authority. Generic ICT/SMC, V32, scores, oracle output, move indexes, hindsight, and trade outcomes cannot authorize a scenario.
- The request is paged without deleting candidates. Return exactly one verdict for every supplied family ID. Missing, extra, or duplicate family IDs invalidate the whole page.
- For each family independently judge owner/scope, dealing range and PD half, root displacement causality, complete refinement causality, source freshness, and objective-family classification.
- The ordered objective family is engine evidence. Do not select a final TP, alter prices, reorder members, or prefer a farther level for larger R. The engine chooses the first still-live member with planned R at least 1 after Entry and hard SL exist.
- At most the two nearest unconsumed historical H1 levels from 2023-12-01 onward may be carried as inactive fallback evidence. Historical M30-or-lower levels are forbidden. The engine may activate historical H1 only when no current member remains eligible after Entry and hard SL geometry; the model must never prefer it for distance or larger R.
- INTERNAL_ROTATION stays inside the range and uses meaningful M15-or-higher liquidity. EXTERNAL_CONTINUATION preserves H1/M30 external objectives and records nearer levels as intermediate delivery.
- PLAN cannot inspect M1, create an order, or return prices, timestamps, state, schedule, watch events, entry, SL, or TP.
- Approve every defensible independent family. Do not suppress a family merely because another accepted watch lane exists; risk capacity is an engine responsibility.
