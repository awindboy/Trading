# EA Backlog

Last updated: 2026-08-21
Current phase: **D-148 ENTRY SURVIVAL FAILURE TAXONOMY — IMPLEMENTED / COMPILE + AUDIT PARITY PENDING**
Strategy authority: **UNCHANGED**
2021: **KEEP UNTOUCHED**

## P0 — D-146 post-+1R continuation-state audit

- [x] Complete D-145 lightweight runner audit on GOLD 2023/2024/2025.
- [x] Complete D-145 cross-market audit on BTCUSD/SILVER/CADJPY 2025.
- [x] Separate `Fill -> +1R` Entry survival from `+1R -> +2R` continuation.
- [x] Confirm lower M30 protected-to-external range progress at +1R in 6/6 market-year aggregate cells.
- [x] Confirm the same relationship in 11/11 comparable market-year x direction cells.
- [x] Confirm M30 maturity is not a stable Fill-time Entry-success discriminator.
- [x] Demote M30 net advance, FVG timing/displacement, +1R speed, simple progression/PB, M1 confirmation, and standalone leg expansion as general runner rules.
- [x] Freeze D-146 measurement contract in code with zero strategy authority.
- [x] At first +1R, freeze current M30 owner/protected/external/range state.
- [x] From +1R until +2R-or-SL, count/identify causal M30 same-direction BOS, opposite events, protected breaks, owner changes, and external refreshes.
- [x] Record whether the +1R-time external was delivered before terminal resolution.
- [x] Record whether a new outward M30 external becomes causally available before +2R.
- [x] At exact `+2R_REACHED` or `SL_AFTER_1R`, freeze terminal M30 state.
- [x] Keep exact tick outcome ordering; no OHLC reconstruction.
- [x] Keep unified one-file event ledger.
- [x] Keep active research objects restricted to actual +1R-success trades.
- [ ] MetaEditor compile with 0 errors.
- [ ] GOLD smoke audit OFF/ON non-audit parity PASS.
- [ ] Validate D-146 event completeness and runtime on GOLD 2025.
- [ ] Rerun development panel as needed: GOLD23/24/25, BTCUSD/SILVER/CADJPY 2025.
- [ ] Test relation direction by market and LONG/SHORT before any strategy design.

## P0 — Entry-survival research, separate branch

Current 2025 continuation Fill -> +1R:

```text
GOLD    58.8%
BTCUSD  47.4%
SILVER  40.0%
CADJPY  27.0%
total   41.1%
```

- [ ] Define a separate causal research question for `Fill -> +1R`.
- [ ] Use only information known at or before Fill.
- [ ] Do not use D-145 +1R maturity as an Entry gate.
- [ ] Diagnose market background/regime differences before adding filters.
- [ ] Require relationship direction to survive multiple symbols/periods.
- [ ] Preserve the eventual objective: >=50% realized WR with >1R average reward and positive cost-adjusted expectancy.

## P0 — Execution integrity, parallel and separate

### Recoverable pending-cancel rejection

- [x] Confirm cross-symbol stale-fill reproductions after `retcode=10018 / Market closed`.
- [ ] Implement exact-ticket retry for recoverable pending cancel rejection.
- [ ] Keep strategy cancellation required while broker pending remains live.
- [ ] Keep exposure/divergence lock until cancel or fill is proven.
- [ ] Regression-test known fixtures.

### Pending disappeared without fill/cancel proof

Known fixtures include EURCAD / GBPJPY / GBPUSD cases from 2025.

- [ ] Reconcile current-order state against order history, deal history, and position state.
- [ ] Determine true lifecycle cause.
- [ ] Add a deterministic rule only after cause is proven.
- [ ] Re-run contaminated symbol-years after fix.

### Right-censored year end

- [ ] Extend tester horizon beyond year-end until all in-scope origin trades are terminal.
- [ ] Require zero unresolved in-scope execution for final profitability evidence.

## P1 — Dynamic winner-extension strategy variant

**Blocked on D-146 causal evidence.**

Do not implement yet:

```text
fixed 1R TP
fixed 2R TP
progress < X hold rule
remaining-room > X hold rule
runner score
maturity Entry veto
```

Only after D-146:

- [ ] Decide whether post-+1R M30 structure refresh/deterioration is causal enough for a single controlled exit-management variant.
- [ ] Keep baseline and variant separate.
- [ ] Change one meaningful variable at a time.
- [ ] Compare realized WR, average win R, expectancy, DD, streaks, annual/directional breadth, and large-winner dependence.

## Research governance

Always:

- GitHub is Single Source of Truth.
- Read `AGENTS.md` and `HANDOFF.md` first.
- Strict no-lookahead.
- No threshold mining from pooled results.
- No one-year/one-symbol promotion.
- No arbitrary scores/veto stacks.
- Separate implementation correctness, strategy profitability, execution integrity, and portfolio risk.
- `2021 = KEEP UNTOUCHED` until a deliberately sealed validation stage.

## D-147 EXIT ARCHITECTURE RESEARCH V1

- [x] preserve ORIGINAL baseline mode
- [x] add actual-fill-risk frozen R-step trailing mode
- [x] retain structural TP under trailing mode
- [x] add frozen 50%-of-remaining integer-R partial mode
- [x] retain original SL and structural TP under partial mode
- [x] fail safe on broker min/step volume instead of substituting full close
- [x] aggregate partial-exit deals for final realized-net accounting
- [x] add D-147 result summarizer and ORIGINAL baseline comparator
- [ ] MetaEditor compile 0 errors
- [ ] D-147 ORIGINAL canonical parity vs D-146 baseline
- [ ] GOLD 2025 three-mode comparison
- [ ] development-panel cross-market validation
- [ ] decide whether any exit mode deserves promotion beyond research
- [ ] separately resume Fill -> +1R Entry-survival causal study

`2021` remains untouched.

## P0 — D-148 Entry-survival failure taxonomy

- [x] define population as `EXTERNAL_CONTINUATION + normalized SL before +1R`
- [x] keep exact Fill-to-SL risk and exact Bid/Ask barrier semantics
- [x] freeze original PLAN map timeframe/owner and Root identity
- [x] record frozen-owner protected break separately from total map-direction support
- [x] record Root invalidation separately
- [x] after SL, shadow-track original Entry recovery and original +1R recovery
- [x] terminalize on +1R recovery vs current H1/M30 direction-support loss vs right censor
- [x] no arbitrary post-SL time cutoff
- [x] retain runner after real position close without changing broker/strategy state
- [ ] MetaEditor compile 0 errors
- [ ] GOLD short audit OFF/ON non-audit parity PASS
- [ ] GOLD 2025 D-148 EVENT INTEGRITY PASS
- [ ] classify the 21 GOLD 2025 `<1R` failures by causal outcome
- [ ] compare causal pre-Fill context across failure classes and +1R controls
- [ ] decide whether D-148B needs extra M1 reaction-strength / correction-completion instrumentation
- [ ] validate any discovered relation on other GOLD years before strategy authority

### Future — smart partial management (recorded, not active)

- [ ] revisit `R_STEP_PARTIAL` together with D-145/D-146 continuation state so the fraction left as runner can depend on causally available post-+1R structure rather than a blind fixed 50%
- [ ] preserve a mechanical PARTIAL control when that study begins
- [ ] do not optimize a pooled M30-progress cutoff or partial fraction from GOLD 2025
