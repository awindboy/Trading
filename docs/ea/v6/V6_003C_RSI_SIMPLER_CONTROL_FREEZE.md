# V6-003C RSI Simpler-Control Freeze
Date: 2026-08-29
Purpose: required recursive falsification of the already-opened RSI14 H1/H4 result; not a candidate rescue.

C2 DISP14_H1H4:
- completed H1: sign(close - close 14 H1 bars earlier)
- completed H4: sign(close - close 14 H4 bars earlier)
- same nonzero sign -> LONG/SHORT; disagree/missing -> NEUTRAL.

Rationale: preserves RSI's frozen period count (14) and H1/H4 consensus architecture while removing Wilder gain/loss transformation. If C2 explains the same result, RSI has no independent indicator edge.
No other displacement window will be tested in this child.
