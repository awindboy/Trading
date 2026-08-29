# V7 Backlog

Status: `ACTIVE`

## Immediate — V7-003 blinded contextual replication

- [ ] Build a new untouched Double-B event catalog.
- [ ] Freeze selection before outcomes.
- [ ] Include GOLD plus independent-factor market(s).
- [ ] Produce H1 future-hidden chart packets.
- [ ] Show only causally known context.
- [ ] Freeze broker/server session mapping for KTR.
- [ ] Record decision card for every event.
- [ ] Save/hash decisions before future reveal.
- [ ] Reveal future only after full batch lock.
- [ ] Score BASIC/BREAKOUT/TURNING/WAIT classification.
- [ ] Report Entry timing errors separately from direction errors.
- [ ] Report SL placement errors separately from target errors.
- [ ] Report staged-entry contribution and risk amplification separately.

## Decision-card fields

- event id
- market
- event close time
- Double-B side
- ENTER_NOW / WAIT_CONFIRM / SKIP
- LONG / SHORT / NONE
- BASIC / BREAKOUT / TURNING / UNKNOWN
- candle evidence
- MA evidence
- S/R evidence
- trendline evidence or UNKNOWN
- Bollinger separation/extension evidence
- session opening-candle high/low behavior
- current session KTR
- KTR relative context
- structural invalidation
- SL price
- SL/KTR
- realistic target room
- TP price
- TP/KTR
- staged entry yes/no
- add interval
- max legs
- confidence
- uncertainty note

## Secondary research

- [ ] Formalize confirmation logic for WAIT_CONFIRM without outcome reuse.
- [ ] Study whether fresh/terminal expansion can be represented reproducibly.
- [ ] Compare AI visual decisions with user/manual decisions if both can be locked independently.
- [ ] Study campaign-risk caps only after equal-risk-per-leg behavior is understood.
- [ ] Add commission/slippage after a causal decision process exists.

## Deferred

- V7 EA implementation.
- production sizing.
- live/paper deployment.
- portfolio interaction.
- automatic trendline algorithm.
- machine-learning classifier.

## Permanently consumed

- 24 V7-002 reverse-engineered events.
- all event-specific hindsight SL/TP choices in that ledger.
