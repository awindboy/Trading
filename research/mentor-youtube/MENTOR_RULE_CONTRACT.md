# Mentor Protocol Rule Contract

## Purpose

This contract preserves the mentor-video research evidence and causal principles
used by `mentor_engine`. It is based only on the 21 mentor videos in this
directory. Legacy V5-V32 rules may supply clock, identity, replay, and audit
infrastructure, but they may not authorize a current V1 trade.

For the current deterministic EA V1, the controlling strategy authority is
the repository-root `AGENTS.md`, with `docs/ea/EA_SPEC.md` as its deterministic
specification. This research contract preserves mentor-video evidence and causal
principles. `MENTOR_STYLE_MANUAL_TRADING_MANDATE.md` is a historical
manual-trading snapshot unless explicitly brought back into sync with current V1
authority.

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
   The dated 2024-10 warm-up example above is a historical research fixture.
   Current deterministic EA V1 initialization follows the hierarchical,
   compressed bootstrap contract in `docs/ea/EA_SPEC.md` Section 11.14.
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
7. Predeclare an eligible, unconsumed HTF Root OB first and wait for price to
   actually contact that Root. The HTF Root remains the sole OB strategy source.
   Lower-timeframe child discovery, if used for audit/context, begins only after
   this contact. A child that existed before Root contact, including one inside
   the original displacement that created the Root, cannot be relabeled as a
   current post-contact child. No child is required for first-position trigger
   authorization.
8. The map timeframe is adaptive within H1 and M30, with H1 as the highest
   active frame. H1/M30 establish scope; H1/M30/M15 identify and retain the
   pre-existing HTF Root. After actual Root contact, M30/M15/M5 may record
   optional newly formed child observations. M5 describes correction context and
   M1 confirms the executable reaction after a valid Root-reaction sweep. Child
   observations never replace the Root or change Entry/SL/TP/cancellation.
9. A continuation setup must occur in the correct half of its active dealing
   range: long in discount and short in premium. This is the mentor's execution
   discipline, not a universal market law.
10. The base first-entry chain is the predeclared eligible HTF Root, actual HTF
    Root contact, valid Root-reaction liquidity/sweep context, M1 body-close
    CHoCH, and a fresh same-direction 3-candle FVG belonging to the same
    sweep-to-CHoCH causal leg.
    M5 may validate that the M1 event belongs to the expected correction but
    cannot authorize an order. A separate continuation BOS is not mandatory.
    If the meaningful CHoCH has no such causal FVG, the structure event remains
    valid but the base first-position order is not authorized.

    Current deterministic operational contract (D-127) separates detector and
    scenario sequence. The M1 sweep detector applies physical penetration +
    same-bar recovery to active liquidity already known at M1 bar open, without
    Root intersection, scenario ownership, child, distance, age, or quality
    filters. Scenario direction is applied only when checking the ordered chain:
    `Root contact -> later direction-compatible detected Sweep -> later
    same-direction detected M1 CHoCH`. The Root-contact bar itself is excluded
    from satisfying the scenario Sweep stage because closed OHLC cannot prove
    intrabar contact-before-sweep ordering. The existing M1 structure detector
    remains CHoCH authority; the scenario does not add a sweep-time protected
    reference gate.

    This paragraph is an **operational** deterministic replay decision, not a
    mentor quotation. Child availability is not a sweep/CHoCH anchor.
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
13. Match TP to the active V1 scenario scope. Current first-position order
    scopes are `EXTERNAL_CONTINUATION` and `EXTERNAL_REVERSAL`.
    Ordinary counter-H1 `INTERNAL_ROTATION` is not an active V1 order scope;
    opposite LTF structure remains correction context until HTF reversal
    permission opens. Freeze the causally-known, unconsumed, direction-ahead,
    scope-compatible liquidity family before Entry/SL geometry is known, then
    use the nearest candidate with planned R >= 1 after Entry/SL are available.
14. Before FVG selection, an already-available causal FVG that is retested after
    its availability and before the meaningful CHoCH close is not fresh enough
    for the base first-position candidate set. At CHoCH close, select the widest
    eligible FVG, calculate Entry/SL/TP, and submit the pending order immediately.
    Once the pending order is normally registered at the FVG near-side boundary,
    later FVG mitigation or distal traversal is not a separate strategy
    cancellation rule. Before fill, cancel only when the selected objective is
    delivered, required HTF Root/source authority is invalidated, or the scenario's
    direction authority is revoked. Broker submission/fill/cancellation failures
    are execution-infrastructure outcomes, not new strategy states.
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
  This does not include current V1's `LONG_HORIZON_LIQUIDITY_INDEX`,
  which stores H4 external liquidity only and grants no H4 map/owner authority.
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
every trade to expose its map structure, source liquidity, pre-existing HTF Root,
qualifying Root contact, optional child audit if any, sweep, CHoCH, entry zone, SL,
and objective. Profitability is a separate gate.
