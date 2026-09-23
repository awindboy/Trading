# V12 research state

Last synchronized: `2026-09-24`

## Status

`PHASE 1C COMPLETE AND REPRODUCIBLE / BROAD CARRY REJECTED / NO TRADE AUTHORITY`

## Established inputs

- The supplied local timeframe files are now provenance-locked. The full M1
  SHA-256 is
  `fd6b1c886519b544b00dfdcf0ee390970e29c54bb3bf7530c3bd1ef52aa47250`;
  the consumed causal prefix SHA-256 is
  `04e074ca77f449f02ac65a0b11f8efcb06254272be1a99b7273db8876ec4c939`.
- Raw-M1 reconstruction matched the supplied M5, M15, M30, H1, H4, D1, and W1
  exports exactly in coverage, OHLC, tick volume, and volume.

- The supplied 28-page Korean CRT guide is a secondary synthesis of public Romeo
  material. Its SHA-256 is
  `16426b4f1ac3bac12c444d54c103b38760e1e1eb854dff1306467b906b1b6384`.
- The source grammar is broader than a three-candle picture: context, location,
  timing, trigger, target, and reevaluation matter.
- Every candle can be treated as a range. C1 defines a range, C2 tests/sweeps an
  extreme, and C3 is potential distribution/delivery only after causal evidence.
- A sweep followed by a close back inside and an accepted close outside are
  distinct branches.
- Beginner execution belongs after C2 closes. Predicting C2 while it forms is not
  the Phase-0 V12 task.
- The guide explicitly retains Monthly->Daily, Weekly->H4, and Daily->H1 examples.
  V12 initially uses W1->H4 and D1->H1 because they connect to the existing H4
  research without inventing a source claim.
- C1 50% is the first structural destination; the opposite extreme or older
  liquidity is a later destination. Target logic is separate from entry and risk.
- SMT is context/confirmation, not a standalone entry.

## Inherited evidence

- V10 proved that low-noise H4 HA participation can produce a large right tail,
  but broad stop classifiers, next-HA prediction, generic regime labels, fixed
  MA bands, and binary selective funding failed economic conversion.
- FAST/STD/SLOW HA remain useful phase sensors; none is market truth. Whole-base
  STD substitution reduced color churn but increased actual Hard-SL burden.
- Wave Candle compresses completed M5 settlement inside H4 and remains a valid
  observation instrument, but static Wave geometry did not establish a trading
  gate on consumed evidence.
- V11 Stage 0-5 were principally capital diagnostics bound to the V10 R7G ledger.
  They did not constitute a new strategy skeleton.
- A genuinely ledger-independent V11 STD/SLOW-memory skeleton reduced descriptive
  stop rate but failed side/year robustness. Its progress ladder reduced full-size
  stop clusters by staging size, not by recognizing stop candidates.

## Current V12 decisions

- CRT creates candidates; HA/Wave/ML do not.
- The first baseline is mechanical and has no ML.
- All continuous geometry is recorded both in raw price and causal volatility-
  normalized units to compare liquidity eras.
- Decision and outcome records are separated.
- Python raw-M1 replay is the numeric oracle. MQL5 must reproduce the event ledger
  before Strategy Tester P/L is accepted.
- Real ticks are required for economic evidence whenever intrabar ordering can
  change SL/target outcomes. Faster tester modes are smoke tests only.
- Market-closed order failures are execution states, not strategy losses; their
  lifecycle repair remains deferred to the EA implementation phase.
- Phase-0 timestamps are offset-free MT5 broker labels. UTC conversion is
  forbidden until the broker timezone/DST history is independently verified.
- Strict point-rounded C1 extreme breach creates the C2 state; equality is a
  touch, not a breach.
- Phase 1B extends H4->M5 only as a V12 shadow lane, not a Romeo claim.
- External key levels are causal completed H4/day/week/month highs and lows with
  one-use consumption lifecycles. Current opens and CRT targets remain separate
  reference types; no weighted key-level score exists.
- One canonical CRT journey may be reinforced by same-direction activations,
  replaced by an opposite activation, or ended by completed-H4 structural
  failure. Milestones do not end it automatically and no timeout is used.
- Frozen V10 Children and FAST flips are overlays. Phase 1B cannot alter their
  admission, exit, or size.
- Phase 1C may alter the exit clock only in counterfactual output. It preserves
  every entry, unit, and frozen Hard SL and grants no carry or repair action.

## Closed Phase-0 result

- `1,459` exhaustive parent records: `1,215` D1->H1 and `244` W1->H4.
- `1,105` directional structural hypotheses; no Child or entry authorization.
- One same-M1 dual-extreme ordering ambiguity is preserved.
- Two independent builds produced identical hashes for all ten output files.
- This is observation and reproducibility evidence only. It says nothing yet
  about stops, R, profit, or superiority to V10.

## Closed Phase-1A result

- Contract `v12-phase1a-model1-v2` mechanically implements the rejection branch
  only: C3-open control and relative-thick Model #1 confirmation, with C2-extreme
  and trigger-structure Hard-SL variants.
- The retained final pack has `1,217` family/risk decisions, `426` filled
  variant records, separate decision/outcome ledgers, and zero post-cutoff price
  rows parsed. Two independent builds produced all ten files byte-identically.
- Full consumed-history T1 results were:
  - C3-open/C2-SL: 213 fills, 41.78% stops, `-1.12R`, PF `0.99`;
  - Model #1/C2-SL: 156 fills, 31.41% stops, `+11.68R`, PF `1.21`;
  - Model #1/trigger-SL: 57 fills, 38.60% stops, `+2.89R`, PF `1.13`.
- In the V10-matched window, trigger-SL showed `+8.84R`, PF `2.26`, and a
  two-stop maximum streak, but this came from only 26 fills. Its stopped-unit
  rate was `26.92` per 100 versus V10's `12.52`–`14.07`, and its full-history
  annual R was negative in 2022 and 2023.
- Confirmation blocked 13 stops and 5 targets over full history, but delayed
  entry reduced common-fill R by `17.21R`. The trigger-stop guard was selective
  in the recent matched window but removed net-positive capital and reduced
  common-fill R over full history.
- The first prototype therefore fails the V10 replacement gate. It remains a
  no-ML mechanism baseline, not an entry, sizing, EA, or trade rule.

## Closed Phase-1A interpretations

Do not promote or revive these by tuning consumed outcomes:

- relative-thick Model #1 confirmation plus C2-extreme SL as a robust V10
  replacement;
- the trigger-candle SL guard as a stable stop classifier;
- the recent 26-fill trigger-SL slice as evidence of scalable superiority;
- fewer absolute stops caused primarily by `84%` no execution as sufficient
  evidence that bad trades were recognized;
- Phase-1A realized-terminal drawdown as V10 portfolio drawdown parity.

## Closed Phase-1B result

- Contract `v12-phase1b-h4m5-journey-v1.1` built `7,287` H4 decisions,
  `4,819` activations, `2,649` canonical journeys, `17,610` one-use levels, and
  `2,234` FAST flips from chronological raw M1.
- Two independent complete packs were byte-identical and passed validation;
  zero post-cutoff rows were parsed.
- The unchanged selected R7G overlay preserved all `1,649` Children, `3,881`
  funded units, `486` stopped units, and `+741.010865R`.
- Aligned active-journey Children had `10.43` stopped units per 100 funded;
  opposed Children had `20.79`. Opposed Children still retained `+195.72R` and
  large positive right-tail capital, so relation cannot be a veto.
- Linked new-direction k1 after a FAST flip stopped `26.12%` when an opposite
  CRT journey was authorized versus `36.93%` in all other states. This ordering
  held in every consumed year. The non-authorized group still earned `+35.42R`.
- When the old journey remained active, linked new-direction k1 stopped
  `42.86%`. A same-direction key arrival reduced the pooled rate only from
  `46.94%` to `40.91%` and was not stable enough to become a rule.
- Phase 1B therefore establishes a useful distinction between Child
  interruption and independent opposite authorization. It does not establish
  an entry filter, permanent rejection, delay duration, sizing map, or profit
  oracle.

## Closed Phase-1B interpretations

Do not promote these from consumed evidence:

- blocking every V10 Child opposed to the active CRT journey;
- blocking every new-direction k1 without opposite CRT authorization;
- treating one external key arrival as proof of reversal or continuation;
- funding later aligned Children more heavily solely because their pooled stop
  burden is lower;
- describing the H4->M5 empirical lane as a Romeo rule.

## Closed Phase-1C result

- Contract `v12-phase1c-crt-protected-carry-repair-v1` tested selected V10
  Children whose ordinary FAST-NHA exit occurred while the same aligned CRT
  Parent remained active.
- `118` Children across `60` bridges qualified for broad carry; `31` bridges
  repaired to the original FAST direction before Parent end.
- Broad carry raised net R by `23.19R`, but added 26 stops, 66 stopped units,
  `5.6%` funded unit-hours, and `5.49R` grouped realized drawdown. Removing its
  best bridge changes the delta to `-13.75R`; 2026 was `-40.18R` versus baseline.
- Requiring the origin C1 opposite edge to remain unresolved changed 12 Children
  and added `17.01R`, but one episode supplied `85.8%` of the gain and 2025 was
  negative versus baseline.
- The 31 repair Children earned `+5.12R` versus `+4.70R` under their ordinary k1
  exit clock. Twenty-six were already selected by R7G; only five were incremental
  candidates. Average entry improved in only five cases.
- Two complete output packs were byte-identical, passed validation, and parsed
  zero post-cutoff price rows.

## Closed Phase-1C interpretations

Do not promote or tune on consumed outcomes:

- holding every aligned Child whenever the Phase-1B Parent is active;
- using the 12-Child unfinished-origin-target slice as a carry rule;
- adding capital at every PHA repair;
- claiming PHA repair reliably improves average entry;
- choosing a new liquidity family or target distance from Phase-1C outcomes.

## Next hypotheses

These are questions, not rules:

1. Can a causal ordered target inventory distinguish an unfinished Journey from
   a still-active boundary whose original objectives are already consumed?
2. After that target state is frozen, can `neutral bridge / later repair`
   preserve right-tail exposure without the broad carry's added stop burden?
3. Conditional on the five frozen FAST-flip meanings, do FAST/STD/SLOW
   disagreement and Wave settlement add information beyond CRT geometry?
4. Can separate competing-risk heads rank immediate stop, later repair, and
   right-tail continuation without collapsing them into one negative-R label?
5. Does first/later aligned status remain useful conviction information outside
   consumed history and without a fixed capital ladder?
6. Does the answer remain stable across lane, side, year, and normalized
   liquidity era?

## Evidence boundary

- All GOLD# observations through `2026-09-18 23:57` are consumed.
- GOLD# 2021 remains sealed.
- Phase 1A is a consumed-history structural-R backtest. Phase 1B is a
  consumed-history journey/transition diagnostic. Phase 1C is a consumed-history
  holding-clock and repair diagnostic. No V12 EA, MQL5 parity, actual-tick
  economics, or independent future validation exists yet.
- The post-`2026-09-18 23:57` prices in the supplied files remain unread by the
  official builder and reserved for a later frozen shadow.
