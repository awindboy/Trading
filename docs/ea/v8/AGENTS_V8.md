# V8 Research Instructions

Status: `ACTIVE`
Generation: `V8`
Last synchronized: `2026-09-01`
Production authority: `NONE`
Market: `GOLD#`
Untouched reserve: `GOLD# 2021`

## 1. Current branch map

```text
V8-A
FROZEN / CURRENT ABSOLUTE-$10 MOVEMENT CONTROL

V8-A2
RETAINED ABSOLUTE-$10 CHALLENGER / NOT PROMOTED

V8-A-N
RETAINED ATR-NORMALIZED MOVEMENT CHALLENGER

V8-A-N N1
FROZEN DEVELOPMENT MOVEMENT TRIGGER:
1.50 ATR fresh P15 75-cross

V8-A-N N2
ACTIVE BOTTLENECK
initial 2024-only technical rule falsified
N2-R1 maximin technical ensemble ~57.5% development only
next = genuinely new direction information

V8-A-N N3
INITIAL SIMPLE ATR PAYOFF FAMILY COMPLETE
no variant yet meets WR>=50% + avg winner>1R in every year

V8-A-N N4
CURRENT COMPLETE NORMALIZED STRATEGY NOT PROMOTED

FIXED-$10 FRESH75
DEVELOPMENT CONTROL
$10 SL / $13 TP remains stronger current combined benchmark

V8-C LONG
PROVISIONAL FROZEN / MT5 REAL-TICK VERIFIED

V8-C-S1 SHORT
RESEARCH-ONLY / M1 PROXY
```

## 2. Frozen controls

Preserve V8-A, V8-A2 and V8-C LONG unchanged.

V8-A:

```text
P(reach C0 +/-$10 within 15/30/60m)
```

V8-A2 remains the 86-feature absolute-dollar survival challenger with the prior-288 R15/R30/R60 reliability layer.

V8-C LONG remains:

```text
M5 SMA20 contact-start
V8-A P15 > prior-288 Q75
Stoch K14>D3
completed M15 3-bar up
completed H1 3-bar down
=> LONG next M5 open
SL/TP +/-10
one position
```

Accepted R0.4:

```text
N456 / WR60.09% / +91.85R
```

Do not modify its entry.

## 3. V8-A-N movement authority

V8-A-N is a retained research challenger, not production authority.

Causal scale:

```text
pre-decision M5 Wilder ATR14
```

The normalized research established that fixed ATR-multiple movement base rates and normalized excursion distributions are substantially more stable across 2022-2026 than a fixed $10 barrier.

Current prototype independent-distance probability surfaces are research-only because rare distance-order violations remain.

Final model architecture must enforce:

```text
farther distance -> probability cannot increase
longer horizon -> probability cannot decrease
```

## 4. N1 frozen normalized movement trigger

N1 was selected without LONG/SHORT labels or trade P/L.

Frozen trigger:

```text
barrier = 1.50 * causal pre-decision M5 ATR14

previous completed M5 P15_1.50ATR <75%
current completed M5 P15_1.50ATR >=75%
```

Movement evidence:

```text
2024 N809  P15 hit81.64%  P30 93.92%  P60 98.88%
2025 N834  P15 hit77.85%  P30 91.77%  P60 98.18%
2026 N551  P15 hit80.04%  P30 93.77%  P60 97.80%
```

2026 is partial through the available Aug-28 history.

Frequency characteristics:

```text
monthly mean ~67-70 triggers
active-day median = 3
median spacing ~328-380m
<=60m repeat ~23-30%
```

Do not change N1 based on downstream direction or P/L.

## 5. N2 direction status

### Initial 2024-only freeze

A five-vote indicator rule reached ~59.6% in 2024, then:

```text
2025 48.28%
2026 49.44%
```

It is falsified. Do not threshold-rescue it.

### N2-R1

After 2025/2026 were consumed, a post-hoc maximin development ensemble was created.

Direction accuracy:

```text
2024 57.34%
2025 57.62%
2026 57.43%
```

This stability is useful as a development control, but there is no independent validation authority.

The broad indicator/OHLC feature space is therefore not sufficient evidence for a high-confidence direction engine.

Current N2 priority is new causal information:

- raw XM tick/quote microstructure;
- sub-minute bid/ask update imbalance;
- quote arrival acceleration;
- spread dynamics;
- later CME GC order flow / macro surprise if available.

Do not change N1 while researching N2.

## 6. N3 simple ATR-consistent economics

Development direction = N2-R1.

Entry = next M5 open.

Primary test:

```text
SL 1.0 ATR
TP 1.0 / 1.25 / 1.50 ATR
60m horizon
```

Results:

```text
TP1.0:
WR 54.64 / 54.80 / 55.72%
EV +0.093 / +0.096 / +0.114R
avg winner = 1R

TP1.25:
WR 49.94 / 49.04 / 51.18%
EV +0.124 / +0.103 / +0.153R
avg winner = 1.25R

TP1.50:
WR 45.36 / 46.16 / 47.55%
EV +0.134 / +0.150 / +0.191R
avg winner ~1.5R
```

No tested variant satisfies both:

```text
WR >=50% every year
average winner meaningfully >1R
```

Do not immediately optimize 1.10/1.15/1.20 to rescue N3.

## 7. Execution-cost warning

The normalized trading proxy is not MT5 real-tick authority.

Approximate recorded entry spread relative to a 1ATR risk unit:

```text
2024 median ~0.137R
2025 ~0.061R
2026 ~0.049R
```

Therefore ATR normalization can create high relative transaction cost in quiet regimes even while movement targets are statistically portable.

Do not call N3 cost-adjusted profitable.

Any later executable normalized architecture must address spread/slippage with actual fill-relative testing.

## 8. N4 comparison

On common 2025/2026 development evidence:

```text
fixed fresh75 $10/$10:
WR 59.65 / 58.87%
EV +0.193 / +0.177R

fixed fresh75 $10/$13:
WR 52.63 / 52.07%
EV +0.207 / +0.198R

normalized N1 + N2-R1 + SL1ATR/TP1.25ATR:
WR 49.04 / 51.18%
EV +0.103 / +0.153R
```

Current interpretation:

- V8-A-N movement portability is stronger;
- normalized N1 trigger cadence is structurally superior;
- normalized direction is weaker;
- current complete normalized strategy does not beat the fixed-$10 $10/$13 development benchmark.

Do not abandon V8-A-N; improve the bottleneck rather than undoing the movement result.

## 9. Evidence status

```text
2022-2026:
development evidence for V8-A-N

2024-2026:
consumed normalized direction/economics development evidence

2021:
LOCKED / UNTOUCHED
```

No claim of independent validation for N2-R1 or N3.

## 10. Current work order

1. Preserve N1 = 1.50ATR fresh75.
2. Do not reopen N3 parameter tuning.
3. Build N2 raw tick/quote microstructure research on exactly the frozen N1 population.
4. Use shifted/placebo tick windows to distinguish local information from regime correlation.
5. Only reopen N3 after direction or execution information improves materially.
6. Build a monotonic V8-A-N probability surface before live indicator authority.
7. Keep fixed-$10 $10/$13 as the current trading benchmark.
8. Keep V8-C separate.
9. Keep GOLD# 2021 locked.

## 11. Reading authority

1. `HANDOFF_V8.md`
2. `V8_A_N_FRESH_HIGH_N1_N4_RESULTS_20260901.md`
3. `V8_A_N_ATR_NORMALIZED_MOVEMENT_RESEARCH_20260901.md`
4. `DECISIONS_V8_RESEARCH_DIRECTION_ADDENDUM_20260901.md`
5. `RESEARCH_STATE_V8.md`
6. `BACKLOG_V8.md`
7. historical V8-A2/V8-C docs as needed.

Always refresh GitHub HEAD before continuing.
