# V12 research state

Last synchronized: `2026-09-26`

## Status

`PHASE 1W RETRY-LOCATION DIAGNOSTIC / ACCOUNTING QUALIFIED / NO TRADE AUTHORITY`

Current interpretation: see the Phase-1W result. Historical Phase-1V claims of
ordinary equity drift refer to ex-post tail-excluded attribution and +/-1 count
curves, not an unconditional expectancy finding or actual equity. Its 57 tail
episodes use weighted Child R>=5 (14 episodes meet unweighted Child R>=5).
Its 48 positive-start/negative-end episodes are included in the 338 no-first-SL
negative episodes. Actual ENTRY is 1,409; another 240 selected rows did not fill.

The Phase-1W fixed H4 footprint saves 54 negative episodes for 15 lost positives,
but raises win rate only 0.82 percentage points and does not shorten the maximum
negative-episode streak. Price-location duplication remains a modest diagnostic,
not an authorized gate. Waiting for a new attempt would require its own replay.

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
- Phase 1D joins a frozen MT5 economic-calendar snapshot to the broker-label M1
  clock. Scheduled metadata and realized surprise remain physically separate;
  no time/event field may invent, veto, resize, or reverse a Child.
- Phase 1F advances Parent objectives only at a later completed H4, keeps a
  monotonic directional frontier, and gives no level family a score. The result
  rejects nearest-target completeness as action authority.

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

## Closed Phase-1D result

- The original monthly MT5 export was invalidated by a first-chunk three-hour
  clock error. The synchronized single-query source has `68,369` unique values;
  one exact ten-member BLS timestamp override leaves `20,274` timed clusters.
  Calendar offset zero still ranks first in the frozen alignment audit.
- Broker hour 16 was normalized activity rank 1 in 2022–2025 and rank 2 in
  2026. Its V10 Children still earned `+203.53R`; fixed-hour avoidance is not a
  viable stop-reduction rule.
- USD-high releases produced median matched 15-minute tick-volume/range lift of
  `1.11x/1.15x`; the incremental range effect decayed to `1.03x` by four hours.
- All V10 Children 30–60 minutes before USD moderate/high releases formed an
  86-Child, `-33.63R`, PF `0.51` slice with 40 stopped units and only `5.78R`
  right tail. The hour-20 aligned subset had 35 Children and `24.73` stopped
  units per 100 versus `3.85` for other hour-20 aligned Children.
- The 35-Child interaction is small and event-family heterogeneous. It is a
  frozen shadow feature, not a consumed-data veto.
- For NHA flips within four hours after USD moderate/high events, linked-k1 stop
  rate increased from `16.28%` to `27.11%` across causal surprise-magnitude
  bins while mean new FAST-run length fell from `3.62` to `2.90` H4 bars.
- Two independent packs were byte-identical, passed validation, and parsed zero
  post-cutoff price rows.

## Closed Phase-1D interpretations

Do not promote or tune on consumed outcomes:

- broker hour 16, hour 20, or a named session as a standalone veto;
- avoiding all high-importance or USD events;
- using actual/forecast surprise before release or as a direction oracle;
- treating the 35-Child hour-20 interaction as sufficient trade authority;
- discarding post-event high-stop states that still contain large right-tail R.

## Closed Phase-1E result

- A fixed UTC+3 broker mapping passes 56/56 NFP and 38/38 Fed-rate schedule
  sentinels after the one locked source correction.
- London-New-York overlap is the most active minute-for-minute phase. Session
  activity is real, but session stop burden and economic conviction diverge.
- London-before-New-York has `16.10` stopped units per 100 and also the highest
  session net R (`+294.28R`) and right tail (`331.15R`). New-York-after-London
  has only `8.76` stopped units but just `+2.74R`.
- Friday and Wednesday have the highest broad weekday stop burden, while still
  retaining `+92.89R` and `+134.14R`. Wednesday contains the longest nine-stop
  chain but also `265.96R` of >=5R right-tail units.
- Linked-k1 stop rates after FAST flips are roughly 35.5%–37.9% in Asia/London
  phases versus 13.0%–14.3% after London/outside core. Mean new run length is
  similar, so time describes immediate whipsaw more than eventual run length.
- The 35-Child H20 pre-event interaction is wholly New-York-after-London but is
  spread across auctions, Baker Hughes, FOMC, and multiple weekdays. Its 95%
  week-block net-R interval crosses zero and it remains shadow-only.
- Two complete output packs are byte-identical across ten files; 36 tests and
  both validators pass with zero post-cutoff price rows parsed.

## Closed Phase-1E interpretations

Do not promote or tune on consumed outcomes:

- avoiding London, Friday, Wednesday, or any named session to reduce stops;
- treating low-stop New-York-after-London exposure as high-conviction capital;
- using a session label as information independent of the six H4 decision slots;
- funding or vetoing the 35-Child H20 pre-event interaction;
- promoting the small Asia-Friday or session/weekday/CRT cells as rules.

## Closed Phase-1F result

- Contract `v12-phase1f-parent-target-succession-v1` selected `4,675` rolling
  targets across all `2,649` Phase-1B Parents; `3,089` completed before Parent
  end. Two independent 13-file packs are byte-identical and all 41 tests pass.
- External targets are structurally dense: `2,551 / 2,780` are previous-H4-only
  clusters, every external cluster contains H4, median selection distance is
  `0.224 H4 ATR`, and median completion time is `0.483` hour.
- `1,422 / 1,499` active-Parent V10 Children are target-unfinished. Every one of
  the 118 carry Children, 60 bridges, 31 repairs, and 35 H20 pre-event Children
  is unfinished. The definition therefore cannot select the useful bridges.
- The 77 complete/reframe-pending rows consist of 66 `ORDER_FAIL`, ten
  `EXIT_PENDING_BLOCK`, and one ordinary entry. Their low pooled stop burden is
  not interpretable as a strategy advantage.
- External-target Children carry lower pooled stopped exposure, but the effect
  is strongly conditioned by aligned/opposed relation, first/later Child, CRT
  origin branch, and side. High-outside LONG continuation is positive while
  low-outside SHORT continuation is negative.
- The broad carry result is unchanged: `+23.19R` delta with 26 added Hard SLs,
  66 added stopped units, and negative 2026 delta. Target completeness does not
  rehabilitate it.

## Closed Phase-1F interpretations

Do not promote or tune on consumed outcomes:

- treating the existence of a nearest one-use target as Parent conviction;
- carrying or adding on every unfinished rolling target;
- interpreting the reframe-pending group's low stop rate without separating
  market-closed and blocked execution states;
- removing previous-H4 or imposing a minimum ATR distance after seeing this
  target-density result;
- treating external-target phase as a veto or size release without controlling
  branch, side, and first/later Child status.

## Closed Phase-1G result

- The raw-M1 causal prefix produced `4,868` completed source boxes and path
  contexts for all `1,649` V10 rows, `2,234` FAST flips, 60 bridges, and 31
  confirmed repairs. Two independent 14-file packs are byte-identical.
- On `1,409` actual V10 entries, full path improved mean out-of-time stop Brier/
  log loss/AUC from `0.1110 / 0.3747 / 0.6629` to
  `0.1067 / 0.3577 / 0.7320`. Fold 2 calibration worsened.
- Settlement/repair and boundary consumption carry the strongest compact stop
  information. Static session names and event sequence alone do not explain it.
- Full path does not consistently improve `>=5R` estimation beyond continuous
  time, and FAST run-length mean R2 is `-0.0155`. The frozen joint success gate
  is not met.
- A post-contract `P(>=5R) - P(stop)` coordinate separates a high-conviction
  quintile with `5.26%` pooled stopped units and positive R in all three folds,
  but this is consumed-data hypothesis generation, not a sizing result.

## Closed Phase-1G interpretations

Do not promote:

- a stop-only V10 veto; the highest stop-risk quintile retains `+135.99R` and
  `225.08R` of `>=5R` right-tail capital;
- the exploratory conviction score or any quintile boundary as sizing;
- event proximity as the cause of a source-box break;
- continuous path as a forecast of how many H4 bars the next FAST run lasts;
- a hidden threshold selected from the favorable consumed folds.

## Closed Phase-1H result

- Two independent nine-file packs are byte-identical. All focused tests and
  complete-pack validation pass; zero post-cutoff price rows were parsed.
- The 50-field compact path improves both frozen outcome heads versus continuous
  clock on mean log loss. Its train-calibrated Q5 lowers stopped exposure in all
  folds and retains positive R, but fold-2 Q5 R/unit is below its population.
  The frozen primary gate fails.
- Adding FAST/STD/SLOW HA improves stop log loss in all three folds and produces
  the cleanest Q5 capital slice, but does not improve right-tail log loss.
- Wave alone worsens stop log loss on average and fails side/capital stability;
  HA plus Wave also fails the two-head incremental gate.
- Historical absolute-volatility terciles do not travel across eras: every test
  row falls in the training-defined high tercile. Era stability is unproven.

## Closed Phase-1H interpretations

Do not promote:

- compact Q5 or the shadow tilt as a position-size map;
- the attractive HA Q5 as proof of future edge;
- HA as a right-tail predictor merely because it improves stop discrimination;
- Wave as useful after path state merely because some pooled capital rows look
  favorable;
- absolute prior-range terciles as stable liquidity regimes.

## Closed Phase-1I result

- Phase 1I is the first direct run-episode reverse engineering: 679 funded FAST
  runs are classified after completion as 57 tail journeys, 181 stop-only runs,
  and 441 neutral runs, then observed again at first entry using causal state.
- Forty-six stop-only runs follow a prior funded stop-only run and carry 115
  stopped units. The frozen policy removes 58.6% of the test repeat units but
  lowers normalized stop burden only from 13.21 to 12.88 per 100 funded units.
- It retains 86.8% of Children and 87.8% of tail units, but fold-1 tail retention
  is only 65.3%. Pooled win rate improves only 0.28pp and equal-stop-budget R is
  below V10. Tail, win-rate, and equal-risk gates fail.
- Perfect repeat-stop removal has real value: 10.14 stopped units per 100,
  complete tail retention, 95.3% Child retention, and +534.52R versus +446.37R.
  It raises Child win rate only 1.58pp, so this narrow target alone cannot create
  a dramatic win-rate change.
- Stop-only discrimination is usable but unstable; tail-run AUC is 0.563,
  0.693, and 0.502. Existing first-decision dimensions cannot protect rare
  decisive journeys.

## Closed Phase-1I interpretations

Do not promote:

- the asymmetric first-decision policy despite its repeat-unit removal;
- absolute stopped units removed without funded-exposure normalization;
- broad skip-after-stop or one-run cooldown;
- the perfect oracle as evidence that the available features can identify it;
- descriptive London/New-York transition or HA contrasts from only 11 after-
  stop tail journeys.

## Closed Phase-1J result

- The fixed 181 stop-only and 57 tail-journey runs yield 6,872 causal M15 rows;
  four runs terminate before one post-entry M15 completes.
- At the second completed M15, cumulative MAE separates tail from stop-only
  runs with pooled AUC 0.720 and fold AUCs 0.734, 0.681, and 0.689. Signed path
  efficiency is directionally stable with pooled AUC 0.673.
- Two favorable settlements occur in 96.5% of tails versus 55.2% of stop-only
  runs; two opposed settlements occur in 50.9% versus 81.8%. These directions
  repeat in all test folds, but lifetime event prevalence is exposed to longer
  tail terminal times.
- Six repaired-departure feature pairs pass the frozen mechanism screen. This
  nominates staged participation for a capital audit; it does not authorize a
  rule.

## Closed Phase-1J interpretations

Do not promote:

- second-M15 MAE, path efficiency, favorable/opposed persistence, or repaired
  departure directly to funding;
- lifetime event occurrence as if both classes had equal observation time;
- after-stop pooled AUC from only 11 tail runs as fold-stable evidence;
- a fixed two-bar schedule or threshold tuned on this consumed result.

## Closed Phase-1K result

- `PROGRESSION_RELEASE` retains 97.7% of test Children and 95.9% of tail units,
  but removes only 0.6% of stops and zero repeat stopped units. Win rate is
  unchanged and equal-stop-budget R worsens.
- `DAMAGE_STOP` removes 21.1% of stops only by removing 32.3% of Children and
  22.1% of tail units. Stopped units per 100 worsen from 13.21 to 15.54.
- First-Child-only retains 47.6% of Children and 52.9% of tail units; its
  normalized stop burden and equal-risk economics are much worse.
- Early M15 path separation therefore does not map onto the existing next-H4
  Child decision. The primary gate fails.

## Closed Phase-1K interpretations

Do not promote:

- two favorable M15 settlements as permission for the next existing H4 Child;
- two opposed M15 settlements as a broad stop-funding rule;
- first-Child-only as proof that lower exposure improves quality;
- a tuned M15 threshold intended to rescue these consumed mappings.

## Closed Phase-1L result

- Exact H4 parity is established against all 6,770 historical V10 rows.
- Moving the same repeated-HA semantics to H1 creates 3.92x Children and 3.91x
  stopped units without a material stop-density or win-rate improvement.
- H1 core retains 43.8% of H4 equal-total-stop-budget R and is negative in two
  years. H4 FAST/STD alignment raises retention to 70.4% but still fails.
- M15 directional net and body efficiency have stable univariate associations,
  but directional net reduces both stop and later right-tail incidence. It is a
  competing-outcome coordinate, not an admission rule.

## Closed Phase-1L interpretations

Do not promote:

- repeated H1 HA Children as a higher-opportunity replacement for H4;
- H4 FAST/STD alignment as sufficient Parent authorization;
- any threshold on the three passing M15 univariate screens;
- gross H1 R without matching total stopped-unit budget.

## Closed Phase-1M result

- H1 `k=1` plus H4 FAST alignment reduces total stops by 36.7%, maximum stop
  streak from 11 to 6, and maximum concurrent units from 21 to 1.
- Equal-total-stop-budget R retains 92.4% of H4, but per-attempt stop density
  worsens from 26.28 to 31.62 and win rate falls from 32.27% to 31.37%.
- The lane is negative in 2024 and 2026. Its pooled +223.57R is fully supplied
  by 2023 (+229.46R); the other four years sum to -5.89R. SHORT is negative.
- The reduced stop count is a lower-frequency effect, not higher conviction.

## Closed Phase-1M interpretations

Do not promote:

- H1 `k=1` or H4-aligned `k=1` to entry or sizing authority;
- lower total stops as evidence of a higher hit-rate strategy;
- a long-only rule, 2023-era condition, or H4 alignment threshold fitted after
  seeing the concentration;
- one-active-Child exposure as proof of edge rather than a property of k1 runs.

## Closed Phase-1N result

- H1 `k=1` has 8,666 candidates and M15 `k=1` has 34,519 candidates under the
  causal lower-clock matrix.
- H1 HA+M15 micro, H1 HA+static time, and M15 HA+static time pass predictive
  screens, but their Q5 bands retain only `18.75%`–`21.46%` of Children.
- H1 right-tail R falls to zero in both passing broad bands; M15 retains only
  `3.03%`. Broad temporal admission fails the capital gate.

## Closed Phase-1O result

- The after-one-stop cohorts contain 2,586 H1 and 9,657 M15 candidates.
- H1 nonlinear temporal heads remove roughly `35%`–`42%` of repeat stops while
  retaining `94%`–`98%` of right-tail capital, but one OOS fold remains negative.
- M15 after-one-stop models find repeat risk but remove too much tail and net R.

## Closed Phase-1P result

- The intermediate clocks create 4,246 H2 and 17,012 M30 `k=1` candidates;
  after-one-stop cohorts contain 1,309 H2 and 4,820 M30 candidates.
- Four H2 and six M30 model families pass the frozen consumed-data capital,
  year, side, fold, and liquidity-era gates.
- H2 continuous clock removes `32.89%` of repeat stops with `95.10%` tail
  retention. M30 session path removes `37.25%`, retains `91.24%` of tail, and
  raises OOS net R from `209.79` to `234.62` on consumed evidence.
- M30 micro/session path is the strongest research boundary; H2 is supportive.

## Closed Phase-1Q result

- Third-and-later-stop cohorts contain 357 H2, 686 H1, 1,249 M30, and 2,285
  M15 candidates.
- Only M15 session-path and static-time heads pass all frozen gates. Session
  path removes `31.65%` of third+ stops, retains `97.36%` of right-tail R, and
  reduces maximum streak from five to four.
- Raw and equal-stop-budget R both remain below baseline and win rate is almost
  unchanged. The result describes deep churn but does not solve it.

## Closed Phase-1N through Phase-1Q interpretations

Do not promote:

- H1/M15 temporal quintiles as broad admission or sizing rules;
- the pooled H1 after-one-stop improvement while one frozen fold is negative;
- M30/H2 HGB scores, model depth, or quintile boundaries fitted on consumed data;
- M15 state before two prior stops, or the claim that it eliminates stop chains;
- lower timeframe itself as the edge. The useful object is clock-specific
  temporal state conditional on the stop-chain stage.

## Closed Phase-1R result

- Causal annual expanding models remove 339 of 1,004 targeted repeat stops
  (`33.76%`) across 2023–2026.
- Across all M30 history, the policy removes 339 of 4,820 stops (`7.03%`) but
  reduces net R from `384.61` to `329.97`, retains `88.84%` of >=5R tail, and
  worsens maximum stop streak from five to six.
- In the selected-R7G window, M30 policy improves its baseline from `189.88R`
  to `209.76R`, while V10 R7G earns `741.01R` at `12.52` stopped units per 100
  versus M30's `27.63`.
- At equal V10 funded units M30 earns `123.87R`; at equal 486 stopped units it
  earns `56.14R`. M30 session path is not a V10 replacement.

## Closed Phase-1S result

- Three same-week-embargoed OOS folds cover `1,219` frozen V10 R7G Children.
- Weekly price/event state produces stable stop-risk discrimination, but weak
  `R >= 2` journey discrimination.
- Full veto reduces stopped units `353 -> 225` and stop density `12.38 -> 10.19`
  per 100, while net R falls `498.26 -> 249.32` and >=5R tail falls
  `170.70 -> 46.80`.
- The flagged `288`-Child cohort has twice the stop rate of the kept cohort but
  still contains `248.94R` and `123.90R` of >=5R tail. It is a high-variance
  transition state, not an unnecessary-direction state.

## Closed Phase-1T result

- Direct all-head weekly-price retraining reduces selected Children
  `1,649 -> 1,561` and stopped Children `232 -> 214`, but refit stopped-unit
  density slightly worsens and maximum streak remains five.
- Net R falls `722.47 -> 421.89`; >=5R tail falls `283.59 -> 163.06`; all three
  years and both sides lose R.
- R4-only ablation identifies ranking displacement as the main damage. The
  removed baseline set carries `210.22` weighted R and `106.37R` of >=5R tail;
  the added set carries `-33.34R` and no >=5R tail.
- STOP-only weekly price improves AUC and log loss but saves only four refit
  stopped units while losing `40.66R`. Event response saves eight and loses
  `42.87R`. Predictive lift does not imply a useful capital mapping.
- Two builds are byte-identical. R4 parity is exact, while XGBoost STOP/R7G
  parity versus the supplied MT5 ledger remains incomplete and explicit.

## Closed Phase-1U result

- The exact MT5-selected control has 1,649 Children, 232 Hard-SL Children, 635
  positive Children, 16 >=5R Children, and a maximum stop streak of five.
- The frozen ownership gate has 1,331 Children, 158 Hard-SL Children, 528
  positive Children, nine >=5R Children, and a maximum streak of four.
- Stop rate improves on both sides and in every represented year, but 74 avoided
  stops cost 107 positive Children. Positive retention is `83.15%` and >=5R
  retention `56.25%`, so the count-quality and tail gates fail.
- Causal k1 transition `00_TO_11` has a low `13.53%` stop rate, but persistent
  opposition retains four >=5R Children and `108.48R`. Transition sequence is
  informative but not an authorization rule.
- Two builds are byte-identical; tests and pack validation pass. No Phase-1U
  state, policy, or transition has action or sizing authority.

## Closed Phase-1V result

- V10 has 679 funded entry episodes, 197 positive and 482 negative. The 57 tail
  episodes lift total result to `+646.18R`; the 622 non-tail episodes total
  `-423.25R`, with a `-342` one-vote count balance.
- Only seven of 53 inter-tail blocks are positive. Ordinary equity decline is a
  measured property, not a visual anecdote.
- First-Child Hard SL identifies a clean entry failure in 144 of 145 cases, but
  338 negative episodes have no first-Child Hard SL. Another 48 begin with a
  positive first Child and become negative through later management.
- Entry-only ownership saves 65 first stops and 16 repeated first stops, but
  loses 70 positive and 16 tail episodes. The non-tail count slope remains
  approximately `-0.55`; all ownership states remain negative.
- Two builds are byte-identical and all source joins reconcile. No Phase-1V
  accounting result or policy has action or sizing authority.

## Next hypotheses

These are questions, not rules:

1. Can a W1 CRT Parent create an H4 directional candidate by distinguishing
   sweep-return from outside acceptance before HA participates in Child timing?
2. Does the Phase-1S weekly state add only calibrated transition-risk context
   inside that independently created candidate without vetoing tail opportunity?
3. Does the M15 third-and-later-stop warning transfer as a subordinate warning
   while preserving Parent/Child semantics and the H4 execution clock?
4. Can Python and MQL5 produce identical W1/H4 weekly-state, branch, and event
   ledgers before any Strategy Tester economics are claimed?
5. If future evidence fails, should all lower-clock and weekly-state models
   remain diagnostic while only explicit CRT Parent branches create candidates?
6. Can a future-frozen Parent-created candidate use weekly transition risk as
   calibration context without letting it compete with R4 for broad ranking or
   reusing the failed `EV>0` R7G map?
7. Can a future Parent-created Child use FAST, STD, and SLOW as event,
   developing acceptance, and ownership-transfer clocks without converting
   their current alignment into another broad veto?
8. What causal Journey-birth event distinguishes the 338 negative episodes that
   do not begin with a first-Child Hard SL from ordinary and tail successes?

## Evidence boundary

- All GOLD# observations through `2026-09-18 23:57` are consumed.
- GOLD# 2021 remains sealed.
- Phase 1A is a consumed-history structural-R backtest. Phase 1B is a
  consumed-history journey/transition diagnostic. Phase 1C is a consumed-history
  holding-clock and repair diagnostic. Phase 1D is a corrected temporal/event
  diagnostic, Phase 1E is a named-session/weekday diagnostic, Phase 1F is a
  consumed-history rolling-target density diagnostic, Phase 1G is a continuous-
  path competing-outcome diagnostic, Phase 1H is a compact-head/HA/Wave
  component-role diagnostic, and Phase 1I is a run-episode reverse-engineering
  and oracle-bound diagnostic. Phase 1J is a within-run causal-timeline and
  early-mechanism diagnostic. Phase 1K is a failed staged-funding capital
  mapping diagnostic. Phase 1L is a failed H1-main-clock feasibility diagnostic,
  Phase 1M is a failed-stability H1 transition-Child diagnostic, Phase 1N is a
  failed broad temporal-admission diagnostic, Phase 1O is an unstable after-one-
  stop interaction diagnostic, Phase 1P is an intermediate-clock boundary
  diagnostic, Phase 1Q is a deep stop-chain warning diagnostic, Phase 1R is a
  failed full-history M30/V10 replacement comparison, and Phase 1S is a failed
  weekly-direction veto with retained stop-risk mechanism. Phase 1T is a failed
  direct V10-head feature augmentation with a declared XGBoost platform-parity
  limit. Phase 1U is a failed broad multi-speed ownership gate with retained
  transition-state mechanism. Phase 1V corrects admission accounting to entry-
  episode grain and rejects entry-only ownership. No V12 EA, MQL5 parity,
  actual-tick economics, or independent future validation exists.
- The post-`2026-09-18 23:57` prices in the supplied files remain unread by the
  official builder and reserved for a later frozen shadow.
