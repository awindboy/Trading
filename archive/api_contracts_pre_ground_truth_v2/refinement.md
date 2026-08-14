# REFINEMENT contract
- Select a causal M30/M15/M5 child only after root and objective are frozen.
- A child must be on a strictly lower timeframe than its parent. The frozen root candle itself is never a child. Select childBarIds only from packet.refinementCandidates.
- A refinement path contains at most one child per timeframe and is ordered from higher timeframe to lower timeframe. Same-TF candidates compete; they are never consecutive parent/child nodes. When one unique lower-TF candidate explains the same delivery, it becomes the final child instead of retaining a wider higher-TF execution zone.
- The scenario freeze must precede the child touch. Never adopt an earlier touch retrospectively after MAP discovery.
- Child must share direction, lie inside or immediately beside the parent swing event, belong to the parent's formation time, explain the same displacement, and deliver lower-TF structure.
- Price overlap, later coincidence, an arbitrary narrow candle, or FVG overlap is not refinement.
- If children compete and causality is unclear, keep the higher child or WAIT/NO_TRADE.
- Preserve a causal child even when it has not been touched yet. The engine waits for an exact post-freeze, post-formation M1 touch; do not use an earlier touch or inspect M1 trigger before that event.
