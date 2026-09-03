# V8 Sequential Capital Allocation Research — 2026-09-03

Status: DEVELOPMENT / PRACTICAL CAPITAL ALLOCATION
Account assumptions supplied by user:
- starting equity: USD 1,000
- minimum volume step/minimum lot: 0.01
- leverage: 1:1000
- 0.01 lot P/L: approximately USD 1 for each USD 1.00 GOLD price move
- GOLD# 2021 remains locked

## Core correction

Do not apply equal size/equal risk to all ACCEPTANCE events.
Use the existing research according to its causal meaning:

1. Slow-N / ACCEPTANCE -> frequent opportunity / small probe
2. actual structural survival -> evidence update
3. realized early MFE -> large-winner continuation evidence
4. stronger evidence may receive larger *later* capital, subject to discrete lot and account-risk constraints

## Executability correction

A 0.01 lot position cannot be split 50/50 because 0.005 lot is unavailable.
Therefore the old conceptual 50/50 partial architecture is not the primary $1,000-account implementation.

Primary executable decomposition:

A. ROUTINE BASE
- Acceptance -> 0.01 lot
- TP +0.25S
- SL -0.25S
- bank the result as a complete trade

B. RUNNER RE-ENTRY
- at Acceptance+15m only
- require M1 close structure intact
- require prior frozen high-progress state:
  P0 MFE15 >= 0.555S
  P2 MFE15 >= 0.546S
- re-enter a separate runner at next M1 open
- add-on stop control: -0.40S
- size in 0.01-lot units from account-risk budget
- compare 2% and 3% risk-budget policies; do not outcome-tune between them

This avoids using the runner signal as the initial entry gate while allowing large capital only after the market
causally demonstrates runner-grade behavior.

## Approximate median-scale dollar mechanics

Using representative S medians from the practical movement phase and one-spread illustration of USD 0.17 per
0.01-lot round trip:

Routine .25S probe risk per 0.01:
- 2024 S~11.9: ~USD 3.15 (~0.31% equity)
- 2025 S~20.0: ~USD 5.17 (~0.52%)
- 2026 S~43.0: ~USD 10.92 (~1.09%)

Runner .40S stop risk per 0.01:
- 2024: ~USD 4.93
- 2025: ~USD 8.17
- 2026: ~USD 17.37

At a 2% runner-risk budget (USD 20) the discrete median-S runner sizes are roughly:
- 2024: 0.04 lot
- 2025: 0.02 lot
- 2026: 0.01 lot

At 3%:
- 2024: 0.06
- 2025: 0.03
- 2026: 0.01

The 2026 equality is caused by the 0.01 lot granularity, not by equal setup quality.

## Exact Slow-N high-progress economics translated to dollars

Prior exact P0/P2 high-progress standalone economics used TP +0.75S / SL -0.40S after the 15m runner state.

Annual E[R]:
P0: 2024 +0.071 / 2025 +0.481 / 2026 +0.450
P2: 2024 +0.033 / 2025 +0.432 / 2026 +0.453

At the median-S 2% discrete risk sizing above, expected dollars per elite runner are approximately:
P0: +1.40 / +7.86 / +7.82
P2: +0.65 / +7.06 / +7.87
for 2024 / 2025 / 2026.

These are aggregate expected-value translations, not an equity-curve claim.

## Right-tail finding

The previous +0.75S runner TP likely truncates the right tail.

Broad causal ACCEPTANCE mechanism discovery (NOT exact Slow-N economic validation), restricted to
15m close-intact + MFE15>=0.55S, shows total favorable excursion by 480m:

- median ~1.27-1.35S
- P(MFE>=1.5S) ~38-44%
- P(MFE>=2.0S) ~18-31%
- P(MFE>=3.0S) ~5-13%

At 2%-budget median-S discrete runner sizes, full capture would correspond approximately to:
- 1.5S: USD 71 / 60 / 64.5
- 2.0S: USD 95 / 80 / 86
- 3.0S: USD 143 / 120 / 129
for 2024 / 2025 / 2026.

This is precisely the type of low-frequency right-tail payoff that can dominate a USD 1,000 account.
It is opportunity characterization only; it does not authorize assuming MFE can be captured perfectly.

## Frozen next payoff challenger

Keep the exact high-progress runner entry and -0.40S initial stop.

Control:
- fixed TP +0.75S.

Open-tail challenger:
- no hard profit cap after +0.75S;
- after +0.75S is first confirmed, trail 0.50S behind the favorable extreme;
- the stop is updated only from the PREVIOUS completed M1 bar, so no same-bar lookahead;
- max horizon 480m;
- compare fixed-TP vs trailing under exact Slow-N P0/P2 before promotion.

The 0.75S activation and 0.50S trail distances are inherited existing research scales, not P/L-mined values.

## Capital policy interpretation

Routine ACCEPTANCE is not where the account should take its largest risk.
The desired shape is:

Acceptance -> 0.01 routine probe
routine target -> bank small USD profit
15m runner-grade proof -> re-enter larger discrete lot under a fixed account-risk budget
right tail -> allow rare large USD winners

Do not increase size merely because P15 or predicted retention is high.
Increase only after causal realized evidence (close integrity + realized early MFE) that has already survived later-year validation.

2021 remains untouched.
