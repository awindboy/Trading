# MAP contract - Ground Truth V2

- `AGENTS.md` is the sole strategy authority. Use only closed H1/M30/M15/M5 evidence and supplied family IDs.
- Review every family ID in the page. Return one verdict for every input family ID; omission, addition, or duplicate ID invalidates the entire page.
- Freeze owner, scope, dealing range, root OB, causal refinement path, and the engine-supplied ordered objective family. Do not invent a price or reorder family members.
- EXTERNAL_CONTINUATION uses unconsumed H1/M30 external liquidity. INTERNAL_ROTATION uses meaningful M15-or-higher liquidity inside the dealing range. EXTERNAL_REVERSAL requires the recorded H1/M30 protected-swing body break and new owner.
- A root OB is the last opposite-colour cause candle whose displacement body-delivered structure near a meaningful swing. HTF FVG, overlap alone, nearest candle, and a consumed zone are not root sources.
- A child must explain the same physical displacement lineage. If distinct lineages remain unresolved, reject with `UNRESOLVED_LINEAGE`.
- M1 evidence is unavailable and cannot be a PLAN reason. Do not return entry, SL, TP, state, time, or schedule.
