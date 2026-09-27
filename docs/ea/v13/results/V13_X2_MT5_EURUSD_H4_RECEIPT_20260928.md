# V13 X2 — same-broker EURUSD# H4 observation receipt

Date: `2026-09-28`
Status: `CONSUMED DEVELOPMENT / NEGATIVE BILATERAL-FX RESULT / NO ACTION`
Contract: `../V13_X2_MT5_EURUSD_H4_OBSERVATION_CONTRACT_20260928.md`
Source: `research/v13/x2_mt5_eurusd_h4_observation.py`
Local generated audit: `output/v13_x2_mt5_eurusd_h4_20260928/` (not in Git)

## Decision

Using a truly **same-clock H4 external market** did not rescue Journey-birth
loss selection. Same-broker EURUSD# H4 one-/three-bar dollar-proxy changes,
with or without GOLD# Journey-side alignment, worsened chronological Brier
score in all four test blocks versus GOLD# H4 morphology plus ordered GOLD# H1
state. The descriptive highest-risk groups still held valuable long-Journey
winners. No Child admission, exit, sizing, model, EA or production promotion.

This is a negative result for the contracted **EURUSD# bilateral H4** family,
not for DXY, USD yields, futures order flow, or every possible external state.
It does, however, directly answer the time-grain weakness of X1's delayed
daily ECB proxy: the X2 series is intraday H4 and clock-matched.

## Source and causal checks

- GitHub `main` checked before contract/evaluation:
  `be88fa2be516963b2dcd196819f9b2fd026b077a`.
- XM MetaTrader 5 terminal build `6230`, Python `copy_rates_range`, UTC-aware
  request 2022-01-01 through 2026-08-28 20:00; symbols exactly `GOLD#` and
  `EURUSD#`, timeframe H4.
- Returned GOLD# history had 7,199 bars. **All 7,199 timestamps and all four
  OHLC values matched** the frozen repository GOLD# H4 CSV, with zero value
  differences. This is the specific source-clock parity check, not an
  assumption that two products share universal UTC/session semantics.
- Returned EURUSD# history had 7,253 H4 bars. It covered the opening time of
  **every one of those 7,199 GOLD# bars**; no missing or duplicate FX match.
  All FX bars had valid OHLC geometry and nonzero broker tick activity.
- The causal X2 feature build matched an exact EURUSD# H4 signal bar at all
  4,108 gold decision timestamps. It rejected any FX feature whose bar had
  not completed by `known_at`. It built/saved/hashed the feature ledger before
  loading future Journey outcomes; all 966 Journey births were represented.
- The pre-existing Baseline-0 idealized economic parity was 965 closed
  Journeys, 3,858 Children and +8,147.11 GOLD price points. This is not USD
  profit, real-tick MT5 tester economics, or an EA variant.
- MetaQuotes history API semantics:
  https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py

The X2 model uses `-log(EURUSD# close)` change over one and three completed
H4 bars, each divided by its prior-20-FX-bar median absolute change. The
third locked coordinate is three-bar change × current GOLD# Journey side.
No source popularity, sign rule, chosen lag, or optimized threshold was used.
The absolute normalized one-/three-bar FX-change medians by year were
`0.978/0.981` (2024), `0.997/1.000` (2025), and `0.994/1.000` (2026), so
the fixed trailing scale did not leave a large raw-era magnitude drift.

## Target and chronological outcome

At each Journey's first Child, the primary label was eventual negative
*whole-Journey* Baseline-0 Child-sum PnL. Previous-Journey loss was used only
for repeated-loss diagnosis. A training Journey had to be **closed and known**
before the next test block began. The same four expanding chronological OOF
blocks as X1 yielded 777 test Journeys, including 590 losers (`75.9%`) and
441 repeat losses. 2024-H1 supplied training history, not OOF claims.

| OOF model | Brier ↓ | Log loss ↓ | AUC ↑ | Fixed-bin ECE ↓ |
| --- | ---: | ---: | ---: | ---: |
| Training-fold loss rate | **0.18521** | **0.55962** | 0.5032 | **0.04328** |
| GOLD# H4 morphology + ordered H1 | 0.18706 | 0.56832 | **0.5462** | 0.06762 |
| + same-broker EURUSD# H4 1-/3-bar changes | 0.18810 | 0.57177 | 0.5402 | 0.07691 |
| + side × EURUSD# 3-bar change | 0.18865 | 0.57373 | 0.5369 | 0.07641 |

The base-rate predictor even beat the H4/H1 economic-loss model in pooled
Brier score; FX did not fix that weakness. Brier by chronological block:

| Test block (Journeys) | H4/H1 | + FX changes | + side interaction |
| --- | ---: | ---: | ---: |
| 2024-H2 (191) | 0.17295 | 0.17462 | 0.17670 |
| 2025-H1 (168) | 0.22968 | 0.23186 | 0.23195 |
| 2025-H2 (178) | 0.16582 | 0.16623 | 0.16626 |
| 2026 to cutoff (240) | 0.18422 | 0.18442 | 0.18444 |

The simple FX additions also worsened Brier in five of six year×side slices;
only 2026 LONG improved very slightly (`0.19430 -> 0.19406`). Such a slice
is diagnostic only, not authority for an exception or side-specific model.

## Repeated losses versus valuable winners

The top predicted-loss 20% is a predeclared **descriptive rank bucket** of
156 OOF Journeys, not a simulated veto.

| Diagnostic | H4/H1 | + FX | + interaction |
| --- | ---: | ---: | ---: |
| Losing Journeys / 156 | 122 | 121 | 120 |
| Winning Journeys / 156 | 34 | 35 | 36 |
| Repeat-loss Journeys / 441 overall | 89 | 92 | 86 |
| Gross winning points | +1,820.43 | +4,170.88 | +4,802.84 |
| Gross losing points | -2,967.88 | -2,794.01 | -2,928.36 |
| Bucket net points | -1,147.45 | **+1,376.87** | **+1,874.48** |
| >=10-bar Journeys in bucket | 8 | 11 | 14 |
| Their net points | +1,031.28 | **+3,593.00** | **+4,089.05** |

The FX-change score caught three more repeat losses than H4/H1 alone
(`92` versus `89`) but caught **one fewer losing Journey overall** and
included 11 profitable >=10-bar Journeys. The interaction worsened both
loss counts and long-tail false warnings. Compared with H4/H1's top 156,
the FX-change bucket replaced 16 Journeys; its newly included 16 comprised
12 losses, 4 wins and **+2,203.48** net points. These outcomes are known
only ex post and cannot be used to sculpt a new rule.

## Boundary and next research decision

The only supported decision here is to **stop the contracted EURUSD# H4
one-/three-bar proxy family**. Do not search lags, normalize differently,
flip the sign, add a time exception or veto winners on this consumed period.
The result suggests the externally sourced FX movement is not an incremental
selector of repeated economic Journey failure under this specific target and
minimal model; it does not prove external markets never matter.

Any next external family must state a *different information mechanism* and
obtain trustworthy time-stamped history with causal availability; avoid
another re-expression of GOLD# or a pile of correlated FX pairs. The exact-
window actual-tick MT5 Baseline-0 receipt and untouched future validation
remain required before an economic action can be promoted.

### Broker dollar-index source rejected at the availability gate

The same MT5 terminal lists `USDX-DEC26` and returned 7,197 H4 history rows
starting in 2022. However its symbol description is **US Dollar Index
December 2026**, and its broker-provided `start_time` is 2026-09-10 — *after*
the V13 canonical cutoff. These old bars may be a backfilled synthetic/history
display under a future-dated contract name. They do not establish that this
exact instrument was available at 2024-2026 decisions. X2 therefore did
**not** use those apparent pre-start bars as a causal DXY substitute. This
is a source-authority rejection, not an outcome test of a valid dollar index.

## Reproduction hashes

```text
GOLD# H4:       b080fb5463df1f80592cfeeecacc4d422069b69ac40635b912d03d97873aecbf
HA-8A features: dc2a082cddd16359da8cb518cd535747297beecad521d40821034e0bf543be0d
MT5 EURUSD# H4: ee4e09e58e6361da398c282618ac21a655dddb64d75bd5141a961d11e40c828e
X2 features:    71079b25b8a97ac7fd49e98f0141b2141d8a5555d506d7e5a52824714d774e33
```
