# REFINEMENT contract - Ground Truth V2

- `AGENTS.md` is the sole strategy authority.
- Select only supplied lower-timeframe OB IDs that share direction, formation episode, price event, displacement, and actual lower-timeframe body structure delivery with the parent.
- Price overlap, FVG overlap, a later coincidental candle, or choosing the narrowest candle is not causality.
- Preserve every distinct causal lane. If one execution event has multiple unresolved lineages, return `UNRESOLVED_LINEAGE`; do not choose one by score or recency.
- The refinement must be known before its first touch. Do not inspect M1 trigger evidence in this phase.
