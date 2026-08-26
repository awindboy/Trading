# V3-003E — Dual Reload Reproducibility Restoration and Latest Improvement Results

Status: `DISCOVERY RESULT / REPRODUCIBILITY PACK / NO PRODUCTION AUTHORITY`  
Date: `2026-08-26`  
Repository HEAD audited before this update: `02e5fa578579883f6fdd2ed5936e9d17ff8cb05a`  
Market: `GOLD# ONLY`  
Execution environment represented by discovery data: `XM Ultra Low / XMGlobal-MT5 7 / GOLD#`  
Discovery/development data: `2023-2025 M1`  
Validation vault: `2022 — CLOSED`  
Untouched: `2021`

## 0. Purpose

This document is the authoritative continuation record for the research completed **after**
`V3_003D_DUAL_RELOAD_MODULE_RESEARCH_SYNTHESIS.md`.

The prior V3-003D documentation became stale before the research session ended. In
particular, `RESEARCH_STATE_V3.md` and `BACKLOG_V3.md` still said Module L/H reproducibility
was the next task even though that replay had already been completed during the session.

This document therefore records:

1. what was independently reproduced from raw GOLD data;
2. the latest Module-L improvements;
3. the latest Module-H improvements and caveats;
4. the H -> L episode interaction;
5. branches already falsified after V3-003D;
6. the two experiments that were **started but not completed** when the session ended;
7. the exact order in which the next session must continue.

This is a research handoff, not an EA promotion.

---

# 1. Documentation/reproducibility audit

## 1.1 Candidate-A script path correction

The V3-003D synthesis listed the Candidate-A replay script under an incorrect path:

```text
research/ea/v3/v3_003c_reload_state_acceptance_probe.py
```

The actual repository path is:

```text
scripts/v3_003c_reload_state_acceptance_probe.py
```

The script exists at the audited HEAD and its blob is the expected V3-003C implementation.
This update corrects the stale path in the old synthesis.

## 1.2 New integrated replay chain

This update adds:

```text
scripts/v3_003d_correction_completion_probe.py
scripts/v3_003e_dual_module_repro.py
```

The integrated V3-003E replay consumes accepted GOLD 2023-2025 M1 data and:

```text
Candidate A
-> natural M15 source-scale panel
-> Module-L virtual-failure / deep-requalification ledger
-> Module-H pullback variants
-> H-specific direct-transfer / BOTH metadata
-> H-to-L recovery links
-> descriptive combined episode ledgers
```

It fails closed if data outside 2023-2025 are supplied.

The exact physical ledgers produced by the replay used for this document are committed under:

```text
docs/ea/v3/ledgers/
```

A future session must use the script/ledgers as the starting point, not try to reconstruct
the latest results from chat memory.

---

# 2. Common Candidate-A parity — PASSED

The integrated replay reproduced the frozen `V3_RELOAD_CANDIDATE_A` reference exactly:

| Year | Candidate A | +1R before SL |
| --- | ---: | ---: |
| 2023 | 40 | 60.0% |
| 2024 | 29 | 65.52% |
| 2025 | 27 | 62.96% |

Natural source sensitivity was also reproduced:

```text
M15 k=1.5
2023 67 / 53.73%
2024 53 / 62.26%
2025 41 / 53.66%

M15 k=2.0
2023 40 / 60.00%
2024 29 / 65.52%
2025 27 / 62.96%

M15 k=2.5
2023 32 / 56.25%
2024 18 / 66.67%
2025 18 / 66.67%
```

Candidate A remains a **local reaction/timing development benchmark**. It is not promoted
to strategic-destination authority.

---

# PART I — MODULE L: LOW-R / HIGH-WR

## 3. Module-L primary causal architecture — REPRODUCED

Module L continues to use the first Candidate-A trade as a **virtual probe only**.

```text
Candidate A virtual Entry
-> virtual sweep-extreme SL occurs
-> higher context still alive
-> correction continues deeper
-> new meaningful intermediate M15 liquidity
-> atomic same-M1 penetration + close recovery
-> fresh same-direction M5 re-acceptance
-> first REAL Module-L Entry
```

Important semantic boundary:

```text
virtual first failure != actual -1R capital loss
```

The virtual failure provides information that the first correction-completion attempt was
premature.

Generic deeper correction followed by the first M5 turn was already a weak negative control.
Delayed recovery after body delivery through the liquidity was also weak. Module L therefore
continues to require the deeper **atomic** intermediate-liquidity event.

## 4. Module-L physical replay parity

After deduplicating overlapping M15 `k=1.5 / 2.0 / 2.5` detections by physical
requalification trigger:

```text
10 independent higher-context episodes
11 physical Module-L trades
```

Reproduced barrier result:

```text
checkpoint = min(1R, 0.5 D1 ATR)

checkpoint before SL = 11 / 11
full +1R before SL   = 10 / 11
exact-mirror checkpoint = 1 / 11
```

This remains a **small sample**. Do not describe it as a proven 100%-WR strategy.

## 5. Latest Module-L payoff improvement — CURRENT PRIMARY L PAYOFF CONTROL

Pushing the entire position to 1.5R or 2R weakened the high-WR character, especially in
2024.

The stronger architecture is:

```text
checkpoint = min(1R, 0.5 D1 ATR)

when checkpoint is reached:
    realize 50%
    residual stop -> economic BE
    residual target -> +2R
```

The 50% fraction is reused from prior SP controls. It was not selected from a dense discovery
grid.

Reproduced primary physical ledger:

| Year | Trades | Positive | Residual reached 2R | Mean realized R |
| --- | ---: | ---: | ---: | ---: |
| 2023 | 5 | 5 | 4 | +1.297R |
| 2024 | 4 | 4 | 1 | +0.738R |
| 2025 | 2 | 2 | 2 | +1.500R |
| **Total** | **11** | **11** | **7** | **+1.131R/trade** |

Therefore Module L is no longer merely:

```text
"take about 1R and leave"
```

Its current role is:

> lock a very high-probability first checkpoint, then let a free residual capture additional
> delivery.

Exact-mirror checkpoint remains only `1/11`, so the high positive rate is not explained only
by using a nearby barrier.

## 6. Module-L source expansion boundaries

The research session also established the following boundaries:

### Rejected

```text
generic M15 pivot liquidity
k=1.0-only low-prominence additions
```

Expanding through generic pivots increased sample size but materially reduced precision and
increased mirror success.

### Exploratory only

```text
M15 mentor-wave source
```

The mentor-wave family produced only a few independent additions. It is useful as a semantic
cross-check but does not yet have enough unique evidence to expand Module L authority.

### Current L research problem

The main weakness is **sample count**, not payoff.

Future sample expansion must come from a liquidity family that preserves the same
correction-completion meaning. Do not relax the atomic/deeper-reload sequence simply to
manufacture frequency.

---

# PART II — MODULE H: HIGH-R / LOW-WR

## 7. Reproduced H base control

Reference Module-H discovery geometry:

```text
Candidate A
-> clean M1 ownership path
-> first 50% retracement of the accepted M5 leg
-> same sweep-extreme SL
-> original SL remains active until +3R
-> at +3R residual SL -> BE
-> final TP +5R
```

Reference `k=2 / 50%` replay:

```text
48 fills
14 TP5
31 SL
3 BE
total +39R
EV +0.8125R/trade
```

This matches the prior scratch result.

The simple broken-M5-level retest remains an important H0 control. The 50% geometry remains
a discovery candidate, not a frozen universal ratio.

## 8. H-specific direct M1 ownership transfer — STRONGEST NEW H ELIGIBILITY FINDING

`clean M1 path` contains a stricter causal sequence:

```text
at sweep:
M1 owner is opposite the trade

then:
exactly one M1 ownership transfer occurs

that transfer is into the trade direction

and:
no opposite owner flip occurs before the M5 trigger
```

This is `direct M1 ownership transfer`.

### Reference k=2 / 50%

The 4 non-direct H fills were:

```text
0 TP5
4 SL
```

Therefore direct-transfer eligibility changed the reference from:

```text
48 fills / 14 TP5 / 31 SL / 3 BE
```

to:

```text
44 fills / 14 TP5 / 27 SL / 3 BE
+43R
EV +0.9773R/trade
```

No +5R winner was removed.

Annual direct-transfer reference:

| Year | N | TP5 | SL | BE | EV |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2023 | 20 | 5 | 13 | 2 | +0.600R |
| 2024 | 13 | 5 | 7 | 1 | +1.385R |
| 2025 | 11 | 4 | 7 | 0 | +1.182R |

### Natural panel robustness

The integrated replay additionally verifies:

```text
M15 source k = 1.5 / 2.0 / 2.5
pullback = 25 / 50 / 75 / 100%
```

Across that complete natural panel:

```text
non-direct +5R winners = 0
```

This gives direct transfer much stronger H-stage evidence than its earlier use as a general
Entry gate.

Stage separation remains important:

```text
direct transfer as generic Candidate-A gate    != authorized
direct transfer as Module-H 5R eligibility     = strongly promising
```

## 9. BOTH branch — PROMISING SHADOW EXCLUSION, NOT FROZEN

Within direct-transfer H setups, define:

```text
owner_agree =
M30 owner == trade direction
AND
H1 owner == trade direction

BOTH =
M30 expansion > 1
AND owner_agree
```

Across the natural `k × pullback` panel reproduced in the integrated replay:

```text
direct-transfer + BOTH +5R winners = 0
```

For the reference k=2 / 50% sample, shadow-excluding BOTH gives:

```text
40 fills
14 TP5
23 SL
3 BE
total +47R
EV +1.175R/trade
```

Annual descriptive cells:

| Year | N | TP5 | SL | BE | EV |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2023 | 17 | 5 | 10 | 2 | +0.882R |
| 2024 | 12 | 5 | 6 | 1 | +1.583R |
| 2025 | 11 | 4 | 7 | 0 | +1.182R |

### Critical caveat

The H-fill reference contained no meaningful 2025 BOTH sample to independently test the
exclusion in 2025.

Therefore:

```text
direct transfer = stronger candidate
BOTH exclusion   = shadow candidate only
```

Do not hard-freeze BOTH exclusion before independent evidence exists.

## 10. H large-winner character remains intact

The +5R winners represent meaningful GOLD movement rather than fake high-R created by a tiny
stop.

Prior session measurement for the same winner set was approximately:

```text
median +5R target distance:
2023 ~$23.6
2024 ~$23.6
2025 ~$37.7

rough D1 scale:
2023 ~1.16 D1 ATR
2024 ~0.71 D1 ATR
2025 ~0.83 D1 ATR

median time to +5R:
2023 ~4.6 h
2024 ~13.1 h
2025 ~15.0 h
```

This is why Module H should continue to protect the 5R tail rather than shrink TP merely to
raise win rate.

## 11. Module-H protection controls

### Primary

```text
before +3R:
    keep original sweep-extreme SL

at +3R:
    move residual to BE

final:
    +5R
```

The natural source/pullback panel showed that +3R -> BE preserved existing +5R winners.

### Rejected

```text
+1R -> BE
+2R -> BE
M1 owner-flip final exit
M5 structure-reacceptance final exit
micro-structure trailing
```

They cut genuine later +5R winners.

### Secondary positive-frequency control

Use the previously established SP 25% fraction:

```text
+3R:
    realize 25%
    residual -> BE
    residual final -> +5R
```

For the current direct + not-BOTH shadow population:

| Year | N | Positive rate | Avg positive | EV |
| --- | ---: | ---: | ---: | ---: |
| 2023 | 17 | 41.18% | 3.43R | +0.824R |
| 2024 | 12 | 50.00% | 3.88R | +1.438R |
| 2025 | 11 | 36.36% | 4.50R | +1.000R |

Pooled:

```text
positive rate = 42.5%
average positive = 3.84R
EV = +1.056R/trade
```

This trades some raw EV for more realized-positive trades. Keep it separate from the
raw-EV-maximizing +3R-BE-only H control.

---

# 12. H failure-taxonomy branches already tested after V3-003D

Do not repeat these without a new causal reason.

The following did not produce a sufficiently stable cross-year improvement while preserving
the +5R winner set:

```text
wait for original Candidate-A +1R proof before pullback Entry
cancel pending merely because M1 owner flips before fill
require M1 owner still aligned at fill
50% touch then require an extra M1 rejection close
source-age hard gate such as >24h
require source to have formed after the current M5 correction start
simple M30+H1 opposite-owner veto
directional reinterpretation of M30 expansion from recent-leg net displacement
one H attempt per state episode
```

Several of these looked good in one year and failed in another. Do not resurrect them as
2023-specific loss-streak fixes.

---

# PART III — MODULE H -> MODULE L EPISODE INTERACTION

## 13. H failure -> later L requalification — REPRODUCED

Using the current H `direct-transfer & not-BOTH` shadow population, five H losses were later
followed by independently authorized Module-L deep requalification.

Committed link ledger:

```text
V3_003E_H_TO_L_RECOVERY_LINKS.csv
```

The five episode nets under the current Module-L payoff were:

```text
+0.500R
+0.500R
+0.500R
-0.546R
+0.500R
```

Therefore:

```text
4 / 5 H-loss episodes became net-positive after later L evidence
```

Important:

> Do not hindsight-cancel the H trade because L later appeared.

No stable deterministic separator was found at H Entry time that cleanly identified the
future H->L recovery subset.

The causal sequence remains:

```text
H independently qualifies -> take H
if H fails -> accept -1R
if later deeper atomic L evidence appears -> take independently authorized L
```

## 14. Descriptive combined episode economics

These results are **descriptive research**, not portfolio authority.

### Current H raw + Module L

Using H direct + not-BOTH shadow, full +5R / +3R-BE management, and adding L only after
actual H loss plus standalone L episodes:

```text
46 episodes
positive rate       52.17%
negative rate       41.30%
average positive    +3.249R
expectancy          +1.292R/episode
total               +59.44R
max negative streak 5
max DD              ~7R
```

Annual descriptive cells:

```text
2023 19 episodes / positive 52.63% / avg positive 2.85R / EV +1.13R
2024 15 / 53.33% / 3.44R / +1.46R
2025 12 / 50.00% / 3.67R / +1.33R
```

### H +3R 25% harvest + Module L

```text
46 episodes
positive rate       58.70%
negative rate       41.30%
average positive    +2.712R
expectancy          +1.189R/episode
total               +54.69R
max negative streak 5
max DD              ~7R
```

This variant sacrifices some raw expectancy to increase positive-episode frequency.

### Authority boundary

Do not call either line the final combined strategy.

Before combination authority:

```text
position/exposure ordering
episode risk budget
exact pending/fill ordering
commission/slippage/swap
exact-tick parity
```

must be explicit.

---

# 15. Latest work started immediately before the session ended — NO RESULT YET

The previous session ended while two Module-H experiments were being prepared.

These experiments are **not completed** and no outcome should be assumed.

## 15.1 Stronger H invalidation based on original swept liquidity

Question:

> After H pullback fill, can a body close back through the original swept-liquidity level
> identify a genuine rejection failure before the catastrophic sweep-extreme SL, while
> preserving the +5R winners?

This is more structurally meaningful than the already-rejected M5 broken-level reacceptance
exit.

Required next test:

```text
H primary ledger
-> after fill
-> first M1 body close through original swept liquidity
-> first M5 body close through original swept liquidity
-> compare timing versus TP5 / BE / SL
-> compute hypothetical exit R only if causal
-> verify zero/near-zero TP5 destruction before considering it
```

Do not substitute wick penetration for body-close failure unless tested separately.

## 15.2 +2R 50% protection / loss-magnitude experiment

The other started experiment was:

```text
+2R:
    realize 50% using existing SP fraction
    keep residual original SL until +3R
+3R:
    residual -> BE
final:
    +5R
```

Purpose:

- increase actual positive trades;
- reduce the economic damage of trades that reach +2R but later fail;
- do so without turning Module H into a low-R system.

No result was completed before session end.

Resume this as an explicit secondary payoff experiment and compare against:

```text
H primary: +3R -> BE -> 5R
H secondary: +3R 25% harvest -> residual BE -> 5R
```

Do not assume +2R harvesting is superior.

---

# 16. Immediate next-session research order

A new session must proceed in the following order.

## Step 1 — authority refresh and replay parity

Read:

```text
AGENTS.md
docs/ea/HANDOFF.md
docs/ea/v3/AGENTS_V3.md
docs/ea/v3/HANDOFF_V3.md
docs/ea/v3/RESEARCH_STATE_V3.md
V3_003D_DUAL_RELOAD_MODULE_RESEARCH_SYNTHESIS.md
THIS DOCUMENT
```

Then run:

```text
scripts/v3_003e_dual_module_repro.py
```

against the same accepted GOLD 2023-2025 data.

Do not continue if these fail:

```text
Candidate A 40 / 29 / 27
Module L 11 physical / checkpoint 11 / full1 10 / mirror checkpoint 1
Module H base 48 / 14 TP5 / 31 SL / 3 BE
Module H direct 44 / 14 TP5 / 27 SL / 3 BE
Module H direct-notBOTH shadow 40 / 14 TP5 / 23 SL / 3 BE
H->L links = 5, of which 4 are net-positive with current L payoff
```

A parity failure is a reproducibility bug, not an invitation to retune.

## Step 2 — finish the two interrupted H experiments

First:

1. original swept-liquidity body-close invalidation;
2. +2R 50% protection variant.

Do not branch into new ideas before recording these results.

## Step 3 — continue H remaining-loss taxonomy

Primary comparison population:

```text
Candidate A
-> direct M1 ownership transfer
-> 50% pullback research geometry
-> same sweep SL
-> +3R BE
-> 5R
```

Keep `BOTH exclusion` as **shadow**, not frozen.

Goal:

> remove or reduce the remaining H losses / loss streak without deleting the existing +5R
> winners.

Do not use a 2023-only veto.

## Step 4 — continue Module-L sample expansion

Keep the current high-precision mechanism fixed.

Research:

```text
meaningful independent M15 liquidity semantics
context/scenario lifetime
adaptive vs mentor-wave physical overlap
why low-prominence/generic pivot additions fail
```

Do not loosen the atomic/deeper-reload sequence.

## Step 5 — explicit H/L episode risk architecture

Use the committed link and combined ledgers to formalize:

```text
one H risk allocation
possible later independent L risk allocation
maximum cumulative episode risk
standalone L exposure
position overlap
```

Keep standalone H and standalone L statistics separately visible.

## Step 6 — only then decide whether Level-A is mature enough for exact tick

Do not open 2022 before the dual-module definitions are stable enough that a single
independent validation run is meaningful.

---

# 17. Do-not-repeat list carried forward

Unless genuinely new causal evidence exists, do not reopen:

```text
M1 early trigger replacing M5 correction completion
delayed recovery treated as atomic same-bar rejection
generic-pivot Module-L sample expansion
k=1.0-only low-prominence additions
mandatory FVG midpoint/retest Entry
broad SL widening
fast +1R interpreted as strategic-scale proof
static HTF threshold mining
quarter or direction vetoes
proof-first H Entry after original Candidate-A +1R
generic M1/M5 runner trailing
+1R BE / +2R BE as H primary protection
fixed 10R treated as solved mentor objective
nearest generic swing / previous-day-week level treated as proven final destination
```

---

# 18. Current module hierarchy

## Module L — current primary research control

```text
virtual Candidate-A failure
-> context alive
-> deeper meaningful intermediate M15 liquidity
-> atomic same-bar recovery
-> fresh M5 re-acceptance
-> real Entry
-> checkpoint=min(1R,0.5D1)
-> 50% realize
-> residual BE
-> residual 2R
```

Status:

```text
REPRODUCED
VERY SMALL SAMPLE
HIGH PRECISION
SAMPLE-EXPANSION PROBLEM UNSOLVED
```

## Module H — control hierarchy

```text
H0 simple:
Candidate A
-> clean M1
-> broken M5 retest
-> sweep SL
-> 5R

H1 geometry:
Candidate A
-> clean M1
-> 50% accepted-leg pullback
-> sweep SL
-> +3R BE
-> 5R

H2 stronger eligibility:
H1
-> direct M1 ownership transfer

H3 shadow:
H2
-> exclude BOTH branch
```

Evidence ranking:

```text
direct transfer   stronger
BOTH exclusion    promising but not frozen
```

---

# 19. Production and validation authority

None of this document authorizes:

```text
EA Entry change
EA SL change
EA TP change
EA sizing change
live trading
2022 discovery use
2021 inspection
other auction-state module start
```

Other market-state modules remain deferred by user instruction until the current L/H reload
research is substantially improved or reaches a documented ceiling.

One-line continuation rule:

> Verify the committed V3-003E replay first; finish the two interrupted H experiments; then
> keep improving H by preserving every genuine +5R winner while cutting remaining losses,
> and improve L by expanding only semantically meaningful deep-requalification evidence,
> with H->L recovery treated as a causal episode sequence rather than hindsight routing.
