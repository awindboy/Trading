# V13 HA-9 trade-mode research backlog

Last synchronized: `2026-09-28`
Status: `RESEARCH BACKLOG / NOT ACTION AUTHORITY`

## 1. Why this program exists

The actual-tick ledger shows that V13 is not one homogeneous strategy.

- Child #1 is a low-win-rate, long-horizon Journey anchor.
- Child #2..#10 are short-horizon tactical add-ons.

The next problem is therefore not another broad entry veto. It is to determine,
after an add-on has entered and without seeing future price, whether its current
mode is:

```text
FAILURE
QUICK-HARVEST
NORMAL SWING
RUNNER
```

The same entry can then receive a different causal holding, protection, exit and
re-arm policy. Position sizing remains out of scope until these modes separate
stably across time.

## 2. Frozen boundaries

- Baseline 0 remains the frozen comparator.
- HA-9 remains the active research candidate, not production authority.
- Child #1 is not changed while the add-on mechanism is being decomposed.
- The canonical consumed period ends at `2026-08-28 20:00` broker time.
- Post-exit price may be used only as a research label, never as a candidate
  input.
- The one-H4 proof window and signal-extreme proof/lock price are not optimized
  on the consumed sample to rescue a result.
- MQL5 `Every tick based on real ticks` remains the authority for official
  execution economics.

## 3. Research sequence

### Phase 1 — Decompose the dominant loss and fast-profit populations

1. Reconstruct the actual MT5 Child ledger and distinguish Child #1 from
   add-ons.
2. Decompose 4–8h losing add-ons into genuine failures and post-timeout
   recoveries.
3. Decompose sub-4h winning add-ons into well-harvested trades and possible
   missed continuation.
4. At the first and second completed H1 checkpoints, inspect only causal:
   proof timing, H1 path, breakout acceptance, MFE/MAE, path efficiency,
   standard-H4 morphology, HASTOC, causal swing and activity state.

### Phase 2 — Counterfactual exit matrix

Keep actual entry fixed and replay executable causal exits:

| Horizon | Candidate exit/protection |
| --- | --- |
| Very short | opposite completed H1 HA; H1 close back inside proof level |
| Short | one-H1 state extension after timeout |
| Medium | opposite FAST-H4 HA; completed-H1 structural trail |
| Long | opposite standard-H4 HA; causal raw-swing trail |
| Current | HA-9 proof/lock/timeout |

The purpose is not to select the best exit in hindsight per trade. It is to test
whether a state observable before the action timestamp consistently identifies
which horizon is economically appropriate.

### Phase 3 — Failure-aware state timeout

Replace the coarse interpretation of `one H4 elapsed` with state diagnosis while
keeping the original HA-9 result as comparator:

```text
no proof + persistent opposition -> FAILURE candidate
no proof + repaired             -> one-H1 extension candidate
no proof + no opposition        -> weak continuation candidate
proof + rejected close          -> QUICK-HARVEST candidate
proof + accepted close          -> SWING/RUNNER candidate
```

No state is promoted merely because it improves one consumed aggregate. It must
reduce losses or improve ordinary blocks without hiding a transfer into larger
or longer losses.

### Phase 4 — Proof quality and holding mode

Study interactions rather than one-feature thresholds:

- time-to-proof by natural H1 ordinal;
- touch versus raw-H1 close acceptance;
- H1 HA alignment and repair/opposition state;
- standard-H4 body, delta expansion/contraction and wick state;
- HASTOC level and phase change;
- effort versus result from relative tick activity;
- local signal-H4 extreme versus causal raw progress swing.

These features may select holding mode. They do not automatically veto entry.

### Phase 5 — Information-based re-arm

After a failed add-on, do not use a fixed cooldown. Test whether a new tactical
Child is allowed only after genuinely new information, such as:

- a new causal progress swing break;
- break/acceptance beyond the failed signal extreme;
- H1 transition from repaired/persistent opposition to no opposition;
- standard-H4 delta re-expansion;
- a reset in Journey proof history.

Measure avoided repeat-loss clusters, skipped winning Children, trade count and
chronological block quality.

### Phase 6 — Journey persistence, runner and tactical roles

Separate two questions that were previously mixed:

1. Should an already-proven Child continue as the Journey runner?
2. Should a new late Child be added at the current price?

Study causal Journey age, proof history and late-Child deterioration. Candidate
role structure:

```text
Child #1                      = anchor
oldest surviving proven add-on = runner
new add-on                    = tactical
```

Journey length known only after the Journey ends is a label, not an input.

### Phase 7 — Entry-method selector

Only after the holding modes are credible, compare state-selected execution:

- market at Baseline-0 timing for strong expansion;
- HA-open pullback for normal state;
- breakout acceptance for fragile/opposed state.

This is a selector study, not a search for one universally superior entry.

### Phase 8 — Sizing

Sizing is last. A larger unit is considered only for a pre-action state whose
win rate, loss clustering, drawdown and ordinary block quality remain stable by
year and under large-winner trimming.

## 4. Evaluation order

Every candidate is judged in this order:

1. losing Child count;
2. non-flat win rate;
3. consecutive losses and repeat-loss clusters;
4. positive 25/50/100-trade block share;
5. chronological drawdown;
6. expectancy per Child;
7. trade count and churn;
8. profit factor and net profit;
9. large-winner and long-hold cost diagnostics.

Total profit alone cannot promote or reject a mechanism. Likewise, loss-count
reduction that merely converts ordinary losses into fewer catastrophic losses is
not an improvement.

## 5. Required receipts

Each phase must preserve:

- source hashes and canonical cutoff;
- population definitions and coverage;
- action timestamp and executable-price convention;
- strict positive/negative/zero counts;
- causal inputs separated from future-only labels;
- year slices and ordinary-block metrics;
- rejected mechanisms and why they failed;
- a clear statement of whether the result is observation, candidate action or
  official Strategy Tester evidence.

## 6. Progress on 2026-09-28

| Phase | Current result |
| --- | --- |
| 1. Loss/fast-winner decomposition | Complete; duration counts corrected and event populations reconstructed |
| 2. Exit matrix | Complete; global H1/FAST/STD replacements rejected |
| 3. State timeout | Complete; one-H1 extension failed post-cutoff and was rejected |
| 4. Proof/holding mode | Partial; proof speed failed, H1 acceptance runner failed; remaining feature work stays observational |
| 5. Information re-arm | Complete; one/two-failure gates rejected |
| 6. Runner/tactical roles | Complete; proven/accepted runner and add suppression rejected |
| 7. Entry-method selector | Not yet executed |
| 8. Sizing | Not authorized; no stable high-confidence mode exists |

The next distinct research question is whether market/pullback/breakout
execution can improve the same fixed add-on opportunity set without merely
reducing exposure. Do not reopen timeout length, re-arm cooldown or generic
FAST/STD runner searches.
