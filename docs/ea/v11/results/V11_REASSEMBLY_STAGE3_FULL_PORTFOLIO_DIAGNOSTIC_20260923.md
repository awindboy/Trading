# V11 reassembly stage-3 full-portfolio diagnostic

Date: `2026-09-23`

Status: `RETAINED MECHANISM COMPARATOR / CONSUMED DEVELOPMENT EVIDENCE / NO TRADE, RELEASE, SIZING, LEVERAGE, EA, EXECUTION, OR PRODUCTION AUTHORITY`

## Question

Does Stage 2's k1 capital ladder remain useful after all `1,649` resolved selected R7G Children, independently selected k2+ Children, and concurrent exposure are restored?

The event export contains `1,650` selected rows. The terminal `2026-08-28 20:00` SHORT k1 has no resolved causal outcome before the source ends, so the economic replay uses the `1,649` resolved Children. It preserves every resolved selected Child. Only k1 allocation changes: one unit participates immediately and the remaining two units may release at the causal FAST-k2 continuation event. All k2+ R7G allocations remain frozen.

## Full-portfolio result

| Metric | Original full R7G | k1 ladder + unchanged k2+ |
| --- | ---: | ---: |
| selected Children | 1,649 | 1,649 |
| Hard-SL Children | 232 | 232 |
| conventional win rate | 38.51% | 38.45% |
| stopped loss-units | 486 | 390 |
| three-unit full stops | 127 | 79 |
| funded units | 3,881 | 3,589 |
| combined R-units | +741.01R | +682.15R |
| combined-R retention | 100% | 92.06% |
| 1%-unit max drawdown | 44.59% | 42.47% |
| equal-drawdown ending equity | 204.82x | 211.25x |
| max concurrent gross units, close-first | 48 | 48 |
| calendar mean gross units | 4.88 | 4.53 |

The full portfolio keeps considerably more R than the k1-only Stage-2 view suggested. Stopped loss-units fall `19.75%`, three-unit full stops fall `37.80%`, and funded units fall only `7.52%`. The result is directionally consistent by year for stopped-unit reduction; combined R changed from `34.85 -> 38.67R` in 2024, `460.33 -> 409.06R` in 2025, and `245.83 -> 234.43R` in partial 2026.

The descriptive equal-drawdown advantage is small, not transformative. SHORT remains structurally weak and worsens from `-26.74R` to `-30.36R`; LONG changes from `+767.75R` to `+712.51R`.

## Overlap audit

Among `246` valid k1 FAST-k2 top-ups:

- `134` coincide with an independently selected k2 Child;
- `99` of those k2 Children have a three-unit R7G allocation;
- `35` have a one-unit allocation;
- `3` are recorded `ORDER_FAIL` events.

This overlap does not create a higher peak than frozen R7G because the original policy already kept the fully funded k1 Child open while adding k2. It does show why k1-only accounting is incomplete: later independent Child allocations dominate the portfolio peak, which remains `48` gross units.

## Decision

The k1 capital ladder survives full-portfolio arithmetic as a retained mechanism comparator. It does not solve first-unit stop frequency, SHORT weakness, or campaign-level peak exposure. Its apparent Stage-2 scalability gain contracts sharply once the rest of R7G is restored.

The next reassembly layer must decide whether additional capital belongs to each Child independently or to the journey as shared inventory. That question must preserve one-unit participation and the persistent-run right tail; it cannot be answered by deleting k2+ Children.

## Interpretation boundary

`ORDER_FAIL` and `EXIT_PENDING_BLOCK` rows retain their frozen intended-strategy outcomes because market-closure execution repair is deferred to later EA work. The compounding path is a cost-free realization-order diagnostic; spread, slippage, margin, exact concurrent fractional sizing, and live execution are absent.

## Reproduction

- script: `research/v11/analyze_v11_reassembly_stage3_portfolio.py`;
- ignored output: `output/v11_reassembly_stage3_20260923/`;
- summary SHA-256: `55237f52601ee09b548708d9d0ebc09749008c6f0a31a2cc00ed69a4de96e685`;
- child ledger SHA-256: `cfee70fa0985f5b4eac4b04357a0add5795b745ba3d95ba7be56ebd7d648c4c6`;
- tranche ledger SHA-256: `ae78e5d0338244b906ef9d4ca3e9613f12e645fb078bed27af3cafd3032308d3`.
