# V5 Market Mechanism Ontology V1

Status: `DISCOVERY ONTOLOGY / NOT TRADE RULES`
Date: `2026-08-27`

The ontology is intentionally hierarchical.

A mechanism is not accepted because a trader named it. It is a research object with:
- causal observables;
- a falsifier;
- evidence tier;
- data requirements.

---

## M-01 — BALANCE / CONTRACTION

Concept:
Price explores a bounded region with limited net directional progress.

Possible visible expressions:
- rectangle;
- trading range;
- overlapping bars/waves;
- NR4/NR7;
- repeated boundary tests.

Causal observables:
- range compression relative to prior causal distribution;
- declining directional efficiency;
- increasing overlap;
- repeated two-sided reversals;
- lower realized directional progress per unit time.

Practitioner sources:
- Crabel;
- Brandt.

Academic status:
- volatility clustering is a strong stylized fact;
- `contraction necessarily precedes tradeable expansion` is NOT granted by that fact and must be tested.

Falsifier:
If contraction definitions do not condition future transition distributions better than ordinary state, the mechanism
has no project value.

---

## M-02 — DIRECTIONAL EXPANSION / TREND PERSISTENCE

Concept:
Once an imbalance becomes established, price may continue moving in the same direction over a nontrivial horizon.

Visible expressions:
- breakout follow-through;
- trend;
- shallow early pullbacks;
- successive directional waves.

Causal observables:
- directional efficiency;
- wave progression;
- close location;
- range/volatility expansion;
- persistence after boundary break.

Practitioner sources:
- Dennis/Eckhardt/Turtles;
- Seykota;
- Brandt;
- Raschke in outlier/momentum regimes;
- Crabel mark-up/mark-down.

Academic support:
- time-series momentum across 58 futures/forwards (Moskowitz/Ooi/Pedersen 2012);
- century-scale trend-following evidence (Hurst/Ooi/Pedersen);
- underreaction models provide one possible behavioral mechanism.

Falsifier:
If transition-conditioned continuation does not survive costs and independent markets/periods, no production authority.

---

## M-03 — REFERENCE BOUNDARY / LIQUIDITY CONCENTRATION

Concept:
Certain pre-existing prices can matter because orders, inventory, memory, or risk constraints cluster around them.

Possible boundaries:
- prior range edge;
- prior session/day high/low;
- established congestion edge;
- round price;
- confirmed swing extreme.

Practitioner sources:
- Brandt;
- Raschke;
- Crabel;
- Turtle breakout logic.

Academic support:
Carol Osler's FX order data showed:
- take-profit clustering around round numbers;
- stop-loss clustering beyond such levels;
- mechanisms consistent with reversal at a level and acceleration after crossing.

Important:
`all prior highs contain liquidity` is too broad.
V5 must measure which reference types carry information in our data.

---

## M-04 — BREAKOUT ACCEPTANCE

Concept:
Price discovery beyond a prior boundary is accepted rather than immediately rejected.

Do NOT define acceptance first as one arbitrary Boolean threshold.

First ledger quantities:
- penetration distance;
- dwell time beyond;
- fraction of closes beyond;
- maximum extension before re-entry;
- first re-entry time;
- retest depth;
- post-break directional efficiency;
- volatility expansion;
- spread/activity state.

Interpretation:
Acceptance is a continuous phenomenon first.

Practitioner sources:
- Brandt pattern completion;
- Turtles;
- Crabel breakout state.

Potential mechanism:
triggered stop flow + new directional participation + insufficient opposing liquidity.

---

## M-05 — BREAKOUT REJECTION / FAILED PRICE DISCOVERY

Concept:
Price trades beyond a pre-existing boundary but the new area is not sustained and price returns to prior value/range.

Ledger quantities:
same as M-04, viewed through re-entry/opposite response.

Practitioner sources:
- Crabel failed breakouts/liquidity runs;
- Raschke level behavior;
- classical false breakout logic.

Potential mechanism:
- stop activation creates temporary excursion;
- resting/latent opposing liquidity absorbs the move;
- marginal directional demand is exhausted;
- trapped breakout participants exit into reversal.

Do not call the mechanism `stop hunt` unless data support the order-flow statement.

---

## M-06 — EFFORT / RESULT — PRICE-IMPACT EFFICIENCY

Concept:
The information may lie not in activity alone but in how much price movement an amount of directional effort produces.

True microstructure form:
```text
price impact / signed order-flow imbalance
```

Research support:
Cont/Kukanov/Stoikov find short-horizon price changes strongly related to order-flow imbalance, with impact slope
inversely related to depth.

V5 Level-A proxy with MT5:
- tick volume = activity proxy only;
- directional price progress / activity;
- spread and causal volatility controls.

Required naming:
`EFFORT_RESULT_PROXY`

Forbidden naming without better data:
- true absorption;
- true aggressive delta;
- true OFI.

Future Level-B data:
- signed trades;
- bid/ask depth;
- cancellation/refill;
- footprint/volume delta.

---

## M-07 — EXHAUSTION / SHORTENING THRUST

Concept:
A move continues directionally but each unit of time/activity produces less new progress.

Causal observables:
- declining wave extension;
- more overlap;
- worsening progress/activity proxy;
- slower new-extreme production;
- increased failed continuation attempts.

Practitioner source:
Crabel wave character;
classical distribution/exhaustion narratives.

Status:
hypothesis; not yet independently validated for this project.

---

## M-08 — PULLBACK / RELOAD / RE-ACCUMULATION

Concept:
After directional expansion, price partially retraces. The retracement can either preserve the directional state or
transition back to balance/reversal.

Relevant observables:
- pullback depth relative to prior impulse;
- time spent retracing;
- retracement efficiency;
- volatility/activity contraction during retrace;
- boundary/retest behavior;
- subsequent re-expansion.

Practitioner sources:
Crabel;
Brandt continuation patterns;
trend-following lineage.

V3 relation:
old Module L may contain observations relevant to this mechanism but has no inherited authority.

---

## M-09 — REGIME-CONDITIONAL MEAN REVERSION VS MOMENTUM

Concept:
The same apparent overextension can be:
- fadeable in ordinary balance;
- dangerous to fade during a genuine expansion/outlier state.

Practitioner source:
Raschke;
Crabel.

Project implication:
Do not build separate mean-reversion and trend signals before a state classifier exists.

---

## M-10 — PAYOFF CONVEXITY / TRADE LIFECYCLE

Concept:
An edge may come from the distribution of outcomes, not high signal accuracy.

Practitioner evidence:
- Brandt: ~42% self-reported long-run WR, rare trades dominate profit;
- Turtles/trend followers: truncate failures, retain trends;
- Eckhardt/Basso: exits/liquidations can dominate initiation quality.

Project implication:
V5 mechanism discovery and V5 final >=50% WR target are separate.
When a mechanism candidate exists, exit architecture must be researched explicitly rather than appended afterward.

---

# V1-V3 reinterpretation map

Old variables may map into V5 observables, but not rules:

```text
M30 wave progression
-> possible M-02 trend-persistence observation

Candidate-A acceptance / penetration
-> possible crude M-04 interaction proxy

protected break / failed auction
-> possible M-05 boundary-rejection observation

H direct transfer
-> possible M-04/M-05 response/control-transfer observation

L reload
-> possible M-08 pullback/reload observation

H3 BOTH
-> possible balance/two-sided interaction observation
```

This reinterpretation does NOT rescue any failed V3 candidate.
It only prevents already-built instrumentation knowledge from being wasted.
