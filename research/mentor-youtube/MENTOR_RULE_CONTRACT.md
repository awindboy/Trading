# Mentor Protocol Rule Contract

## Purpose

This contract is the only trading-rule source for `mentor_engine`. It is based
only on the 21 mentor videos in this directory. Legacy V5-V32 rules may supply
clock, identity, replay, and audit infrastructure, but they may not authorize a
trade.

For manual chart trading or blind replay, the controlling execution document is
[`MENTOR_STYLE_MANUAL_TRADING_MANDATE.md`](MENTOR_STYLE_MANUAL_TRADING_MANDATE.md).
Its HTF root OB and causal LTF refinement gates must be completed before M1 is
allowed to authorize a trade.

## Evidence classes

- `explicit`: the mentor states the rule or draws it unambiguously.
- `repeated`: the same relation appears in multiple videos.
- `operational`: a deterministic implementation decision required to replay the
  explicit rule. Operational rules must not be presented as mentor quotations.
- `uncertain`: the videos show more than one treatment. These cases remain
  separate named protocols and are not mixed by scoring or tuning switches.

## Core protocol

1. Aggregate closed M1 bars into H1, M30, M15, M5, and M1. A decision may
   use an object only after the candle that confirms it has closed.
   Replay must start early enough to reconstruct the H1 structure that is
   already active at the trade boundary; 2025 Q1 therefore uses 2024-10-01
   through 2024-12-31 as state warm-up, while economic counting starts on
   2025-01-01.
2. Confirm a wave when three consecutive opposite-colour candle bodies close.
   A doji belongs to neither direction and interrupts the sequence.
3. A body close through the protected structure level is BOS/CHoCH. A wick
   breach that closes back inside the level is a liquidity sweep, not a break.
4. Treat smaller waves inside the protected external range as internal
   structure and potential liquidity. Do not promote every internal break to a
   new external trend.
5. A tradable liquidity pool must explain where another participant would put
   a stop. The supported causes are an external swing, a reaction trap, a
   defended range edge, or a confirmed trendline cluster. A recent pivot alone
   is not eligible.
6. The initial scenario source is a structure-owned OB near a meaningful swing
   high or low. The two supported OB definitions remain distinct. An HTF FVG
   may describe delivery inefficiency, but it cannot independently declare a
   source POI or authorize the first position.
7. Refine the source by descending from the HTF OB through H1/M30/M15/M5. At
   least one lower-timeframe child is required. A child OB is valid only when
   it is contained by, overlaps, or is the immediately adjacent substructure
   of its parent swing and belongs to the same displacement. This causal child
   defines the source/context lineage; it does not replace the CHoCH
   displacement FVG as the base first-position entry zone.
8. The map timeframe is adaptive within H1 and M30, with H1 as the highest
   active frame. H1/M30 establish scope; H1/M30/M15/M5 reveal the nested OB family;
   M5 describes the correction context and M1 alone confirms the executable
   reaction. Stop refinement must follow the OB lineage, not an unrelated
   lower-timeframe zone at a similar price.
9. A continuation setup must occur in the correct half of its active dealing
   range: long in discount and short in premium. This is the mentor's execution
   discipline, not a universal market law.
10. The base first-entry chain is the predeclared nested OB family, source
    liquidity context, OB contact, M1 sweep, M1 body-close CHoCH, then a fresh
    same-direction 3-candle FVG belonging to the same sweep-to-CHoCH causal leg.
    M5 may validate that the M1 event belongs to the expected correction but
    cannot authorize an order. A separate continuation BOS is not mandatory.
    If the meaningful CHoCH has no such causal FVG, the structure event remains
    valid but the base first-position order is not authorized.
11. If more than one valid FVG exists in that causal displacement, select the
    widest by price range. An exact maximum-width tie after tick normalization
    is no-trade. Use the selected FVG's first subsequent touch, after both the
    FVG and meaningful CHoCH are available, as the retest. Long entry is the
    bullish FVG upper boundary; short entry is the bearish FVG lower boundary.
    OB-only first-position execution remains a separate research variant.
12. Let `width = FVG.top - FVG.bottom`. For the base first position, long SL is
    `FVG.bottom - 0.20 * width`; short SL is
    `FVG.top + 0.20 * width`. Broker spread, stops-level, and Bid/Ask handling
    remain execution-infrastructure concerns; they must not silently redefine
    this strategy geometry before that infrastructure policy is frozen.
13. Match TP to scenario scope. External continuation targets external
    liquidity; internal rotation targets the first internal liquidity or
    unfilled delivery zone before the external invalidation; confirmed external
    reversal targets new external liquidity.
14. Before fill, cancel when the entry zone is consumed, the objective is
    delivered, or the source structure is invalidated. After fill, the original
    SL and TP decide the experiment.
15. A re-entry after a completed or invalidated scenario requires a new OB,
    sweep, CHoCH, and entry-zone chain. There is no count cap, RR fallback,
    maximum R, arbitrary time exit, ATR quality filter, or weighted score.
16. In-position FVG retracement entries are a separate continuation/add-on
    protocol: the first position must already be delivering toward its frozen
    TP, and the retracement fills a newly created inefficiency. This protocol is
    documented but disabled until the base initial CHoCH-FVG method proves
    reproducible.

## Explicitly separate research variants

- CHoCH plus an additional BOS confirmation.
- H4 context or owner above the active H1 map.
- Direct M5 trigger execution without an M1 confirmation.
- In-position continuation/add-on entry at a delivery FVG retracement.
- OB-only precision entry.
- FVG inversion entry.
- Entries outside the 50% half of the active dealing range.
- Partial profit, break-even movement, and discretionary delivery management.

These variants may be replayed later as immutable protocols. They must not be
implemented as combinable optimization toggles in the base engine.

## Completion rule

Implementation parity requires every `explicit` Casebook relation to pass and
every trade to expose its map structure, source liquidity, context zone, sweep,
CHoCH, entry zone, SL, and objective. Profitability is a separate gate.
