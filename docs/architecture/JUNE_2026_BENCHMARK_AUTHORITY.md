# June 2026 Benchmark Authority

- Strategy authority: `AGENTS.md`
- Current benchmark status: `BLOCKED`
- Invalidated artifact: `output/ground_truth_v2_june2026_v451`

The former two-trade June benchmark is not authoritative. A valid runtime
scenario using `M30:1780534800 -> M5:1780536900 -> M15:1780542000` became
knowable at `2026-06-04T03:45:00Z`, but the frozen candidate ledger did not
record it because that physical family had already been seen once.

The opposite naive correction is also invalid: rebuilding every still-live
physical family whenever any new objective matures produced 3,825 snapshots
from 125 physical families. Those snapshots are not independent trade
opportunities.

The next authoritative benchmark must use a stateful lifecycle:

1. Freeze one PLAN from evidence knowable at that time.
2. Keep it unchanged until objective consumption, source invalidation, owner
   change, through-delivery, completed TP/SL, or another contractual terminal.
3. Only after terminal may the same physical source be mapped to a newly mature
   objective.
4. Audit all accepted executions and daily no-trade intervals independently.

Until those gates pass, Gemini comparisons may be used to diagnose the
pipeline, but not to claim parity, profitability, or Ground Truth completion.
