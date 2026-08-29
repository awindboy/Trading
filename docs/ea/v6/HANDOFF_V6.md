> **V6 CLOSED — 2026-08-30**  
> This generation is historical. Strategy-semantic H/L1/L2 development is closed.  
> Read `V6_FINAL_VALIDATION_AND_CLOSE.md` and the active V7 handoff.  
> Existing text below is preserved as the frozen historical V6 record and is superseded for active routing.

# V6 Development Handoff

Last updated: `2026-08-29`
Expected base GitHub HEAD for this overlay: `8f9c6e3e03906f2e8b4c146c3b3bb4741f6ad0e2`
Current phase: `V6-003D ROLE-CONDITIONED CORE FREEZE / EXTERNAL VALIDATION PREP`
Production authority: `NONE`
Promoted production candidate: `NONE`
Research control: `H + L1 + L2 ROLE-CONDITIONED CORE`
Untouched reserve: `GOLD 2021`

## 1. Mandatory startup

Read in order:

1. latest GitHub HEAD;
2. root `AGENTS.md`;
3. `docs/ea/HANDOFF.md`;
4. `docs/ea/WORKFLOW_AND_ZIP_HANDOFF.md`;
5. `docs/ea/v6/AGENTS_V6.md`;
6. this handoff;
7. `RESEARCH_STATE_V6.md`;
8. `V6_003D_ROLE_CONDITIONED_CORE_FREEZE_RESULTS.md`;
9. `DECISIONS_V6.md`;
10. `BACKLOG_V6.md`;
11. exact code/data before strategy changes.

GitHub wins over chat memory.

## 2. Current research control

### H

```text
DIRECT M1 transfer
+ D24 aligned
+ MENV HIGH_HIGH
-> 50% pending pullback Entry
-> sweep-extreme SL
-> +3R realize 25%
-> residual BE
-> +5R final
```

```text
N 51
WR 41.18%
avg positive +3.786R
EV +0.971R
```

### L1

```text
DIRECT
+ D14 = D24 = local direction
+ not H-authorized at trigger
-> market Entry
-> sweep-extreme SL
-> +1R / 4 active-hour cap
```

```text
N 76
WR 57.9%
EV +0.147R
```

### L2

```text
ONE_RENEG M1 path
(event -> opposite -> event)
+ D24 aligned
-> market Entry
-> sweep-extreme SL
-> +1R / 4 active-hour cap
```

```text
N 126
WR 57.9%
EV +0.129R
```

## 3. Combined core

```text
N 253
WR 54.55%
avg positive +1.269R
EV +0.304R
net +76.96R
historical max DD about 9.37R
11/13 market-years positive
```

Market-year table is in `ledgers/V6_003D_CORE_MARKET_YEAR_SUMMARY.csv`.

This is a research freeze, not a production promotion.

## 4. Main scientific interpretation

The surviving architecture is stage-specific:

```text
D24
= core directional authority

D14
= short-horizon synchronization for L1

M1 path
= local negotiation quality

MENV scale x acceptance
= H destination authority
```

These components are not interchangeable.

- Mature D24 does not rescue noisy M1 paths.
- Mature D24 does not replace MENV for H.
- Stronger MENV continuous scores do not improve HH reliably.
- H time impatience kills slow-starting TP5 winners.
- L2 prefers immediate harvest over delayed pullback Entry.

## 5. Key methodological corrections from this research phase

1. Holding horizons must use active-market time, not wall-clock time.
2. Equal bar counts across TFs are not equal physical horizons.
3. Chart-only directional research must exclude spread; execution costs are separate.
4. `m1_direct_transfer` is only known at M5 trigger, not at first M1 flip.
5. Never row-align separately sorted ledgers; use stable event keys.
6. H authorization is known before later pending fill outcome; do not resurrect L using future H non-fill.
7. Event-source comparisons must not reuse one event's optimized downstream pipeline as if that were neutral.
8. FVG overlapping-zone joins require unique zone/event identity; duplicate weighting was found and corrected.

## 6. FVG / event-source research status

FVG research is `CLOSED` for now.

Important result after correcting duplicate weighting and spread-contaminated direction labels:
- M15 FVG body states provide little independent chart-only direction information;
- much apparent movement uplift is explained by the confirmation candle/volatility state;
- H1 FVG shows a weak location-specific directional tilt but broad economics are consumed by path noise and spread;
- no robust standalone FVG module survived.

Other alternative event/source families that failed broad economic promotion include:
- M5 liquidity;
- previous H4 high/low;
- PDH/PDL direct strategies;
- M15 confirmed pivot liquidity;
- opening range;
- accepted breakout/retest;
- delayed failed breakout;
- generic pullback-resumption;
- M15 BOS retest.

Do not reopen these by threshold rescue.

## 7. Trade-count conclusion

The original M15 DC source is not rare enough to explain the low final trade count by itself.

Core density is mainly reduced at the causal conversion chain:

```text
DC source
-> atomic sweep/recovery
-> valid M5 BOS transition
-> direct / one-reneg quality
-> role authorization
```

The strongest current outcome-blind density descriptor is:

```text
recovery -> M5 BOS trigger conversion rate
```

It correlates strongly with trade density (about Spearman rho 0.86 on the consumed environment panel), but not reliably with EV/WR.

BTC produces more usable opportunities mainly because recovery more often develops into a valid M5 structural transition, not because the final direction filters are materially looser.

## 8. L2 D24-age shadow hypothesis

Consumed-panel L2:

```text
fresh D24 age <24 H1 bars:
N84 / WR 48.8% / EV about +0.003R

mature D24 age >=24 H1 bars:
N42 / WR 76.2% / EV about +0.381R
```

Continuous age relation remains positive after several controls, but GOLD recurrence is inconsistent and external short-history validation is insufficient.

Short extra-market L2 sample:

```text
all L2 N13
mature N4
```

This is not claim-grade validation.

Authority: `SHADOW ONLY`.

The mature `+1R survival -> BE -> +3R` lifecycle improved consumed-panel EV but is also not promoted.

## 9. Current module failure map

### H

51 trades:

```text
21 fail before +1R
9 reach +1R then fail before +3R
4 reach +3R then BE
17 reach +5R
```

H winners can start slowly; do not add 4h impatience exits.

### L

L1/L2 are individually thinner than H and are more sensitive to spread/slippage.

BTC2024 is mainly an L failure environment even chart-only.
XAUEUR2025 is mainly an H destination failure environment.
Do not create one universal bad-regime veto from these two different failures.

## 10. Current robustness

13-market-year block bootstrap / Monte Carlo on the frozen core keeps market-year internal sequences together.

Combined EV 95% range is approximately:

```text
+0.14R to +0.47R
```

H is much stronger individually than L1/L2. Combined stability comes partly from module diversification.

Profit contribution:

```text
H  about 64% of net R
L1 about 15%
L2 about 21%
```

No single trade dominates the positive-R pool.

## 11. Exact next work

Do not continue consumed-panel micro-tuning by default.

Priority:

1. acquire longer outcome-blind histories;
2. preregister market shortlist using non-P/L descriptors such as opportunity density, recovery->M5 conversion and spread/R;
3. validate frozen H/L core unchanged;
4. validate L2 D24-age shadow unchanged;
5. preserve GOLD2021;
6. build exact execution stress and MT5 reproduction after external validation breadth improves.

For execution:
- L: spread/slippage/commission sensitivity first;
- H: commission/slippage plus swap/overnight financing.

## 12. Hard restrictions

- no GOLD 2021;
- no market selection after observing strategy P/L;
- no D24 age gate promotion on current evidence;
- no new H strength score inside HH;
- no H 4h impatience checkpoint;
- no automatic opposed inversion;
- no fresh L2 rescue by D48 or nearby horizons;
- no FVG reopening by width/displacement/CE threshold search;
- no M5 trigger weakening simply to increase trade count;
- no right-censored relabeling;
- no production EA change from this offline research freeze.
