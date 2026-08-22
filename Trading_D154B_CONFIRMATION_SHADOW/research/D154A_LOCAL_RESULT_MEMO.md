# D-154A Local Result Memo — Entry Survival Ownership Audit

Date: 2026-08-22  
Status: **DISCOVERY COMPLETE / NOT STRATEGY AUTHORITY / NOT YET COMMITTED**  
Data: GOLD 2025 + BTCUSD 2025, M1, Every tick based on real ticks, V3E, EM OFF.

## Integrity

Both full runs returned terminal code 0 with EA_START/EA_STOP present, zero execution divergence, and zero cancel rejection.

The D-154A run reproduced the prior D-152 V3E performance exactly:

| Market | Closed | WR | Avg winner | Expectancy | Total R | DD |
|---|---:|---:|---:|---:|---:|---:|
| GOLD | 53 | 52.83% | 1.328R | +0.203R | +10.783R | 6.807R |
| BTCUSD | 125 of 127 | 44.00% | 1.225R | -0.022R | -2.750R | 14.233R |

Formal D-154A OFF/ON parity files were not included in the uploaded ZIP, but this exact reproduction is strong cross-run non-interference evidence.

## Entry-survival baseline

- GOLD: 30/53 = 56.6% Fill -> +1R
- BTCUSD: 60/127 = 47.2%
- pooled descriptive: 90/180 = 50.0%

## Finding 1 — naive Fill-time M1 maturity gate is rejected

At actual Fill:

- TRANSITION: 49/107 = 45.8%
- OPPOSITE_DIR_MATURE: 35/62 = 56.5%
- SAME_DIR_MATURE: 6/11 = 54.5%

BTC especially contradicts a simple `same-direction mature M1 = good Entry` rule.

Therefore do **not** add a Fill-time SAME_DIR_MATURE requirement or opposite-direction veto.

## Finding 2 — first post-Fill owner resolution is materially related to survival

Within the 107 TRANSITION-at-Fill trades, the first post-Fill M1 INITIAL_BOS before the original +1R/SL terminal was:

- SAME direction: 29/43 = 67.4% original Fill -> +1R
- OPPOSITE direction: 14/50 = 28.0%
- no INITIAL_BOS before primary terminal: 6/14 = 42.9%

Direction relation by market x direction:

- BTC LONG: SAME 5/6 = 83.3% vs OPP 5/22 = 22.7%
- BTC SHORT: SAME 14/20 = 70.0% vs OPP 3/14 = 21.4%
- GOLD LONG: SAME 6/10 = 60.0% vs OPP 4/10 = 40.0%
- GOLD SHORT: SAME 4/7 = 57.1% vs OPP 2/4 = 50.0%

The relation direction is SAME > OPP in all four cells. A descriptive Mantel-Haenszel common odds ratio is about 4.9 (95% CI about 1.94–12.46), but this is discovery evidence, not promotion evidence.

## Important confound

The structural event direction is strongly coupled to price path:

- transition + first SAME INITIAL_BOS: median confirmation around +0.184 original R, median ~25.9 minutes after Fill
- transition + first OPPOSITE INITIAL_BOS: median around -0.206 original R, median ~29.7 minutes

So D-154A does **not** establish that M1 ownership adds independent information beyond favorable/adverse movement.

That is why the next step is a real shadow-entry test from the causal confirmation price, not a new filter.

## Confirmation geometry is usually still viable

For transition fills whose first same-direction confirmation occurred before the primary terminal, using the confirmation price and the original normalized SL:

- BTCUSD median structural objective room ≈ 2.90 new R; 92.3% still had >=1R structural room
- GOLD median structural objective room ≈ 4.03 new R; 94.1% still had >=1R structural room

Thus a delayed-entry shadow is geometrically testable without inventing a tighter stop.

## Post-SL source succession

90 SL-first trades:
- 33 recovered to original +1R before map-support loss
- 56 reached map-support failure first (including already-not-same at SL)
- 1 right-censored

Among cases with map support still alive at SL:
- recovery group: other-Root FVG appeared in 14/33 = 42.4%
- map-loss group: other-Root FVG appeared in 9/44 = 20.5%

Only 3 recovered cases had a Root newly created after the failure before an FVG/Fill; all 3 recovered, but the sample is too small.

Actual successor fills before the original recovery/map-loss terminal:
- GOLD: 5 unique successor fills, 4 reached their own +1R
- BTCUSD: 31 unique successor fills, 17 reached their own +1R

Same-Root successor FVG/Fill was zero. Code inspection indicates this is not clean empirical evidence against same-Root retry: a filled master Root remains bound to its scenario while `ReleaseRootScenarioOwner()` is used on pre-execution terminal paths. Treat same-Root zero as lifecycle-constrained until explicitly instrumented outside that authority.

## Frozen D-154A decision

1. Reject simple Fill-time M1 maturity gate.
2. Do not use M30 runner maturity as Entry authority.
3. Promote only the **post-Fill transition-resolution question** to D-154B shadow testing.
4. Keep post-SL other-Root succession as a separate later research axis; do not combine it with D-154B.
5. No real Entry/SL/TP/EM change yet.
