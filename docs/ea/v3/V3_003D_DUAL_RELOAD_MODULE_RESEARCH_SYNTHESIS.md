# V3-003D — GOLD Reload Dual-Module Research Synthesis

Status: `DISCOVERY SYNTHESIS / SESSION HANDOFF / NO STRATEGY AUTHORITY`  
Date: `2026-08-26`  
Repository authority at synthesis start: `66184400986387cb571a9be1e7ed18c1e740cad0`  
Market: `GOLD# ONLY`  
Environment: `XM Ultra Low / XMGlobal-MT5 7`  
Discovery data: `2023-2025 M1`  
Validation vault: `2022 — CLOSED`  
Untouched: `2021`

## 0. Why this document exists

This document is a **continuation contract for future sessions**.

A future session must not reconstruct the current research from chat memory and must not
repeat already-falsified branches merely because they look intuitive.

The current V3 reload research has reached a point where two distinct payoff/entry modules
should be investigated **in parallel**:

```text
MODULE L — LOW-R / HIGH-WR
    prioritize very rare actual losses and frequent positive exits

MODULE H — HIGH-R / LOW-WR
    tolerate more losses only if winners are structurally large, approximately 5R+
```

The user explicitly wants both branches preserved. They are not competing variants where
one must eliminate the other. Their failure mechanisms, Entry authorities and payoff
architectures must remain separable so they can later be improved independently.

Do **not** begin other auction-state modules (compression breakout, failed-auction reversal,
etc.) while this dual reload research still has unresolved high-value work. Those modules
remain deferred until the current reload research either:

1. reaches a materially stronger coherent architecture; or
2. reaches a documented structural ceiling.

## 1. Reproducibility authority boundary

There are two different evidence levels in this document.

### 1.1 Committed reproducible authority

`V3_RELOAD_CANDIDATE_A` is already reproducibly documented by:

```text
V3_003C_RELOAD_STATE_ACCEPTANCE_RESULTS.md
research/ea/v3/v3_003c_reload_state_acceptance_probe.py
```

Reference Level-A population:

```text
2023 40 / +1R 60.0%
2024 29 / +1R 65.5%
2025 27 / +1R 63.0%
```

This remains the frozen development benchmark.

### 1.2 Current-session discovery evidence

The Module L / Module H findings below were produced from the same accepted GOLD raw data
during the 2026-08-26 research session, but the dedicated final scripts and immutable event
ledgers for these later experiments are **not yet committed**.

Therefore:

```text
numbers below = high-priority discovery evidence
numbers below != GitHub strategy authority
```

The next session must first create a reproducibility pack that independently regenerates the
Module L and Module H ledgers before adding new filters or promoting either module.

Do not tune new conditions merely to reproduce the headline numbers.

## 2. Common factual base — Candidate A

Candidate A remains:

```text
causally known intermediate persistent liquidity
-> M1 penetration + same-M1 close recovery
-> pre-sweep M5 owner opposite the reaction direction
-> DELIVERY_ACTIVE at sweep
-> first M5 owner transition back with reaction
-> acceptance_margin > source_penetration
-> trigger-close reference Entry
-> sweep-extreme reference SL
```

Reference `DELIVERY_ACTIVE` in V3-003C:

```text
M30 expansion ratio > 1.0
OR
M30 and H1 BOS-owner both agree with reaction direction
```

Important reinterpretation from later research:

- Candidate A is best treated as a **local reaction / timing benchmark**.
- It must not be called a proven strategic-destination engine.
- `M30 expansion > 1` is directionless by itself; it can describe renewed movement without
  identifying which side owns a large future delivery.
- static HTF state variables tested later did not reliably predict large delivery across all
  three discovery years.

Do not rewrite Candidate A while Module L / H are investigated.

## 3. R is one coordinate, not the definition of a meaningful trade

Later research showed that `+1R before SL` alone can hide the actual economic/market scale.

Reference Candidate-A Entry-to-SL risk distribution was approximately:

```text
minimum         $1.63
25th percentile $3.90
median          $5.73
75th percentile $8.66
90th percentile $14.32
95th percentile $18.28
maximum         $32.15
```

A small-risk trade can reach +1R while capturing only a few dollars of GOLD movement.
A wide-risk trade can make a meaningful $10+ move and still fail to reach +1R.

Therefore every future Module L / H experiment must report at minimum:

```text
MFE / MAE in dollars
MFE / MAE in R
MFE / MAE in M30 ATR units
MFE / MAE in D1 ATR units
time to checkpoint / target / adverse excursion
Entry-to-SL dollars
spread / risk
holding time
scenario / context invalidation timing
```

Do not replace R. Demote it from a single master label to one economic coordinate.

A particularly important discovery was that `risk / D1 ATR` was highly correlated with the
actual `swept-liquidity -> trigger-close displacement / D1 ATR` (rank correlation roughly
0.95–0.99 by year). This does **not** authorize a risk-width filter. It means risk was acting
as a proxy for setup/reaction scale.

Future work should measure reaction/displacement scale directly rather than saying
"wide SL is good".

## 4. Trade-density / strictness census

The low trade count is real, but the research showed where it comes from.

Reference M15 `k=2` approximate annual funnel:

| Stage | 2023 | 2024 | 2025 |
| --- | ---: | ---: | ---: |
| M15 source swings | 1,870 | 1,915 | 1,821 |
| atomic liquidity reactions | 820 | 834 | 733 |
| physical sweep dedupe | 777 | 796 | 706 |
| compatible pre-sweep M5 owner | 660 | 680 | 626 |
| M5 re-acceptance before fresh extreme | 84 | 86 | 67 |
| delivery state | 56 | 44 | 41 |
| strong acceptance | 59 | 58 | 43 |
| Candidate A | 40 | 29 | 27 |

The main compression is the **M5 correction-completion / re-acceptance event**, not a long
list of minor vetoes.

This strictness was not free, but natural attempts to relax it usually destroyed quality:

```text
first M1 owner transition instead of M5:
    roughly 188 / 163 / 131 trades
    +1R roughly 40.4 / 50.3 / 41.2%

delayed recovery after body delivery through liquidity:
    much higher frequency
    materially weaker / unstable outcomes

lower-prominence k=1.5-only additions:
    2023 +1R ~44.4%
    2024 +1R ~58.3%
    2025 +1R ~40.0%
```

Therefore do not reopen the "just loosen the rules to get more trades" branch unless a new
causal mechanism is proposed.

### Market scarcity is not the explanation

GOLD itself produces many large-movement days.

Approximate counts:

```text
daily range >= 1.25 prior D1 ATR:
2023 55 days
2024 60
2025 65

|daily close-open| >= 0.5 prior D1 ATR:
2023 87 days
2024 110
2025 113
```

Candidate A covers only a small fraction of those days.

Conclusion:

> Reload continuation is a narrow specialist module. GOLD is not short of movement.

Per user instruction, do **not** solve this yet by moving to compression/reversal modules.
First finish the current Module L / H research.

## 5. Same-bar atomic recovery is currently meaningful

Do not collapse:

```text
penetration -> same-bar rejection/recovery
```

and:

```text
body delivery through liquidity -> delayed later recovery
```

into one sweep class.

In prior-loss requalification research, the reference delayed-recovery negative control was
approximately:

```text
N=7
+1R ~14.3%
+2R ~14.3%
```

while atomic deeper requalification was far stronger.

Likewise, a generic control:

```text
prior SL
-> correction trades deeper
-> first same-direction M5 transition
```

was weak (roughly +1R 31.8%, +2R 22.7% in the reference census).

In directly comparable episodes, the generic M5 re-acceptance often occurred first and
failed; waiting for a **new deeper intermediate-liquidity atomic sweep/recovery** before the
fresh transition materially improved the result.

Current interpretation:

> liquidity consumption appears to be part of correction-completion information, not merely
> decorative ICT vocabulary.

This still requires reproducible event-ledger confirmation before authority.

# PART I — MODULE L: LOW-R / HIGH-WR

## 6. Module L research purpose

Module L should not merely manufacture a high win rate by closing everything at a tiny
fraction of R.

Its target is:

```text
actual SL becomes exceptional
+
positive exits are frequent
+
the trade still captures a nontrivial market move
+
mirror / naive controls remain much weaker
```

The most promising architecture is **shadow-probe then requalification**, not "make
Candidate A TP smaller".

## 7. Module L primary discovery architecture

Candidate A is initially treated as a **virtual probe**, not an actual order.

```text
Candidate A appears
-> track virtual trigger-close Entry and virtual sweep-extreme SL

if virtual trade does NOT fail:
    no Module-L real trade from this failure path

if virtual SL occurs
AND higher context remains alive:
    correction may still be incomplete

wait for:
    deeper intermediate liquidity
    -> atomic same-bar penetration + recovery
    -> fresh same-direction M5 re-acceptance

then:
    first real Module-L Entry
```

Important:

- the first Candidate-A loss is **not paid with real capital** in this Module-L design;
- the failed virtual probe is treated as information;
- the later real Entry is a distinct authorization problem;
- generic M5 re-acceptance without the fresh deeper liquidity event is not sufficient.

## 8. Module L current discovery result

After physically deduplicating overlapping natural M15 intermediate-prominence detections
(`k≈1.5/2.0/2.5`), the current scratch research found approximately:

```text
10 independent episodes
11 real deep-requalification trades

checkpoint = min(1R, 0.5 D1 ATR)

checkpoint before SL: 11 / 11
full +1R before SL:   10 / 11
exact-mirror checkpoint: ~1 / 11
```

Average realized checkpoint was approximately `0.98R`.

This is highly promising but **far too small a sample** to describe as a 100% strategy.

The Wilson lower confidence boundary remains much lower than 100%.

### Source-family boundary

Important negative evidence:

- noisy M15 `k=1.0` additions materially weakened precision;
- M30 deep-requalification did not reproduce the M15 result;
- M15 mentor-wave source produced only a few examples and was directionally promising but
  insufficient.

Therefore:

```text
DEEP_RELOAD_REQUALIFICATION
!= universal liquidity law
```

Current hypothesis is specifically tied to **intermediate M15-scale correction/liquidity
lifecycle** until broader semantics are proven.

## 9. Module L naive high-volume controls

### 9.1 clean-M1 Candidate A -> 0.5R full TP

Reference scratch result:

```text
2023 26 trades / ~76.9%
2024 18 / ~83.3%
2025 17 / ~100%
pooled ~85.2%
```

But actual median target movement was only a few dollars and the 2023 mirror remained
relatively high.

Use this only as a **naive high-WR control**, not as the preferred Module-L architecture.

### 9.2 clean-M1 Candidate A -> 0.75R full TP

Reference scratch result:

```text
2023 ~73.1%
2024 ~77.8%
2025 ~82.4%
```

with clearer separation from exact mirrors than the 0.5R control.

This is a useful secondary benchmark because it trades more often than deep
requalification, but it remains a payoff shortcut rather than a demonstrated
correction-completion engine.

Do not optimize 0.55R / 0.65R / 0.8R etc. from discovery P/L.

## 10. Module L next research contract

P0 work:

1. **Reproduce the Module-L ledger in a committed script.**
   - physical event dedupe;
   - virtual Candidate-A failure;
   - context-alive test;
   - deeper-liquidity definition;
   - atomic sweep/recovery;
   - fresh M5 transition;
   - executable-side barriers.

2. **Expand sample without relaxing the mechanism.**
   - M15 adaptive intermediate family;
   - M15 mentor-wave family as an independent semantic detector;
   - dedupe by physical requalification, not detector label;
   - do not add k=1.0-only noise simply to increase count.

3. **Build negative controls in the same script.**
   - generic deeper correction + first M5 transition;
   - delayed recovery;
   - exact mirror;
   - low-prominence-only source.

4. **Failure taxonomy for the rare Module-L losses.**
   - did atomic rejection fail?
   - did context die?
   - was fresh transition premature?
   - was execution friction material?
   - was the source actually a duplicate / low-prominence event?

5. **Economic checkpoint study.**
   Keep the current controls:
   - `min(1R, 0.5 D1 ATR)`;
   - full `1R`;
   - naive `0.75R`.
   Do not grid-search arbitrary R values.

6. **Do not convert virtual first failure into a real -1R trade** simply to make more
   episodes. The point of Module L is to exploit failure information without paying for the
   first probe.

Promotion is forbidden until sample size and independent semantic-source evidence improve.

# PART II — MODULE H: HIGH-R / LOW-WR

## 11. Module H research purpose

Module H accepts a lower win rate only if it captures genuinely large GOLD movement.

Target character:

```text
roughly several -1R losses
-> one structurally large winner
-> approximately +5R or more
```

The strategy must not create fake high R merely by placing an arbitrary tiny SL.

The same sweep-extreme scenario invalidation remains the risk anchor.

## 12. clean M1 path has a different role here

`clean M1 ownership path` was not stable enough to promote as a general Candidate-A Entry
filter.

However, after separating research stages, it became much more consistent as a
**winner-continuation / high-R eligibility fact**.

Working meaning:

```text
after sweep:
M1 ownership transfers with delivery
-> no opposite M1 owner flip before the M5 trigger
```

Across natural M15 source scales, clean paths showed better +2R/+3R continuation than
non-clean paths in the current discovery work.

Do not automatically move this variable back into Module L.

## 13. Module H Entry geometry

Applying a pullback Entry to every Candidate A failed, including weak 2025 behavior.

The useful population was:

```text
Candidate A
+
clean M1 ownership path
+
post-trigger structural pullback
```

SL remains the same original sweep extreme.

Two important controls:

### Control H0 — broken M5 structure retest

```text
wait after trigger
-> first retest of the exact M5 structure level that was broken
-> limit Entry
-> same sweep-extreme SL
```

Reference scratch result before later midpoint improvement:

```text
46 fills
12 x +5R
34 x -1R
EV ~+0.565R/trade
```

### Candidate H1 — acceptance-leg 50% pullback

Define the already-known acceptance leg:

```text
broken M5 structure level <-> trigger close
```

and wait for the first 50% retracement.

Reference scratch result:

```text
48 fills
14 x +5R
34 x -1R
EV ~+0.75R/trade before BE management
```

Relative to broken-level control, the discovery sample added two +5R winners without adding
losses.

Important boundary:

`50%` is **not frozen strategy authority**. It was one of the natural
25/50/75/100%-of-acceptance-leg variants examined in discovery. Broken-level H0 must remain
the simple control until independent reproducibility and sensitivity checks are complete.

## 14. Module H actual move size

The 5R winners were not merely tiny-dollar high-R artifacts.

For the reference midpoint research, winner target medians were approximately:

```text
2023 ~$23.6
2024 ~$23.6
2025 ~$37.7
```

and roughly:

```text
2023 ~1.16 D1 ATR
2024 ~0.71 D1 ATR
2025 ~0.83 D1 ATR
```

Median time to +5R was roughly:

```text
2023 ~4.6 h
2024 ~13.1 h
2025 ~15.0 h
```

This is much more consistent with the intended high-R / meaningful-GOLD-move module than
the prior 0.5R/1R-style payoff work.

## 15. Module H exact-mirror evidence

For the reference 50% pullback discovery run, same fill time / same risk / opposite
direction exact mirrors were materially weaker:

```text
2023 original 5R ~21.7% vs mirror ~8.7%
2024 ~35.7% vs 0%
2025 ~36.4% vs 0%
```

This reduces the probability that the tail is merely symmetric GOLD volatility.

Reproduce this in the committed Module-H script before treating the numbers as authority.

## 16. Module H profit protection

### +1R -> BE

Rejected for Module H.

It cut genuine later +5R winners.

### +2R -> BE

Also rejected / inferior.

It cut genuine later +5R winners.

### +3R -> BE

Promising.

In the current scratch source-sensitivity panel (`k≈1.5/2.0/2.5 x 2023/24/25`), moving the
residual stop to BE only after +3R did **not remove any existing +5R winner**.

Reference midpoint result became approximately:

```text
48 trades
14 x +5R
31 x -1R
3 x BE
total +39R
EV ~+0.8125R/trade
```

This is currently the preferred **profit-protection research control**, not authority.

### +3R -> 25% harvest + residual BE -> residual 5R

Secondary control using the already-established 25% SP fraction rather than a newly
optimized percentage.

A final target winner realizes:

```text
0.25 * 3R + 0.75 * 5R = 4.5R
```

A trade that reaches +3R but later fails to reach +5R can still realize `+0.75R`.

This increases positive-trade frequency while preserving a large average positive trade.
Keep it separate from the raw-max-expectancy full-5R control.

Do not optimize the partial fraction from this discovery panel.

## 17. Module H rejected exit ideas

Do not repeat these without new causal evidence:

```text
M1 owner-flip trailing exit
M5 structure reacceptance exit
M5/M15 structural trailing
+1R BE for 5R runner
+2R BE for 5R runner
repeated integer-R partial harvesting
```

They generally cut genuine large winners too early.

## 18. Module H 10R branch

Raw 10R barrier results looked attractive in some subsets, but they are **not** the current
primary architecture.

Problems:

- 2024/2025 median time to 10R could exceed four to five days;
- fixed 10R was sensitive to how scenario lifetime / invalidation was defined;
- counting a later 10R touch after the original thesis should have died is not acceptable;
- holding-cost / overnight / exposure semantics become important.

Therefore:

```text
5R = current high-R research target/control
10R = deferred extension only
```

Do not present 10R as solved strategic-objective delivery.

## 19. Module H next research contract

P0 work:

1. **Commit exact H0 / H1 event ledgers.**
   - Candidate A identity;
   - clean M1 path;
   - trigger time;
   - acceptance leg;
   - pullback pending time;
   - fill;
   - sweep-extreme SL;
   - +3R / +5R path;
   - exact mirror.

2. **Keep H0 broken-level retest as simple control.**
   H1 midpoint must beat it without relying on one year or one source scale.

3. **2023 loss-streak / failure taxonomy.**
   The current high-R control still showed a long 2023 losing streak.
   Do not create a 2023-specific veto.
   Determine whether losses share a cross-year mechanism:
   - false acceptance;
   - pullback too deep / too late;
   - correction resumed;
   - scenario premise already stale;
   - execution-sensitive fill;
   - source-family ambiguity.

4. **Verify +3R BE non-interference with +5R winners.**
   Re-run from a dedicated reproducible ledger.

5. **Keep +3R 25% harvest only as a secondary robustness / positive-frequency variant.**

6. **Measure actual dollars / D1 ATR / time for all 5R wins and losses.**

7. **Do not solve loss streaks by shrinking TP.**
   Module H exists specifically to preserve asymmetric payoff.

# PART III — MODULE INTERACTION / EPISODES

## 20. L and H may operate at different points in one episode

Current discovery found examples with the following sequence:

```text
H-type setup fills
-> H trade fails
-> higher context remains alive
-> correction continues deeper
-> new intermediate liquidity is atomically consumed
-> L deep requalification appears
-> L positive checkpoint
```

In the current scratch audit, several Module-L requalifications were preceded by a
Module-H-like pullback fill that failed the 5R path, and the later L requalification was
positive.

Interpretation:

```text
Module H = first high-asymmetry structural pullback opportunity
Module L = later high-precision recovery after deeper correction evidence
```

This is promising but **not yet combined portfolio authority**.

Do not sum H and L P/L as if exposures, order timing and risk budgets were already solved.

## 21. Episode ledger required

Future work should use an episode ledger rather than treating every trigger as independent.

Minimum episode fields:

```text
episode_id
higher-context identity / lifetime
initial Candidate-A identity
Module-H eligibility and fill
H result / MFE / MAE
virtual or actual failure time
context alive after failure?
deeper-liquidity identity
Module-L requalification identity
L result / MFE / MAE
cumulative risk spent
absolute GOLD delivery
delivery / M30 ATR
delivery / D1 ATR
time to meaningful delivery
context invalidation
```

This is required before H/L are combined in any strategy portfolio.

# PART IV — FAILED / DEMOTED DIRECTIONS

## 22. Do not repeat these branches by default

### Entry / trigger

Rejected or demoted:

```text
sweep alone
first M1 owner transition as a replacement for M5 correction completion
delayed recovery as equivalent to atomic same-bar rejection
mandatory FVG retracement Entry
generic broken-level pullback on all Candidate A
broad SL widening
hold through original SL merely because higher context is still alive
```

### Source / frequency

Do not increase trade count by:

```text
accepting k=1.0-only low-prominence events
blindly adding k=1.5-only opportunities
treating all detector-scale duplicates as independent evidence
allowing repeat same-state entries after an already-successful delivery
```

The current reference `k=2` population substantially overlaps multi-scale-supported
intermediate liquidity. Prefer the semantic idea:

```text
intermediate / multiscale-supported physical liquidity
```

over a magical `k=2` parameter, but do not change the source authority until a reproducible
multi-scale implementation is committed.

### Static strategic-delivery predictors

The following did not reliably solve large-delivery prediction across 2023-2025:

```text
M30 expansion alone
directional progression restoration alone
M30/H1/H4 owner agreement
owner age
owner progress
correction depth
volatility hierarchy
current-day range usage
previous-day / previous-week room
rolling external extremes
defended-range room
nearest generic M30/H1 target
generic mentor-wave target proxy
```

Do not create hard gates from these negative / unstable relationships.

### Objective / TP

Not proven:

```text
nearest swing = final destination
previous day/week high-low = final destination
defended range = next trade destination
fixed 10R = mentor-style structural objective
```

The true deterministic destination hierarchy is still unresolved.

### Winner management

Rejected / demoted:

```text
M1/M5 structural trailing for final runner
M1 owner loss as final exit
+1R BE for Module H
+2R BE for Module H
continuous repeated partials at every integer R
```

### R-based interpretation traps

Do not use:

```text
fast +1R = strategic displacement
small SL = automatically good
wide SL = automatically bad
+1R success = directional thesis fully correct
SL-first = higher scenario automatically wrong
```

## 23. Existing V3-negative results still remain in force

Also preserve the earlier V3-002 / V3-003 negatives:

```text
sweep alone has almost no directional alpha
mandatory FVG-midpoint retest is rejected/demoted
fixed momentum-horizon direction models did not generalize
trade-level winner/loser ML did not generalize
forced reversal on HTF conflict is not authorized
broad SL widening is rejected
objective-room threshold is not authorized
quarter / direction vetoes are not authorized
```

Do not reopen them without new causal evidence.

# PART V — GOVERNANCE AND NEXT SESSION

## 24. Exact next-session order

A future session must proceed in this order.

### Step 1 — GitHub authority refresh

```text
latest commit
-> root AGENTS.md
-> docs/ea/HANDOFF.md
-> docs/ea/v3/AGENTS_V3.md
-> docs/ea/v3/HANDOFF_V3.md
-> docs/ea/v3/RESEARCH_STATE_V3.md
-> this V3-003D synthesis
-> V3-003C reproducible result
```

### Step 2 — reproducibility before more strategy ideas

Create dedicated scripts and immutable ledgers for:

```text
Module L primary deep-requalification control
Module L negative controls
Module H H0 broken-level control
Module H H1 natural 50% pullback candidate
Module H +3R-BE control
exact mirrors
physical multi-scale dedupe
episode linking
```

The scripts must reproduce the current headline relationships from raw 2023-2025 data.

If they do not, fix the research record. Do not tune until the old numbers reappear.

### Step 3 — Module L improvement

Primary question:

> Can the deep-requalification sample expand materially without weakening atomic-liquidity
> semantics or exact-mirror separation?

Do not optimize tiny TP distances to fake WR.

### Step 4 — Module H improvement

Primary question:

> Can the 2023 loss streak / unnecessary -1R population be reduced without losing the
> existing +5R winners?

Do not lower final TP merely to raise WR.

### Step 5 — H/L interaction

Only after standalone ledgers are stable:

```text
H failure -> L recovery
```

episode sequencing, exposure and risk budget may be evaluated.

### Step 6 — exact tick

Request/use exact tick data only after one or both module definitions become sufficiently
stable in Level-A replay.

### Step 7 — 2022 independent validation

2022 remains closed until:

- Module definitions are frozen;
- dedicated scripts / event ledgers are committed;
- accounting and causal ordering are resolved;
- natural source / geometry sensitivity is documented;
- no obvious unresolved discovery bug remains.

Then open 2022 once under the frozen contract and reject/demote rather than retune if the
relationship reverses.

### Step 8 — other auction-state modules

Per current user instruction:

```text
DO NOT start compression-breakout / failed-auction-reversal expansion yet.
```

Only return to those after the current Module L and Module H research is successfully
completed or a structural ceiling is documented.

## 25. Production authority

None of the V3-003D research changes:

```text
production Entry
production SL
production TP
EA code
live execution
```

Candidate A remains a development benchmark only.

Module L and Module H are **parallel research candidates**, not production strategies.

No 2022 or 2021 inspection is authorized by this document.

## 26. Documentation decision

This synthesis deliberately does **not** append a new production strategy decision to
`DECISIONS.md`.

Reason:

- Module L / H are not yet reproducibly committed as standalone research implementations;
- neither has independent 2022 validation;
- exact tick and MT5 execution are still pending.

The HANDOFF / RESEARCH_STATE / BACKLOG routing may be updated to preserve research direction
without falsely promoting a strategy decision.

---

One-line continuation rule:

> Preserve Candidate A as the common local-reaction benchmark; reproduce and improve
> Module L (deep-reload high precision) and Module H (clean structural pullback 5R
> asymmetry) independently, do not repeat the failed relaxation/exit branches, and do not
> open other market-state modules or 2022 until these two reload branches are properly
> frozen.
