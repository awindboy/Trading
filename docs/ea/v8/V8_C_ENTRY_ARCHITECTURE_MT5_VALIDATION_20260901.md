# V8-C Deterministic Entry Architecture and MT5 Validation

Date: `2026-09-01`
Status: `LONG ENTRY PROVISIONAL FROZEN / REAL-TICK VERIFIED ON OPEN DEVELOPMENT EVIDENCE`
Production authority: `NONE`
Market: `GOLD#`
Untouched reserve: `GOLD# 2021`

## 1. Executive state

V8 began by searching for a learned representation that could predict directional action from ambiguous chart context. That broad direction program produced substantial negative evidence. The strongest practical result instead came from a deterministic conditional-entry architecture:

```text
specific factual event
+ high V8-A movement state
+ local Stochastic direction
+ completed multi-timeframe path context
=> selective LONG
```

This V8-C LONG candidate survived MT5 Every Tick based on real ticks across 2024, 2025 and 2026 YTD with approximately 60% realized win rate.

The current conclusion is not that MA20 or Stochastic alone predicts GOLD. The stronger conclusion is that V8-A movement state becomes directionally useful only inside a specific causal event geometry.

## 2. Frozen V8-A

V8-A predicts movement, not direction:

```text
P(reach C0 +/-10 within 15m / 30m / 60m)
```

Historical models are walk-forward:

```text
2024 <- 2022-2023
2025 <- 2022-2024
2026 <- 2022-2025
```

Representation is the frozen 53-feature causal M1 movement/range/activity vector.

## 3. V8-B direction program — what failed

The following are negative-result authority:

- generic future UP/DOWN;
- 5/10/15/30/60m endpoint sign;
- future slope sign;
- excursion dominance;
- independent +10/-10 touch probabilities interpreted as sign;
- micro barriers;
- V8-A probability as direction weighting;
- future-magnitude weighting;
- WAIT/recenter endpoint confirmation;
- non-reproducible confidence-tail selection;
- original B1, invalidated by M15/H1 look-ahead.

Best weak local target:

```text
15m +10-only vs -10-only
AUC ~0.603 / 0.556 / 0.535
```

No learned V8-B direction model has deployment authority.

## 4. Intermediate deterministic findings

### A1 Stochastic survivor

```text
M5 SMA20 contact-start
P30 above causal previous-288 mean
bullish raw Stoch cross
K-D gap <= frozen 2024 median
LONG +/-10
```

One-position:

```text
2024 N132 WR59.85% +26R
2025 N223 WR56.95% +31R
2026 N192 WR56.77% +26R
pooled N547 WR57.59% +83R
```

### P15 50-cross armed Stochastic

```text
N1086
WR52.49%
+54R
```

Positive but weaker.

### AO direction replacement

Failed:

```text
N1086
WR48.53%
-32R
```

On AO/Stochastic disagreement:

```text
AO ~44.03%
Stochastic ~55.97%
```

Therefore AO was not retained.

## 5. Current V8-C LONG rule

```text
M5 SMA20 CONTACT START
+
current V8-A P15 >
linear Q75 of immediately prior 288 completed M5 P15 states
from same V8-A model calendar year
+
raw Stochastic K14 > D3
+
latest completed M15 close > close 3 completed M15 bars earlier
+
latest completed H1 close < close 3 completed H1 bars earlier
=
LONG at next M5 open / first real tick

SL = actual fill -10
TP = actual fill +10
one position
```

No symmetric SHORT is included.

## 6. Why each major component stayed

### Remove P15 relative state

Later-year performance deteriorated:

```text
2024 58.84%
2025 54.21%
2026 51.74%
```

### Remove MA20 event context

Same directional state on all M5 bars:

```text
56.46 / 53.13 / 49.42
```

### Use all contact bars instead of contact-start

```text
55.77 / 52.35 / 52.51
```

### Delay entry

The edge was highly local; +5m/+10m delayed variants weakened, especially in 2026.

### P15 threshold

Q60/Q67/Q70/Q75/Q80 and 144/288/576 lookbacks preserved the broad relationship. Q75/288 is retained as a stable neutral point rather than a single-year optimum.

### Extra Stochastic slope

Marginal gain, meaningful trade-count loss. Rejected from frozen LONG.

### AO / RSI / MACD / session extras

No robust incremental value sufficient for inclusion.

## 7. Symmetric SHORT failure

Mirror:

```text
P15 > Q75
K < D
M15 down
H1 up
=> SHORT
```

Result:

```text
2024 42.07%
2025 48.76%
2026 49.07%
pooled 46.51%
```

This was not rescued by threshold tuning.

Structural interpretation:

The mirror frequently shorts a short-term decline inside a broader positive GOLD path. LONG and SHORT are therefore treated as separate causal setups rather than mirrored indicator signs.

## 8. MT5 implementation history

### R0/R0.1

External iCustom V8-A dependency could terminate Strategy Tester at OnInit. V8-A EX5 was embedded as a resource.

### R0.2

An unnecessary host-period hard failure caused `INIT_PARAMETERS_INCORRECT`. Removed without changing strategy semantics.

### R0.3

P15 history became an EA-side causal online queue, preventing event-time bulk-buffer instability and ensuring current P15 is excluded from its own Q75.

R0.3 then revealed an execution bug: a false `PositionModify()` return was treated as proof of protection failure and caused 74 artificial immediate EXPERT closes in the first 2024-2025 run.

R0.3 P/L is invalid evidence.

### R0.4

R0.4 verifies actual `POSITION_SL`/`POSITION_TP` state and only fail-closes when exact protection genuinely remains wrong.

Accepted R0.4 runs contain zero artificial EXPERT exits.

## 9. Accepted MT5 real-tick results

Environment:

```text
GOLD#
M5
Every tick based on real ticks
Optimization OFF
```

### 2024

```text
N 152
91 wins / 61 losses
WR 59.87%
+29.26R
+0.193R/trade
PF 1.47
max closed-trade DD ~7.64R
max loss streak 6
median holding ~279.4m
```

### 2025

```text
N 165
101 wins / 64 losses
WR 61.21%
+37.35R
+0.226R/trade
PF 1.57
max closed-trade DD ~5.10R
max loss streak 5
median holding ~55.8m
```

### 2026 through 2026-08-28

```text
N 139
82 wins / 57 losses
WR 58.99%
+25.24R
+0.182R/trade
PF 1.43
max closed-trade DD ~5.10R
max loss streak 5
median holding ~15.1m
```

2026:

```text
authorized 142
blocked by existing position 3
actual trades 139
```

The actual trade count matched the prior 2026 one-position research proxy count.

### Pooled

```text
N 456
274 wins / 182 losses
WR 60.09%
+91.85R
+0.201R/trade
PF ~1.49
max observed closed-trade DD ~7.64R
max loss streak 6
```

The real-tick result stayed close to the M1/OHLC discovery relationship instead of collapsing.

## 10. Cost / execution qualification

Accepted tester ledgers recorded:

```text
commission 0
swap 0
fee 0
```

So these results are not universal full-cost authority for other broker/account environments.

Realized average winner is around +1.01R and average loser around -1.02R due to execution around the fixed barriers.

## 11. Holding-time compression

```text
2024 median ~279m
2025 median ~56m
2026 median ~15m
```

The fixed 10-dollar move represents a smaller relative movement as GOLD price and volatility rise.

This is an exit/execution issue, not evidence that the entry condition itself failed.

## 12. Current separate SHORT candidate — V8-C-S1

Research-only:

```text
M5 SMA20 contact-start
P15 > prior-288 Q75
raw Stoch K < D
previous M5 high < previous SMA20
event M5 close < event SMA20
trailing 288 M5 net displacement < 0
=> SHORT next M5 open
TP -10
SL +10
```

Interpretation:

```text
negative broader path
+ price already below MA20
+ first re-contact from below
+ failure to reclaim MA20
+ bearish local momentum
+ high V8-A movement state
```

M1 one-position proxy:

```text
2024 N41 WR58.54%
2025 N51 WR54.90%
2026 N48 WR62.50%
pooled N140 WR58.57%
82 wins / 58 losses
+24R
+0.171R/trade
```

Combined LONG+SHORT M1 proxy:

```text
N574
WR60.98%
+126R
```

This is consumed development evidence only. V8-C-S1 has not passed MT5 real-tick validation.

## 13. Current authority

```text
V8-A:
FROZEN movement-probability control

V8-B:
PAUSED negative-result authority

V8-C LONG:
PROVISIONAL FROZEN entry candidate
MT5 real-tick verified on 2024/2025/2026 open development evidence

V8-C-S1 SHORT:
research candidate
M1 proxy only

Production:
NONE
```

## 14. Next research sequence

Do not further tune V8-C LONG entry.

Next:

1. Preserve R0.4 LONG exactly.
2. Add V8-C-S1 SHORT only in a research variant.
3. MT5 real-tick validate SHORT separately on 2024/2025/2026.
4. Audit parity/execution before economics.
5. If SHORT survives, freeze the entry architecture.
6. Move to winner continuation / exit research.
7. Seek average winner meaningfully >1R while retaining WR >=50%.
8. Add full execution-cost testing where commission exists.
9. Keep GOLD# 2021 locked.

## 15. Final limitation

The current full exit at +/-10 is intentionally a 1R entry-edge validator.

It is not the final strategy because the project requires average winner/payoff meaningfully above 1R, positive full-cost expectancy, and stability across independent evidence.

GOLD# 2021 remains locked until the architecture stops changing.
