# V13 HA-9 trade-mode phase-1 receipt

Last synchronized: `2026-09-28`
Status: `CONSUMED DEVELOPMENT / OBSERVATIONAL / NOT ACTION AUTHORITY`

## 1. Question

Can information available during the first H4 after an add-on entry distinguish:

- 4–8h timeout losses that are genuine failures from cuts that soon recover; and
- sub-4h winners that were appropriately harvested from possible runners?

This phase does not change HA-9. It establishes the actual Child ledger,
corrects the research populations and tests whether the proposed mode features
contain enough separation to justify executable counterfactual exits.

## 2. Sources and causal boundary

| Source | SHA-256 |
| --- | --- |
| `ReportTester-318585216.xlsx` | `c82a2d826ea69bd7bd0ada31bd49d42bbef23419011b7517c91262a53b043104` |
| `GOLD#_M1_202201030100_202609222358.csv` | `fd6b1c886519b544b00dfdcf0ee390970e29c54bb3bf7530c3bd1ef52aa47250` |
| `GOLD#_H1_202201030100_202609222300.csv` | `2898e5b9b6f95a6e8fe27c0c6578f74b7a7bd8adbefe10132ab38e3eef1a426c` |
| `GOLD#_H4_202201030000_202609230000.csv` | `b080fb5463df1f80592cfeeecacc4d422069b69ac40635b912d03d97873aecbf` |
| ideal HA-9 `child_ledger.csv` | `9a586d9ab8233b4c25b5a5bf36d9db2cd7b136713176e3bbd2fd92c1e5c3e979` |

The report runs beyond the consumed boundary, through `2026-09-25`. Canonical
research therefore uses only Children closed by `2026-08-28 20:00`. Signal-H4
and named M1/H1 checkpoint features use only information available by that
checkpoint. Post-exit movement and the standard-H4 exit are labels only.

## 3. Ledger integrity and population corrections

The parser reconstructed 3,977 entries and 3,977 exits into 3,977 completed
Children. Every entry comment was resolved, there were no duplicate Child keys,
and realized-P/L matching error was below `9e-13`.

| Scope | Children | Strict wins | Strict losses | Zero | Net USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full report | 3,977 | 2,181 | 1,790 | 6 | +3,170.12 |
| Canonical cutoff | 3,858 | 2,118 | 1,734 | 6 | +3,067.50 |

Two source-summary definitions required correction:

1. The MT5 summary's 2,187 profitable trades includes six zero-profit trades;
   strict positive trades are 2,181.
2. `1,844 fast winners` is not the winning population. It is all full-report
   add-ons held under four hours. Strict winners among them are 1,505. The
   canonical equivalents are 1,790 total and 1,460 winners.

All 3,858 canonical actual Children joined one-to-one to the ideal HA-9 ledger,
the integrated H1/H4 feature ledger and the causal raw-swing ledger.

## 4. Child roles are economically different

| Role | N | Wins | Losses | WR, non-flat | PF | Net USD | Median hold |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Child #1 | 965 | 331 | 634 | 34.30% | 1.177 | +1,863.03 | 13.04h |
| Add-on #2..#10 | 2,893 | 1,787 | 1,100 | 61.90% | 1.099 | +1,204.47 | 2.96h |

This confirms that Child #1 and add-ons must not be pooled when researching
mode management.

## 5. Add-on duration decomposition

Canonical actual-tick results:

| Hold time | N | Wins | Losses | Zero | WR, non-flat | Net USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| <=1h | 925 | 816 | 104 | 5 | 88.70% | +3,918.48 |
| >1h and <4h | 865 | 644 | 220 | 1 | 74.54% | +4,138.71 |
| >=4h and <8h | 1,016 | 282 | 734 | 0 | 27.76% | -7,383.08 |
| >=8h | 87 | 45 | 42 | 0 | 51.72% | +530.36 |

The 734 losing 4–8h add-ons are the dominant canonical add-on loss pile.
733 of 734 never proved the signal-H4 favorable extreme. This population is
therefore essentially the HA-9 timeout-loss population, not a mixed generic
loss set.

## 6. Failure versus recovery after a 4–8h loss

For the 734 losing add-ons:

- 24.80% later reached entry before the standard-H4 Journey exit;
- 14.71% later re-crossed the signal-H4 favorable extreme;
- only 9.54% would have ended positive at the standard-H4 exit;
- 46.19% had a better standard-H4 result than the actual timeout, but most of
  those were merely less negative;
- median best post-exit P/L from entry was still `-$5.28`.

So broad timeout removal is not supported. Most losses were genuinely poor
Children even when the Journey later survived.

The causal H1 path at timeout did separate recovery probability:

| H1 path at exit | N | Reached entry later | Re-proved later | Positive at STD-H4 exit |
| --- | ---: | ---: | ---: | ---: |
| persistent opposition | 368 | 11.41% | 7.07% | 4.89% |
| repaired | 116 | 43.10% | 25.86% | 18.10% |
| unrepaired mixed | 239 | 34.31% | 19.25% | 11.30% |

`repaired` is meaningfully less terminal than `persistent opposition`, but only
21 of 116 repaired losses became positive at the long standard-H4 exit. H1
repair is therefore a candidate for a short, executable extension test, not a
license to hold every timeout to the Journey end.

## 7. Signal morphology adds recovery information

Within the same 734 losses:

- delta contraction: 5.45% positive at standard-H4 exit versus 14.04% without
  contraction;
- opposite wick present: 4.64% versus 13.88% without it;
- wick reappearance: 0.71% positive;
- FAST-H4 opposition: 2.13% positive.

The strongest single numeric associations with eventual standard-H4 positivity
were still modest:

| Feature | Rank association |
| --- | ---: |
| signal-H4 absolute HA delta | 0.211 |
| signal-H4 body ratio | 0.180 |
| raw close position | 0.157 |
| Journey HASTOC(10) | 0.141 |
| first/second-H1 excursion or efficiency | <=0.110 |

This supports interaction/state research but not a new single-feature rule.

## 8. Fast winners are not automatically runners

The canonical sub-4h winning add-on population contains 1,460 trades and
`+$10,056.23` actual profit.

- the standard-H4 exit beat the actual exit in only 38.77%;
- only 49.18% remained positive at the standard-H4 exit;
- median standard-H4 minus actual result was `-$4.87`;
- proof in H1 #1, H1 #2 or H1 #3–4 all produced roughly 38–39% standard-H4
  outperformance;
- H4 morphology, HASTOC and early-H1 excursion had near-zero association with
  standard-H4 outperformance.

Median additional favorable movement after exit was `$18.78`, but this is a
future maximum, not an executable result. It cannot be used as evidence that
the trades should simply have been held longer. Standard-H4 is also too coarse
to serve as the sole runner label.

## 9. Preliminary mechanism probe

A diagnostic combination selected timeout losses whose H1 state was repaired
or no-opposition and whose signal H4 had neither delta contraction nor opposite
wick. It selected 44 losses; 14 became positive at the standard-H4 exit and the
selected basket improved from `-$251.05` to `+$156.66`.

This is not promoted:

- it rescues only 14 of 734 losses;
- it was composed after observing this consumed population;
- its long exit hides the path and capital-time cost;
- it has no independent validation.

It only establishes that H1 repair and H4 morphology may interact and should be
tested with predeclared, natural exit horizons.

## 10. Phase-1 conclusion

The original research direction is partly confirmed and partly narrowed:

1. The dominant remaining problem really is the no-proof 4–8h timeout-loss
   pile.
2. H1 path and H4 morphology contain recovery information, but a blanket
   timeout extension is clearly harmful.
3. Time-to-proof alone does not identify a runner.
4. Large post-exit MFE is not an executable edge.
5. The next valid step is a fixed-entry counterfactual matrix using natural H1,
   FAST-H4 and standard-H4 exits, with the timeout state frozen before each
   action.

No trading rule changes as a result of this receipt.

## 11. Reproduction artifacts

- script: `research/v13/ha9_trade_mode_phase1.py`
- complete Child feature ledger:
  `output/v13_ha9_trade_mode_phase1_20260928/trade_mode_ledger.csv`
- 4–8h loss ledger:
  `output/v13_ha9_trade_mode_phase1_20260928/loss_4_8h_ledger.csv`
- sub-4h winning ledger:
  `output/v13_ha9_trade_mode_phase1_20260928/fast_winner_under_4h_ledger.csv`
- machine-readable receipt:
  `output/v13_ha9_trade_mode_phase1_20260928/summary.json`
