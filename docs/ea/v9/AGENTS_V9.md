# V9 Research Instructions

Status: `ACTIVE / HUMAN-LIKE CHART REPLAY + DECISION CORRIDOR + DISCRETIONARY PAPER-TRADING RESEARCH`  
Generation: `V9`  
Last synchronized: `2026-09-07`  
Production authority: `NONE`  
EA authority: `NONE`  
Market: `GOLD# ONLY`  
Untouched final temporal reserve: `GOLD# 2021`  
V8 predecessor Git HEAD: `14e67d26ef1a896a37e52a64dfedbbf1b1bba913`

## 1. Why V9 exists

V9 is not a declaration that V1-V8 were irrational, meaningless, or simply wrong.

The previous generations investigated many theoretically coherent market ideas:

- deterministic market structure;
- liquidity / OB / FVG / sweep / CHoCH;
- higher-timeframe delivery and auction state;
- local acceptance / failure;
- entry survival;
- winner continuation;
- exit architecture;
- AI-native context representations;
- Double-B / KTR;
- H/L scenario families;
- P15 movement probability;
- grid and deep-adverse campaign management;
- scenario portfolios;
- Directional Change;
- price-only state transition / persistence;
- scheduled macro events.

Several of these produced genuine research findings and some produced positive development economics.

The reason for a new version is deeper.

Repeated testing showed that no representation studied so far gives the project a reliable right to know future GOLD direction with high precision.

This does not mean:

- markets are random;
- structure is useless;
- every previous version was wrong;
- direction contains no information.

It means three problems must be permanently separated:

```text
understanding the market
!=
predicting future direction
!=
making a good trade
```
V9 changes the primary research target from:

> How can direction be predicted more accurately?

to:

> Given incomplete market knowledge, can we identify situations where being wrong becomes observable relatively nearby while being right leaves a materially larger structural route?

This is `decision sufficiency`, not omniscience.

---

## 2. Permanent V9 principle

A good trade does not require:

* the ultimate market direction;
* the final top or bottom;
* a complete causal model of every price move;
* identification of the exact institutional actor;
* certainty;
* a complete map of every historical swing or node.

A V9 trade requires enough causal information to answer:

1. What current route or local thesis is being traded?
2. What observable market behavior would make that thesis wrong?
3. If the thesis survives, where is the next meaningful place to reassess?
4. Is the asymmetry between falsification and available structural route attractive enough?

The project is allowed to say:

```text
I do not know what GOLD ultimately does.
I know enough about this local decision to trade or not trade.
```

---

## 3. Authority and resume order

GitHub is the project's permanent memory.

ChatGPT conversation is the workbench.

Every new V9 session must:

1. refresh Git HEAD;
2. read `docs/ea/v9/AGENTS_V9.md`;
3. read `docs/ea/v9/HANDOFF_V9.md`;
4. read `docs/ea/v9/RESEARCH_STATE_V9.md`;
5. read `docs/ea/v9/V9_MANUAL_CHART_REPLAY_MARKET_MEMORY_AND_DECISIONS_20260907.md`;
6. read `docs/ea/v9/DECISIONS_V9.md`;
7. read the V9 paper-trading journal;
8. use V8/V3 documents as preserved upstream research evidence and controls;
9. never let conversation memory override newer GitHub state.

V8 remains research history and evidence authority for its own experiments.

V9 supersedes V8 only as the active research direction.

---

## 4. Market and data authority

Scope:

```text
GOLD# ONLY
```

Authoritative M1 source used in late V8/V9:

```text
GOLD#_M1_202201030100_202608282357.csv
SHA256:
626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2
```

Data boundaries:

* 2024 exact Bid/Ask tick data exists and is development execution evidence.
* Known active tick gaps are censored when M1 proves the market traded through the gap.
* 2025 exact tick is unavailable. Treat it as absent.
* 2025 and 2026 M1 may be used for descriptive/replay research.
* M1 is not exact execution authority where intrabar chronology matters.
* GOLD# 2021 remains untouched final temporal reserve.

Do not silently convert M1 replay economics into spread/slippage-adjusted strategy claims.

---

## 5. V9 does not begin with code

Required order:

```text
manual chart replay
-> historical archaeology
-> matched success/failure comparisons
-> counterexamples
-> revised market language
-> blind/sequential replay
-> discretionary paper trading
-> trade journal
-> stable decision rubric
-> only then formalization
-> only then code / shadow instrumentation
-> only then EA / exact execution
```

Do not answer every market idea by immediately building:

* an indicator;
* a classifier;
* a score;
* a threshold;
* a veto;
* an entry gate;
* an EA;
* a P/L tournament.

Early code may only assist with:

* retrieving dates;
* aggregating M1 into chart timeframes;
* rendering charts;
* hiding future data;
* indexing episodes;
* chronology.

Fixed-N retrieval screens are retrieval tools, not market definitions.

---

## 6. Human-like adaptive resolution

Humans do not necessarily inspect a fixed number of bars.

If meaningful history is too far away on M5, change resolution:

```text
M5
-> M15
-> H1
-> H4
-> D1
```

Higher timeframe is not merely another trend filter.

It is historical compression.

The correct question is not:

> What happened in the last 100 / 240 / 1000 bars?

It is:

> How far back, and at what resolution, must I look to understand the history still relevant to current price?

Do not freeze V9 into a single timeframe.

---

## 7. Sparse active memory

The conceptual `Market Memory Graph` remains useful:

```text
accepted regions = nodes
directional journeys = edges
```

But do not build an exhaustive graph of every swing.

That recreates AI-style over-modeling.

For a current trade decision, the trader usually needs only a sparse set of active memories:

* current child structure;
* relevant parent structure;
* the area whose restoration would falsify the current route thesis;
* the next meaningful destination.

Everything else can remain ignored until relevant.

---

## 8. Core chart vocabulary

These are reasoning tools.

They are not frozen algorithmic states.

### Candidate area

A temporary staging / two-way area that may later become important.

A pause is not automatically a node.

### Accepted region / node

An area that has demonstrated meaningful two-way business and/or supported a subsequent route.

Balance does not mean low volatility or narrow compression.

A wide multi-week range can be a major accepted region.

### Launch memory

A prior candidate area may gain structural meaning after a later causally observed departure materially changes the route.

This is not look-ahead if the trader waits until the departure has already happened before granting the old area authority.

### Active memory

A historical area that still has functional relevance to the current route.

### Consumed / merged memory

A former structure whose old function has been sufficiently reaccepted/traded through that it no longer governs the current decision.

### Parent / child structure

Market structures are hierarchical.

A local H1/M5 child can exist inside an H4/D1 parent journey.

### Journey / edge / route

Directional translation between relevant memories.

### Departure / transit / arrival

The same local chart pattern can have different meaning according to where it occurs in the larger journey.

### Destination

The next meaningful active memory where the current trade question should be reassessed.

Destination does not imply automatic reversal.

### Reaction

Opposite-direction movement occurred.

### Rejection

The tested side failed functionally enough to change the route interpretation.

Therefore:

```text
reaction != rejection
```

### Settlement ladder

Track where the market repeatedly forms temporary accepted centers after disturbance.

Example recovery:

```text
4100 -> 4120 -> 4140 -> 4170
```

Example bearish migration:

```text
4420 -> 4408 -> 4395 -> 4380
```

The migration of centers can matter more than the original shock candle.

### Structural scar

A meaningful counterflow can damage child structure and create new endogenous memory, especially during price discovery where no historical resistance exists.

Scar presence is not reversal authority.

### Repair

The market attempts to restore a prior active structure to its old functional role.

### Failed repair

A repair attempt occurs but does not restore the old role.

This may support route switching.

Do not reduce it to generic `break + retest`.

### Bridge length / structural room

The usable route between the current decision and the next active memory.

Do not freeze this into a fixed ATR or R value yet.

---

## 9. Role > Pattern

Permanent V9 lesson:

> The role of a visible event inside the larger market episode matters more than the pattern name itself.

The same:

* breakout;
* sweep;
* reclaim;
* displacement;
* rejection candle;
* FVG;
* OB;
* Bollinger event;
* P15 ignition;

may represent different things in:

* young departure;
* active transit;
* parent arrival;
* failed repair;
* already-consumed structure.

These objects may be useful execution vocabulary.

They have no standalone trade authority.

---

## 10. Origin -> Journey -> Destination

Early V9 replay found the useful narrative:

```text
Origin
-> Journey
-> Destination
```

But replay also falsified the simplification:

```text
destination -> reversal
```

A destination can be:

* defended;
* temporarily reacted from;
* consumed;
* merged into a new node;
* converted into a new origin.

Episode age also does not automatically imply reversal.

A mature route can accelerate before finally failing.

Therefore the more general model is hierarchical route switching.

---

## 11. Hierarchical route switching

Conceptual example:

```text
Parent Node A
      |
      | edge
      v
Child Node B
      |
      | edge
      v
Child Node C
```

If C survives, the local route can continue.

If C fails:

```text
C -> B
```

may become the active route.

When B is reached, the C->B trade thesis is normally resolved.

Then B is reassessed.

If B subsequently fails:

```text
B -> A
```

may become a new trade question.

This means a large winner may emerge as:

```text
bridge 1
-> reassess
-> bridge 2
-> reassess
-> bridge 3
```

rather than an initial prediction of +5R.

---

## 12. Node importance is functional

Do not decide importance solely from:

* touch count;
* candle count;
* duration;
* visual prominence;
* swing labels;
* tick activity.

Ask instead:

> Which already-known market-memory area, if genuinely restored, would demonstrate that my current route interpretation has failed?

This is `counterfactual thesis dependence`.

Node relevance is thesis-relative.

---

## 13. Node birth is a process

Blind replay rejected:

```text
pause + first departure = node
```

A better conceptual process is:

```text
candidate area
-> departure
-> departure creates meaningful separation / journey
-> prior area earns launch-memory authority
-> later revisit tests whether its role survives
```

Do not predict every important node at birth.

Authority can be earned through subsequent causally known behavior.

---

## 14. Node failure is a process

Do not equate:

```text
wick through
```

or:

```text
one close through
```

with definitive failure.

Observed route-switch styles include:

### Gradual role inversion

```text
penetration
-> value forms beyond prior node
-> repair attempt
-> old role not restored
-> new departure
```

### Abrupt multi-node traversal

Strong movement crosses several nested child structures too quickly for a textbook retest.

Do not require the same candle sequence in every valid transition.

---

## 15. Direction correctness != trade quality

A directionally correct thesis can be a poor trade.

Example conceptually:

```text
current price
↓
next active memory very close
```

There may be little structural room even when direction is correctly read.

The opposite can also occur:

```text
falsification relatively nearby
+
next active memory far enough away
```

The directional probability need not be extraordinary for the trade to be attractive.

Therefore V9 first asks:

```text
TRADEABLE?
```

not:

```text
HOW CERTAIN AM I ABOUT DIRECTION?
```

---

## 16. Decision Corridor

Current practical V9 object:

```text
       Falsification Anchor
               ^
               |
          Current Price
               |
               | open structural route
               |
               v
       Next Active Memory
```

A candidate becomes tradeable when:

1. the falsification anchor is causally observable;
2. genuine recovery of that anchor would weaken/kill the thesis;
3. sufficient evidence exists that the opposite route is currently open;
4. the next meaningful memory is materially farther away;
5. the asymmetry is attractive enough despite uncertainty.

---

## 17. Decision sufficiency

Do not explain the market forever.

Once enough is known:

```text
falsification = A
current market fails to restore A
next meaningful destination = B
risk toward A is materially smaller than available route toward B
```

freeze the thesis.

Do not continue adding narrative merely because more explanation is possible.

This is both a practical principle and a hindsight-storytelling guardrail.

---

## 18. Trader states

These are states of the decision maker, not objective market regimes.

### OBSERVE

No sufficient route/asymmetry.

### ARMED

A meaningful junction exists but required evidence has not occurred.

### TRADEABLE

A usable Decision Corridor exists.

### RESOLVED

Destination reached or falsification occurred.

Restart the market read.

`NO TRADE` and `NOT YET` are legitimate successful decisions.

---

## 19. Entry protocol

Before every discretionary paper entry record:

```text
decision time
LONG / SHORT
parent context
current child route
falsification anchor
first natural destination
why route is open
why asymmetry is sufficient
what remains uncertain
```

Entry is the final output of analysis.

It is not the starting point of V9 research.

---

## 20. Trade management

Manage the market thesis, not unrealized P/L.

Do not automatically:

* move to BE at +1R;
* take partial at a fixed R;
* exit after 30/60 minutes;
* hold to +2R/+3R to improve statistics.

Ask:

```text
Has falsification occurred?
Has the first natural destination been reached?
Has the relevant market structure changed?
```

At the first natural destination, the original thesis normally becomes `RESOLVED`.

Reassess from there.

A further route requires new causal justification.

---

## 21. V9 evidence classes

### Outcome-informed archaeology

Future deliberately visible.

Used to learn market language and find counterexamples.

Never validation.

### Blind snapshot replay

Everything after t0 hidden.

Interpretation written before future reveal.

### Sequential replay

Future revealed incrementally, e.g.:

```text
t0
-> +1h
-> +4h
-> +1d
```

Belief updates are recorded.

### Paper-trading replay

Actual discretionary entry/manage/exit using only revealed information.

Then a trader-style journal is written.

Do not mix the authority of these evidence classes.

---

## 22. Contamination rule

By V9 start, many 2024-2026 dates had already been viewed through:

* archaeology;
* blind montages;
* sequential replay;
* existing V8 strategy outputs;
* matched-pair analysis.

Therefore 2026 is consumed qualitative/development evidence.

Do not call the full 2026 year a clean blind OOS sample.

A locally future-hidden paper trade can still test process.

It cannot by itself establish untouched annual performance.

Also:

> Later same-direction movement cannot rescue a thesis after an opposing structure/reset already resolved the original episode.

---

## 23. V8 bridge that must remain preserved

V8 2024 exact scenario portfolio:

```text
unique candidates 96
completed         89
censored           7
wins              49
losses            40
WR             55.06%
mean           +0.1049R
total          +9.339R
PF              1.262
avg positive   +0.9168R
avg negative   -0.8896R
```

Interpretation:

* positive development evidence;
* improved frequency versus strict V3;
* still a relatively weak edge;
* average winner did not satisfy the desired final property;
* no independent exact-tick validation.

Do not rewrite this as failure or success.

It is an important benchmark.

Directional Change broad direction:

```text
outside existing modules:
2024 ~49.8%
2025 ~54.2%
2026 ~48.2%
```

Conclusion:

```text
stable representation != stable directional information
```

Generic P15 price-only state transition likewise did not yield a stable universal direction resolver across later periods.

Macro calendar remains information-expanding for movement, but generic release-M5-body direction did not remain stable.

---

## 24. Final strategy objectives remain

V9 does not lower the economic bar.

Final strategy still seeks:

* realized WR >= 50%;
* average winner meaningfully > 1R;
* positive cost-adjusted expectancy;
* acceptable drawdown and loss streak;
* adequate trade frequency;
* robustness across independent evidence;
* no denominator manipulation;
* no validation rescue by threshold changes.

The new hypothesis is that structural asymmetry plus good no-trade decisions may produce better payoff geometry than trying to predict every movement more accurately.

---

## 25. Stop rules

Do not:

* prematurely automate V9 vocabulary;
* threshold-mine node definitions;
* invent `N bars = node`;
* invent `X ATR = meaningful departure` from a few cases;
* map every historical swing;
* treat every sweep/FVG/OB as relevant;
* treat reaction as rejection;
* treat destination as reversal authority;
* demand complete market explanation;
* claim causal actor/mechanism without evidence;
* hold beyond a resolved destination merely to manufacture larger R;
* use M1 as exact execution authority;
* call 2026 untouched blind validation;
* use GOLD# 2021.

---

## 26. Immediate active research

Continue:

```text
future-hidden chart replay
-> TRADE / NO TRADE / NOT YET
-> Decision Corridor
-> discretionary entry/manage/exit
-> journal
-> self-falsification
```

The next important evidence is not another indicator score.

It is whether the V9 decision process repeatedly produces sensible trades and sensible refusals under hidden future data.

---

## 27. Production status

`NONE`

No V9 EA or production strategy exists.