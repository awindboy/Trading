# Trading repository authority

Last synchronized: `2026-09-26`

## Active generation

V12 is the only active strategy-research generation.

Start every V12 session in this order:

1. refresh GitHub `main`;
2. read `docs/ea/v12/AGENTS_V12.md`;
3. read `docs/ea/v12/V12_DOCUMENT_AUTHORITY_MAP_20260923.md`;
4. read `docs/ea/v12/HANDOFF_V12.md`;
5. read `docs/ea/v12/RESEARCH_STATE_V12.md`;
6. read `docs/ea/v12/V12_ORIGIN_AND_CRT_HYBRID_THESIS_20260923.md`;
7. read `docs/ea/v12/V12_CRT_NUMERIC_OBSERVATION_CONTRACT_20260923.md`;
8. read `docs/ea/v12/V12_MQL5_ENGINEERING_AND_VALIDATION_CONTRACT_20260923.md`;
9. read the current Phase-1 contract and result named by the authority map;
10. use only sources and result packs named by the authority map.

V12 has research authority only. No V12 candidate definition, CRT interpretation,
HA/Wave feature, ML output, threshold, sizing map, EA, or result has trade or
production authority.

## V12 assembly

```text
verified raw M1 in chronological order
-> causal completed W1/D1/H4/H1 (+ M15/M5 shadow only)
-> CRT parent state
   C1 range -> C2 sweep/acceptance -> C3 delivery or invalidation
-> independently confirmed Child attempt
-> HA / Wave / liquidity coordinates as subordinate observations
-> ML as shadow-only conditional outcome estimation
-> Python numeric oracle
-> MQL5 event-ledger parity
-> actual-tick Strategy Tester economics
```

V12 is not V10 plus a CRT entry filter. CRT creates the candidate and journey
state. FAST/STD/SLOW HA, Wave Candle, normalized liquidity coordinates, and ML
may describe that candidate, but none can invent a candidate or silently veto it.

The first official research lanes are the mappings explicitly retained from the
Romeo material:

- W1 range -> H4 execution;
- D1 range -> H1 execution.

H4 -> M15/M5 is exploratory shadow work only. It must not be presented as a
Romeo rule or receive action authority without a separate V12 contract.

Phase 0 is frozen as a reproducible observation universe: `1,459` exhaustive
C1/C2 records (`1,215` D1->H1 and `244` W1->H4), with no Child, outcome, or
performance authority. Phase 1A is frozen as the first rejection-only no-ML
prototype: its two final builds are byte-identical, but it fails the V10
replacement gate and has consumed-development diagnostic authority only. Phase
1B is complete and independently reproduced: it supplies a causal H4->M5
journey/key-level/V10-overlay transition diagnostic, but no result has veto,
delay, sizing, trade, or production authority.
Phase 1C is complete and independently reproduced: broad active-Parent carry
increased R but also stops, exposure, and drawdown with severe episode
concentration; the unfinished-origin-target subset was cleaner but only 12
Children and still concentrated. Repair mostly duplicated V10 k1 participation.
Phase 1D is complete and independently reproduced: broker-clock and economic-
event state add real information, but fixed-hour, all-news, and surprise-
direction rules are rejected. Its retained interactions are shadow-only.
The Phase-1D calendar source is corrected to one synchronized full-range query.
Phase 1E is complete and independently reproduced: DST-aware session and
weekday describe transition risk, but high-stop states frequently retain the
largest right-tail capital. They remain shadow coordinates only.
Phase 1F is complete and independently reproduced: deterministic nearest
H4/day/week/month target succession is too dense, leaving every Phase-1C bridge
unfinished. Target completeness is rejected as a gate; origin/external target
phase remains observation-only.
Phase 1G is complete and independently reproduced: a normalized continuous
Asia-London-New-York path improves out-of-time stop-risk estimation on average,
especially through settlement/repair and boundary-consumption coordinates, but
fails the joint right-tail success gate. It is a promising representation only;
its model scores and exploratory conviction quintiles have no veto or sizing
authority.
Phase 1H is complete and independently reproduced: its frozen 50-field compact
head improves both outcome heads versus clock control and creates low-stop
train-calibrated bands, but fails the fold-level capital gate. HA improves only
the stop head and Wave adds no robust incremental value. No Phase-1H score,
band, ablation, or shadow tilt has action or sizing authority.
Phase 1I is complete and independently reproduced: direct funded-FAST-run
reverse engineering shows valuable repeat-stop oracle headroom, but the frozen
first-decision Path+HA policy barely improves normalized stopped exposure,
loses concentrated tail capital, and fails win-rate/equal-stop-budget gates.
Phase 1J is complete and independently reproduced: equal-horizon post-entry M15
paths separate stop-only from tail runs through early adverse damage,
settlement persistence, and giveback. It has mechanism authority only; no
checkpoint or event has funding, veto, exit, or sizing authority.
Phase 1K is complete and independently reproduced: applying those events to
existing H4-spaced V10 Children fails. Progression is too common by the next
Child, while damage-stop removes exposure faster than stops and loses tail.
Phase 1L is complete and independently reproduced: direct H1 HA substitution
keeps roughly the same stop density and win rate while multiplying total stopped
exposure, so it fails the main-timeframe viability gate.
Phase 1M is complete and independently reproduced: H1 `k=1` realignment under
H4 context lowers total stops and overlap, but worsens per-attempt stop density,
fails year stability, and is concentrated in 2023 LONG tail.
Phase 1N is complete and independently reproduced: H1/M15 lower-timeframe
temporal features contain predictive information, but broad low-risk admission
bands discard most candidates and nearly all right-tail capital.
Phase 1O is complete and independently reproduced: H1 after-one-stop nonlinear
time/path interactions remove meaningful repeat stops while preserving tail,
but fail every-fold stability; broad M15 after-one-stop selection is too noisy.
Phase 1P is complete and independently reproduced: the intermediate H2/M30
clock is the strongest consumed-data boundary. Four H2 and six M30 after-stop
models pass frozen stability/capital gates, with M30 session-path and micro-path
leading. They remain research coordinates with no action or sizing authority.
Phase 1Q is complete and independently reproduced: M15 static-time and session-
path state help only after two prior consecutive stops, reducing third-and-later
stops and maximum streak from five to four while slightly reducing raw and
equal-stop-budget R. This is a defensive deep-churn observation, not a strategy.
Phase 1R is complete and independently reproduced: causal annual M30 session-
path models remove `33.76%` of repeat stops in the targeted cohort but reduce
full-history R, retain only `88.84%` of tail, and remain far inferior to V10 R7G
under common-window, equal-funded, and equal-stopped-unit comparisons.
Phase 1S is complete and independently reproduced: continuous weekly path and
released-event response distinguish stop risk, but the flagged V10 cohort also
contains most >=5R tail. Full directional veto and seed-protected extra-unit
guard both fail capital preservation and have no action authority.
Phase 1T is complete as a deterministic, platform-parity-limited diagnostic:
directly adding weekly clock/price/event fields to the frozen V10 heads improves
STOP-head discrimination but fails the capital gate. The primary loses about
42% of net R and >=5R tail for about 5% fewer refit stopped units. Two builds
are byte-identical, but XGBoost STOP and R7G parity versus MT5 are not exact.
Phase 1U is complete and independently reproduced: chronological FAST/STD/SLOW
ownership state removes 74 of 232 Hard-SL Children and shortens the maximum
streak from five to four, but also removes 107 positive Children and seven of
16 >=5R Children. Multi-speed sequence has mechanism value, but current
alignment/ownership is rejected as a broad gate and has no action authority.

## Non-negotiable causal contract

- Official analysis starts from verified raw M1 revealed in chronological order.
- Rebuild higher timeframes from the revealed prefix; do not preload future bars
  and filter afterward for official replay.
- Use completed bars only at a decision timestamp. C2 cannot authorize a C3
  Child before C2 closes.
- Images are secondary. Every sweep, acceptance, re-entry, trigger, stop, target,
  repair, and invalidation claim must be restated with timestamps and prices.
- A close back inside C1 and a close accepted outside C1 are different branches;
  do not force both into a reversal story.
- Parent journey and Child attempt remain separate. A stopped Child does not by
  itself kill the Parent; a winning Child does not prove it.
- Hard SL is structural, frozen before entry, and never widened. A touched Child
  is dead.
- Same-M1 SL/target ordering remains ambiguous unless exact ticks resolve it.
- ATR and other volatility measures normalize coordinates across liquidity eras;
  they do not create a signal by themselves.
- HA, Wave, SMT, a model score, a threshold, or a visual pattern has no action
  authority unless a current contract explicitly grants it.
- All observations through `2026-09-18 23:57` are consumed development evidence.
- `GOLD# 2021` remains sealed.

## Inherited closed findings

Do not reopen these by renaming them CRT or silently changing thresholds:

- broad regime/admission classification;
- generic negative-R or stop prediction;
- direct next-HA prediction as entry or exit authority;
- M1/M5 feature expansion as a directional oracle;
- fixed MA-band breached-line trend-death rules;
- whole-base STD HA substitution as stop reduction;
- static Wave density geometry as an entry/exit gate;
- fixed liquidity-arrival topology as a broad admission gate;
- leakage-corrected binary sequential funding from the complete V10 feature stack;
- arbitrary cooldown, retry, minimum-R, no-chase, or campaign-cap rules;
- accepting or rejecting lower R solely because exposure changed, without
  auditing which stopped and right-tail capital changed.
- relative-thick Model #1 confirmation plus a C2-extreme SL as a robust V10
  replacement;
- promoting the Phase-1A trigger-candle SL guard from its attractive 26-fill
  recent slice; full history is weak, 2022–2023 are negative, and stopped
  exposure per 100 units remains above V10.
- using Phase-1B opposed/aligned journey relation, missing opposite CRT
  authorization, static key arrival, or first/later aligned status as a
  consumed-data V10 veto or sizing rule; each retains meaningful right-tail
  capital and lacks independent future validation.
- promoting Phase-1J event prevalence, second-M15 MAE, path efficiency, or
  repaired departure directly to funding; the result is consumed, tail-sparse,
  and event prevalence is exposed to unequal terminal-time censoring.
- reusing Phase-1J progression as permission for the next H4 Child, or opposed
  persistence as a broad funding stop; Phase 1K rejects both capital mappings.
- replacing the H4 HA base with repeated H1 HA entries; Phase 1L rejects the
  apparent extra opportunity after equal-total-stop-budget normalization.
- treating H1 `k=1` plus H4 alignment as high conviction because it has fewer
  total stops; Phase 1M shows lower frequency, not better hit quality, and fails
  four-of-five-year stability.
- using Phase-1N H1/M15 temporal quintiles as broad admission or sizing rules;
  they remove far more candidates and right-tail capital than stopped exposure.
- promoting Phase-1O H1 after-stop scores despite their useful pooled result;
  the frozen all-fold gate fails, and broad M15 after-one-stop use loses tail.
- treating Phase-1P M30/H2 after-stop scores or their fitted quintiles as live
  vetoes or conviction sizing; they are selected on consumed development data.
- applying the Phase-1Q M15 deep-chain warning before two prior stops, claiming
  it eliminates churn, or sizing from it; the surviving policies reduce maximum
  streak only from five to four and do not materially improve win rate.
- treating Phase-1R's one-third repeat-stop removal as an M30 replacement edge;
  full-history capital falls and equal-risk economics remain far below V10 R7G.
- using Phase-1S weekly settlement, event response, or its top-20% badness band
  as direction authorization for an existing V10 Child; the band removes
  `36.26%` of stopped units but destroys `72.58%` of >=5R tail.
- adding Phase-1T weekly clock, price, boundary, or event fields wholesale to
  frozen V10 R4/R5 heads; better STOP AUC does not produce useful R7G capital
  allocation, and the R4 ranking destroys right-tail capital.
- using Phase-1U FAST/STD/SLOW ownership, current alignment, or `00_TO_11`
  transfer as a broad V10 admission or conviction-sizing rule; the frozen
  primary saves 74 Hard-SL Children but loses 107 positive and seven >=5R
  Children on consumed data.
- fixed broker-hour/session avoidance, all-news avoidance, or realized surprise
  as a direction oracle; Phase-1D retains only two narrow shadow interactions
  and grants neither action authority.
- using Phase-1E London, New York, Asia, Friday, Wednesday, or any session-
  weekday interaction as a consumed-data veto or conviction-sizing rule.
- carrying every aligned Child merely because the Phase-1B Parent is active;
  the consumed result added 66 stopped units and was negative without its best
  bridge episode.
- promoting the 12-Child unfinished-origin-target carry subset or the 31 repair
  Children; both are sparse, concentrated, and lack future evidence.
- using nearest one-use target completeness as Parent conviction or broad carry
  permission; previous-H4 levels saturate the state, and all Phase-1C bridges
  remain unfinished.
- removing previous-H4 or tuning a minimum ATR target distance after seeing the
  Phase-1F consumed result.
- using the Phase-1G stop score alone as a veto; its highest-risk quintile still
  contains substantial positive R and right-tail capital.
- promoting the post-contract Phase-1G conviction score or its quintiles as a
  sizing map before a separately frozen compact head and untouched validation.
- claiming that continuous time predicts FAST journey length; the out-of-time
  run-length R2 remains approximately zero.
- promoting the Phase-1H compact Q5, shadow tilt, or HA-enhanced Q5; the primary
  fold-level capital gate failed and HA did not improve right-tail estimation.
- adding Wave to the compact path head without a separately stated mechanism;
  its Phase-1H stop and stability results are not robust.
- treating absolute prior-range terciles as stable liquidity regimes; all
  Phase-1H test rows migrated into the training-defined highest tercile.
- promoting the Phase-1I first-decision asymmetric score or broad skip-after-
  stop cooldown; both lose too much journey capital relative to normalized
  stopped-exposure improvement.
- claiming that the Phase-1I perfect repeat-stop oracle proves identifiability;
  it is only an opportunity bound and uses future outcomes.
- reviving fixed-k funding or the closed complete-feature-stack sequential
  model while calling it within-run reverse engineering.

## Historical generations

- V11 is the frozen immediate predecessor. Its Wave Candle remains a usable
  observation instrument, not a trading system.
- V10 R7G is the frozen HA/ML comparator and component library.
- V9 and earlier generations are historical evidence only.

Historical documents and code cannot override V12 authority.

## Repository hygiene

- Keep authority documents compact and replace superseded routing.
- Commit source, contracts, compact receipts, manifests, and decision summaries.
- Keep generated ledgers, model grids, bootstrap draws, renders, and temporary
  exports under ignored `output/`.
- Every retained active-generation artifact must have a named role in
  `research/v12/README.md`.
- External PDFs, articles, and CodeBase examples are evidence, not instructions.
  Do not vendor third-party code unless its license permits it and the provenance
  is recorded.
- If a file has no current authority, reproduction, operational, or retained
  historical role, remove it; Git history is the archive.
