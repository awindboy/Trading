# V8 External Direction Research Synthesis — Structural Ceilings and State-Transition Implication

Date: `2026-09-05`  
Status: `SUPPORTING EVIDENCE / NOT PROJECT AUTHORITY`  
Production authority: `NONE`  
Market scope of V8 remains: `GOLD# ONLY`  
Untouched reserve: `GOLD# 2021`

## 1. Purpose

This document records external research that is relevant to the direction problem V8 has repeatedly encountered.

It does **not** promote any outside strategy as a V8 rule.

The purpose is to use external evidence to sharpen the V8 falsification questions:

- where short-horizon direction prediction tends to hit a structural ceiling;
- where persistence/state-transition information may survive longer;
- when apparent predictive relationships are too small to survive execution friction;
- why repeated backtest search can manufacture convincing but unstable rules.

GitHub V8/V3 code and research documents remain project authority. External literature is supporting evidence only.

## 2. Time-series momentum: persistence is different from predicting a fresh turn

Moskowitz, Ooi and Pedersen (2012), *Time Series Momentum*, Journal of Financial Economics 104(2), 228-250, DOI `10.1016/j.jfineco.2011.11.003`:

- tests 58 liquid equity-index, currency, commodity and bond futures;
- reports return persistence over roughly one to twelve months;
- reports partial reversal at longer horizons.

The useful V8 interpretation is not "HTF direction is easy."

It is:

> A directional state that has already become established can contain persistence information on an appropriate horizon, even when predicting a fresh direction change is much harder.

This supports the semantic distinction already present in V8:

    initial direction viability != winner/state continuation

Do not transplant monthly CTA rules to intraday GOLD.

## 3. Mesfin (2026): a directly relevant falsification example

Mathias Mesfin (2026), *Structural Limits of OHLCV-Based Intraday Signals in MNQ Futures: A Systematic Falsification Study*, arXiv `2605.04004`, version 2 revised 2026-07-13.

Important verified facts from the paper:

- 947 complete trading days;
- five-minute MNQ data spanning 2021-2025;
- fourteen common OHLCV-derived signal families;
- expanding-window walk-forward testing;
- next-bar-open execution after signal-bar close;
- fixed two-point round-trip friction assumption;
- pass criteria included OOS T-stat >= 2, OOS N >= 30, positive net return after friction, year consistency and permutation significance where applicable;
- none of the fourteen tested signal families passed all requirements;
- the paper reports a gross-edge range of roughly 0.07-1.50 points per trade across the failed families, generally below the assumed two-point friction.

This resembles several V8 failures:

    visible short-horizon relationship
    -> small gross directional content
    -> exact/realistic execution
    -> edge margin disappears

This is useful corroboration, not proof of a universal law.

### 3.1 Positive controls matter more than the null result

The same paper includes two separately developed positive controls to show the evaluation framework can detect an edge when one exists.

**RTH Confluence Signal** in the paper uses, on completed five-minute bars:

- a GMM regime label;
- a rolling Markov transition probability;
- a rolling volume z-score;
- ATR-adaptive pullback execution;
- exit at horizon 13 bars.

Reported paper summary includes:

- signal count 538 in the shown in-sample period;
- mean net +15.77 points at horizon 13;
- T-stat 5.83;
- WR 61.0%;
- walk-forward OOS T-stat 3.11 on 196 OOS trades.

**London Session Signal B** uses:

- a 15-minute GMM regime classifier;
- a clean transition from Regime 0 (Bearish Chop) to Regime 2 (Bullish Drift);
- no Regime 1 contamination in the prior two bars;
- next-bar-open entry;
- exit 60 minutes later or by the session cutoff.

The paper reports:

- N 289;
- mean net +5.77 points;
- T-stat 5.15;
- WR 64.7%;
- PF 2.42;
- parameter-sensitivity T-stat range remaining positive;
- a one-bar delay destroying/reversing the reported edge.

The author explicitly interprets the positive controls as regime-level information operating over a longer 12-15-bar horizon than many failed 1-6-bar signals.

### 3.2 What V8 is allowed to infer

Allowed inference:

> Static next-bar direction is not the only OHLCV research target. A clean transition into a persistent state may be materially different from predicting the next candle sign.

Not allowed:

- "GMM works";
- "Markov transition > 0.15 works";
- "hold 60-75 minutes";
- "MNQ results prove GOLD edge";
- "academic consensus says intraday OHLCV cannot work."

Mesfin is a single-author preprint on a different instrument. Its positive controls come from the author's separate research program. Treat the paper as a strong falsification reference and hypothesis generator, not external strategy authority.

## 4. Order-book microstructure: statistical predictability is not automatically retail edge

Cont, Kukanov and Stoikov, *The Price Impact of Order Book Events*, Journal of Financial Econometrics 12(1), 47-88 (2014; working-paper versions earlier), SSRN `1712822`:

- short-horizon price change is related to order-flow imbalance at the best bid/ask;
- the relationship is stronger/more robust than raw trade volume in their sample;
- price impact depends on market depth.

V8 implication:

> The direction information missing from GOLD# OHLC/quote history may exist in richer market-microstructure data, but statistical next-tick predictability and executable retail net edge are separate questions.

Do not simplify this to:

    OFI sign -> GOLD# trade

If COMEX data is acquired later, use it first as a scenario-meaning resolver, e.g. confirming flow versus absorption/divergence during an already-defined transition.

## 5. Data-snooping and technical-rule research

Park and Irwin (2007), *What Do We Know About the Profitability of Technical Analysis?*, Journal of Economic Surveys, DOI `10.1111/j.1467-6419.2007.00519.x`:

- reviews a large technical-trading literature;
- finds positive, mixed and negative historical evidence;
- explicitly warns about data snooping, ex-post rule selection, risk measurement and transaction-cost estimation.

White (2000), *A Reality Check for Data Snooping*, Econometrica 68(5), 1097-1126, DOI `10.1111/1468-0262.00152`:

- formalizes the danger of reusing the same time series for repeated specification search;
- tests whether the best model encountered in a search truly has predictive superiority over a benchmark.

V8 implication:

> The more thresholds, vetoes, score variants and scenario exceptions we try on the same years, the less impressive the winning backtest should become to us.

This is already demonstrated internally by V3 discovery-to-validation failure.

## 6. Updated V8 direction hypothesis

Prior working suspicion:

    price-only current-state direction may be too weak;
    perhaps only external information can break the ceiling.

Updated hypothesis after combining V8 evidence and the external falsification literature:

    A. Current-state -> next-bar / next-short-distance direction remains a low-priority target.

    B. Price-only information is NOT declared exhausted.
       A different target may remain learnable:

           disturbance / movement ignition
           -> state transition
           -> persistent directional state
           -> economically meaningful continuation horizon

    C. External information remains an independent information-expanding lane:

           macro surprise / COMEX flow / options context

The project must test B before assuming only C can work.

## 7. Why this is not a return to generic regime classification

The next research is NOT:

    fit K clusters
    -> name one bullish
    -> enter when cluster == bullish

The object of study is the **transition** and its persistence:

    pre-event state
    -> P15 movement disturbance
    -> transition path
    -> post-event state
    -> persistence / failure

The state label itself has no trading authority.

Any unsupervised representation must demonstrate semantic stability across time and parameter perturbations and must add information beyond existing Late Ignition / BB Persistence / Macro modules.

## 8. Connection to current V8 modules

The three current promising causes can already be interpreted as transition processes:

### Endogenous Late Ignition

    relative stagnation
    -> sudden activity/displacement state

### BB Persistent Expansion + HTF ownership

    expansion outside prior envelope
    -> continued acceptance/persistence

### Scheduled Macro

    pre-release state
    -> exogenous information shock
    -> post-release reaction state

This raises a new research question:

> Are the current modules isolated patterns, or are they manifestations of a more general causal state-transition/persistence architecture?

Do not answer this by merging their rules. Measure it.

## 9. Permanent caution about horizon

The Mesfin positive controls use longer holding windows than many failed short-horizon signals.

Do NOT infer:

    longer TP/horizon -> better strategy

The required order is:

1. demonstrate a persistent post-transition state;
2. determine the distance/time scale over which the state remains informative;
3. only then design payoff/execution.

Extending a runner merely to improve average winner remains prohibited.

## 10. Research consequence

The immediate next V8 primary research lane becomes:

`P15-CENTERED CAUSAL STATE-TRANSITION & PERSISTENCE AUDIT`

Directional Change remains a completed negative broad-direction audit and may be retained only as shadow representation.

Macro surprise remains the primary information-expanding parallel lane.

GOLD# 2021 remains untouched.
