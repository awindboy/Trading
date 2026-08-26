# V3-003E — Dual Reload Module Advances / Emergency Session Handoff

Status: `DISCOVERY RESULT + CONTINUATION CONTRACT / NO STRATEGY AUTHORITY`  
Date: `2026-08-26`  
Repository HEAD at handoff: `02e5fa578579883f6fdd2ed5936e9d17ff8cb05a`  
Market: `GOLD# ONLY`  
Discovery data: `2023-2025 M1`  
Validation vault: `2022 — CLOSED`  
Untouched: `2021`

## 0. Emergency purpose

This document was created because the research session reached its maximum conversation
length. A new session must continue from this document and must **not** repeat the already
falsified branches recorded below.

The user wants the two reload modules improved in parallel:

```text
MODULE L — LOW-R / HIGH-WR
MODULE H — HIGH-R / LOW-WR / HIGH-R MULTIPLE
```

Do not start other market-state modules yet. Continue improving L and H until they either
reach a stronger coherent architecture or a documented structural ceiling.

## 1. Critical reproducibility finding

The prior V3-003D synthesis stated that a dedicated Candidate-A replay script was committed
under `research/ea/v3/...`, but the current GitHub HEAD does not contain the referenced file.
This is a real documentation/reproducibility gap.

During the just-finished session, the raw GOLD data were replayed independently and the
following were reproduced exactly from scratch:

```text
Candidate A:
2023 40 / +1R 60.0%
2024 29 / +1R 65.5%
2025 27 / +1R 63.0%

Module L physical deep-requalification:
10 independent episodes
11 actual trades
checkpoint before SL 11/11
full +1R before SL 10/11
exact-mirror checkpoint 1/11

Module H reference 50% pullback + 3R->BE + 5R:
48 fills
14 TP5
31 SL
3 BE
+39R total
+0.8125R/trade
```

These results were regenerated from accepted 2023-2025 GOLD raw data, but the newly cleaned
replay implementation and immutable ledgers were **not committed before this emergency
handoff**.

### Mandatory next-session first task

Before any new tuning:

1. create/commit one common Candidate-A replay engine;
2. create/commit Module-L and Module-H downstream replay scripts;
3. commit physically deduplicated ledgers;
4. prove the above counts again;
5. correct the stale synthesis statement that implied the missing script was already in GitHub.

Do not tune definitions merely to match the counts.

# PART I — MODULE L

## 2. Module L primary setup remains deep requalification

Primary causal sequence:

```text
Candidate A appears as VIRTUAL PROBE only
-> virtual sweep-extreme SL is hit
-> higher context remains alive
-> correction continues deeper
-> new meaningful INTERMEDIATE M15 liquidity
-> atomic same-M1 penetration + close recovery
-> fresh same-direction M5 re-acceptance
-> first REAL Module-L Entry
```

Important boundaries:

- the first Candidate-A failure is virtual; do not pay it with capital in Module L;
- generic deeper correction + first M5 transition is insufficient;
- delayed recovery is not equivalent to atomic rejection;
- generic M15 pivots destroy precision;
- low-prominence-only events must not be added for sample size.

## 3. Module L new preferred payoff control

The important new result is that Module L no longer needs to choose between `~1R only` and
losing its high-WR character by moving the full TP farther.

Use:

```text
checkpoint = min(1R, 0.5 D1 ATR)

at checkpoint:
    realize 50%
    move residual to economic BE
    residual target = 2R
```

The 50% fraction is reused from prior SP controls, not newly fitted from a dense grid.

Reproduced physical Module-L primary sample:

```text
11 trades
11/11 positive
7/11 residual reached 2R
average realized positive ~= +1.13R
```

Approximate per year:

```text
2023 5 trades / 5 positive / avg positive ~1.30R / residual-2R 4
2024 4 / 4 / ~0.74R / residual-2R 1
2025 2 / 2 / ~1.50R / residual-2R 2
```

Exact mirror under the same payoff control:

```text
positive ~1/11
average EV ~-0.78R/trade
```

This is currently the strongest Module-L payoff architecture.

### Why full 1.5R / 2R TP was rejected

Sending the entire position to 1.5R or 2R reduced the 2024 high-WR property to around 50%.
The improvement comes from **protect first, free-run residual second**, not from simply
moving Module-L TP farther.

## 4. Module L source expansion boundary

Adaptive intermediate M15 liquidity remains the primary source family.

Generic M15 pivot source expanded the sample substantially but destroyed precision
(roughly 2023 ~59%, 2024 ~89%, 2025 ~78% checkpoint in the exploratory census and a much
stronger mirror), so it is rejected as a sample-expansion mechanism.

M15 mentor-wave source was directionally interesting but tiny. Unioning adaptive primary
with mentor-wave unique physical events produced approximately:

```text
13 unique trades
12 positive checkpoint
~92.3% positive
EV around +0.9R/trade under the newer protection logic
```

However the mentor-wave source added only a very small number of genuinely unique events,
including both a win and a loss. It is not promoted.

### Module-L next research

1. Preserve adaptive intermediate primary semantics.
2. Study behavioral/structural commonality of the 11 primary events rather than loosening
   prominence.
3. Study scenario/context lifetime because some virtual-failure -> real-requalification waits
   are many hours or longer.
4. Search independent semantic source families only if they preserve atomic/deeper-reload
   mechanism and exact-mirror separation.
5. Build failure taxonomy on any future real Module-L loss.
6. Keep generic pivot / k=1.0-only expansion rejected.

# PART II — MODULE H

## 5. Module H baseline before new eligibility work

Prior reproduced reference:

```text
Candidate A
-> clean M1 ownership path
-> first 50% acceptance-leg pullback
-> same sweep-extreme SL
-> +3R then residual BE
-> final +5R

48 fills
14 TP5
31 SL
3 BE
+39R
EV +0.8125R/trade
```

The 5R winners represented real GOLD moves, not merely tiny-SL R inflation.

## 6. Direct M1 ownership transfer — strongest new H eligibility fact

Inside the previous `clean M1 path`, distinguish:

```text
DIRECT TRANSFER:
M1 owner at sweep is opposite trade direction
-> exactly one ownership transfer into trade direction
-> no opposite owner flip before M5 trigger
```

Reference 48 H fills contained 4 non-direct fills.

```text
non-direct:
0 TP5
4 SL
```

Removing only non-direct fills:

```text
44 trades
14 TP5
27 SL
3 BE
+43R
EV ~+0.977R/trade
```

This preserved every known +5R winner.

### Robustness

Across natural M15 adaptive source scales `k=1.5/2.0/2.5` and natural pullback variants
`25/50/75/100%`, non-direct H fills produced **no +5R winner** in the current discovery
panel. An independent M15 mentor-wave source showed the same qualitative role: non-direct
fills were all losers in its small sample.

A very noisy generic pivot source was not rescued by direct transfer, which is a useful
negative control.

Interpretation:

> Direct transfer is a promising Module-H-specific high-R eligibility fact, not a universal
> liquidity filter and not automatically a Module-L gate.

It remains discovery until committed replay/ledger and later validation.

## 7. `BOTH` delivery-state branch — promising H exclusion candidate

Candidate-A delivery state is:

```text
M30 expansion > 1
OR
M30/H1 owner agreement with trade direction
```

Define `BOTH` when both branches are simultaneously true.

In Module H, current discovery found that `BOTH` fills generated **zero +5R winners** across:

```text
M15 adaptive k=1.5/2.0/2.5
x
pullback 25/50/75/100%
```

and the small independent M15 mentor-wave H sample also produced no +5R winner in BOTH.

Reference direct-H after shadow-excluding BOTH:

```text
40 trades
14 TP5
23 SL
3 BE
+47R
EV ~+1.175R/trade
```

Approximate annual cells:

```text
2023 17 trades / 5 TP5 / 10 SL / 2 BE / EV ~+0.88R
2024 12 / 5 / 6 / 1 / EV ~+1.58R
2025 11 / 4 / 7 / 0 / EV ~+1.18R
```

### Important caveat

The actual reference H fill population had essentially no BOTH observations in 2025.
Therefore BOTH-exclusion is **not frozen** despite its clean discovery behavior.

Do not automatically route BOTH to Module L. That separate experiment failed to establish a
clean L edge/mirror separation.

## 8. H exact-mirror / scale evidence remains favorable

For direct-transfer reference H, exact mirror +5R remained materially weaker; approximate
annual original vs mirror rates were:

```text
2023 ~25% vs ~15%
2024 ~38.5% vs 0%
2025 ~36.4% vs 0%
```

This supports directional information rather than symmetric GOLD volatility.

## 9. H profit protection

The following remains the strongest primary H management:

```text
before +3R: keep original sweep-extreme SL
at +3R: move residual stop to BE
final TP: +5R
```

Across the natural source/pullback panel, +3R->BE preserved existing +5R winners in the
current discovery replay.

Rejected / inferior:

```text
+1R -> BE
+2R -> BE
M1 owner-flip exit
M5 structure reacceptance exit
micro-structure trailing
proof-first wait for original Candidate-A +1R before pullback Entry
```

These cut genuine tail winners or destroyed entry geometry.

### Secondary positive-frequency H variant

Reuse prior SP 25% fraction:

```text
+3R -> realize 25%
residual -> BE
residual final -> +5R
```

A final TP realizes `4.5R`; a 3R-touch/fail can realize `+0.75R`.
This increases positive-trade frequency while preserving a large average positive trade.
Keep it separate from the raw-EV-maximizing +3R-BE-only control.

A +2R partial-harvest experiment did not produce a compelling improvement and is not primary.

## 10. H loss-taxonomy work completed / rejected gates

Several intuitive loss reducers were tested and rejected or demoted:

- cancel pending if M1 ownership flips before fill;
- require M1 owner still aligned at fill;
- require touch then M1 rejection close at midpoint;
- wait for original Candidate-A +1R proof before pullback Entry;
- source-age hard gate such as `>24h`;
- require source formed after current M5 correction start;
- explicit M30+H1 opposite-owner veto;
- directional reinterpretation of M30 expansion using recent-leg net displacement;
- one-H-attempt-per-state episode (repeat attempts were too rare to explain loss streaks).

None gave a cross-year causal improvement clean enough to promote while preserving the +5R
winners.

The 2023 remaining loss streak after direct/BOTH work is smaller but still a key research
problem. Do not create a 2023-specific veto.

## 11. Work that was STARTED BUT NOT COMPLETED when the session ended

The following were the immediate next experiments but **no completed result is authorized**:

1. stronger H failure/invalidation based on the original swept-liquidity rejection itself:
   - after H fill, does a body close back through the original swept-liquidity level identify
     doomed H trades without cutting +5R winners?

2. H loss-magnitude reduction using an existing 50% SP fraction around +2R while preserving
   +3R/5R tail logic.

Do not assume either works. Resume them as explicit experiments from the reproduced H ledger.

# PART III — H / L EPISODE INTERACTION

## 12. H failure -> L recovery is reproducible in the discovery ledger

Among current H losses, 5 episodes later produced robust Module-L deep requalification.
Those later L requalifications were all positive at the high-precision checkpoint.

Using the new Module-L payoff (`checkpoint 50% realized -> residual BE -> residual 2R`), the
five H-loss episodes became approximately:

```text
+0.50R
+0.50R
+0.50R
-0.546R
+0.50R
```

That is, 4/5 previously losing H episodes became net-positive episodes after later causal
L evidence appeared.

Crucial rule:

> Do not hindsight-cancel the H trade. Current Entry-time geometry did not show a stable
> deterministic separator between H losses that would later recover via L and H losses that
> would not.

Correct sequence remains:

```text
H is independently authorized -> take H
if H fails -> accept -1R
if and only if later L evidence actually appears -> take independent L requalification
```

## 13. Descriptive combined episode economics

These are discovery descriptions only, not portfolio authority.

### H full-5R management + L recovery inside H episodes

Approximate 40 H episodes:

```text
positive episode rate ~45.0%
negative episode rate ~47.5%
average positive ~4.00R
EV ~+1.34R/episode
max negative streak ~6
max DD ~7.5R
```

H standalone before L recovery was roughly:

```text
positive ~35%
EV ~+1.175R
max negative streak ~9
max DD ~9R
```

### H 3R-25%-harvest variant + L recovery

Approximate:

```text
positive episode rate ~52.5%
average positive ~3.20R
EV ~+1.22R/episode
max negative streak ~6
max DD ~7.5R
```

This trades some raw EV for more positive episodes.

## 14. Standalone L episodes do not appear to conflict with H exposure in current ledger

Of the 11 primary Module-L trades, 5 were H-loss recovery episodes and 6 were standalone L
episodes. In the current discovery replay, the 6 standalone L events did not overlap an open
H position.

A descriptive merged timeline can therefore be computed without obvious overlap in this
sample.

### H full-5R + all L episodes

Approximate 46 episodes:

```text
positive ~52.2%
negative ~41.3%
average positive ~3.25R
EV ~+1.29R/episode
max negative streak ~5
max DD ~7R
```

Annual descriptive cells:

```text
2023 19 episodes / positive ~52.6% / avg positive ~2.85R / EV ~+1.13R
2024 15 / ~53.3% / ~3.44R / ~+1.46R
2025 12 / 50.0% / ~3.67R / ~+1.33R
```

### H 3R-25%-harvest + all L episodes

Approximate:

```text
positive ~58.7%
average positive ~2.71R
EV ~+1.19R/episode
max negative streak ~5
max DD ~7R
```

Annual positive rates were approximately 63.2% / 60.0% / 50.0%.

These numbers are **not** a final combined strategy result. They are motivation for an
explicit deterministic episode ledger and exposure/risk-budget study.

# PART IV — CURRENT RESEARCH BOUNDARIES

## 15. Do not repeat these branches

Unless new causal evidence exists, do not reopen:

```text
M1 early trigger replacing M5 correction completion
delayed recovery treated as atomic rejection
generic pivot expansion for Module L
low-prominence-only sample expansion
mandatory FVG retracement Entry
global SL widening
fast +1R as strategic scale proof
static HTF filter mining
M30/H1/H4 agreement as generic large-delivery gate
objective-room thresholds
previous-day/week nearest target as final objective
M1/M5 runner trailing
+1R BE / +2R BE for Module H
proof-first H Entry after original +1R
quarter/direction vetoes
fixed 10R as solved mentor objective
```

## 16. Current best research controls — NOT production authority

### Module L primary

```text
virtual Candidate-A failure
-> higher context alive
-> deeper meaningful M15 intermediate liquidity
-> atomic same-bar rejection/recovery
-> fresh M5 re-acceptance
-> REAL Entry
-> checkpoint = min(1R, 0.5 D1 ATR)
-> 50% realize
-> residual BE
-> residual target 2R
```

### Module H control hierarchy

Keep all three levels separate:

```text
H0 SIMPLE CONTROL:
Candidate A
-> clean M1
-> broken M5 level first retest
-> sweep SL
-> 5R

H1 GEOMETRY CANDIDATE:
Candidate A
-> clean M1
-> 50% acceptance-leg pullback
-> sweep SL
-> +3R BE
-> 5R

H2 ELIGIBILITY DISCOVERY:
H1
-> direct M1 ownership transfer required
-> BOTH delivery branch shadow-excluded
```

`direct transfer` has stronger evidence than `BOTH exclusion`.
Do not collapse H2 into a frozen strategy until reproducibility files are committed and the
BOTH caveat is explicitly addressed.

## 17. Next-session exact order

1. **Reproducibility package first.**
   Commit Candidate A + Module L + Module H replay scripts and immutable CSV ledgers.
   The previous documented script path is missing from GitHub and must be repaired.

2. **Resume the two unfinished H experiments** listed in section 11.

3. **Continue H remaining-loss taxonomy** from the direct-transfer population, with BOTH
   exclusion as a shadow candidate, not a frozen gate.
   Primary target: reduce 2023 loss streak / DD without losing any existing +5R winner.

4. **Continue L sample expansion only through meaningful source semantics.**
   Do not relax atomic/deeper-reload logic. Study context lifetime and semantic source
   families.

5. **Build one deterministic H/L episode ledger** with cumulative risk and no double counting.
   Preserve standalone module metrics separately from combined descriptive metrics.

6. **Do not open 2022 yet.**
   2022 may be opened only after scripts/ledgers are committed and Module L / H definitions
   are sufficiently frozen.

7. **Do not start other auction-state modules yet.**
   User explicitly wants the current two modules improved further first.

8. `2021` remains untouched.

## 18. Production authority

None.

No current result changes live/production Entry, SL, TP, sizing or EA execution.
No EA/MQL5 code modification is authorized by this document.

One-line continuation rule:

> First make Candidate A/L/H fully reproducible in GitHub; then keep improving Module L for
> precision/sample quality and Module H for 5R winner preservation with fewer losses, while
> using H-failure -> later-L-requalification only as a causal episode recovery sequence and
> not as hindsight routing.
