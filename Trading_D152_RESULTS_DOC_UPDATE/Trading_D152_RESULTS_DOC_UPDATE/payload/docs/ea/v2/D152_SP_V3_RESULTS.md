# D-152 SP V3 Results — GOLD25 / BTCUSD25

Date: 2026-08-22  
Status: **COMPLETED DEVELOPMENT MATRIX / NOT BASELINE PROMOTION**  
EA build tested: `2.02R0L2 / V2_SP_ARCHITECTURE_RESEARCH_V3`  
Batch artifact SHA256: `e28cc77bb7c6419b958fdd77873a1e81fdf546ab9f52c7c776532cdf0e607d37`  
2021: **KEEP UNTOUCHED**

## 1. Test contract

D-153 batch automation executed the D-152 SP comparison under identical conditions:

```text
symbols = GOLD, BTCUSD
period = 2025.01.01 -> 2025.12.31
timeframe = M1
model = Every tick based on real ticks
regime = BASELINE_NO_REGIME_GATE
SL = ROOT_OB_DISTAL_20
risk = FIXED_RISK_MONEY $100
EM = OFF
D151 causal audit = ON
reversal authority = OFF
```

Compared modes:

```text
CTRL = SMART_PARTIAL_V2
V3A = KNOWN_DEFAULT_CLOSE
V3B = PROFIT_BANK
V3C = BANK_3R_LOCK
V3D = STRUCTURAL_BANK
V3E = BANK_2R_LOCK_ONE
```

All 12 runs completed with:

```text
terminal return code = 0
EA_START / EA_STOP = present
execution divergence = 0
pending cancel rejection = 0
```

## 2. GOLD 2025

| mode | closed | WR | final >= +1R | avg winner | expectancy | total R | max closed-R DD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SP V2 control | 53 | 52.83% | 22.64% | +1.374R | +0.228R | +12.073R | 10.252R |
| V3A known-default close | 53 | 52.83% | 20.75% | +1.379R | +0.230R | +12.214R | 9.388R |
| V3B small profit bank | 53 | 50.94% | 22.64% | +1.274R | +0.151R | +8.005R | 10.792R |
| V3C +3R lock | 53 | 52.83% | 28.30% | +1.150R | +0.110R | +5.821R | 9.140R |
| V3D structural bank | 53 | 50.94% | 26.42% | +1.365R | +0.198R | +10.471R | 8.455R |
| **V3E +2R lock-one bank** | **53** | **52.83%** | **33.96%** | **+1.328R** | **+0.203R** | **+10.783R** | **6.807R** |

Fill -> +1R:

```text
30 / 53 = 56.6%
```

## 3. BTCUSD 2025

| mode | closed / fills | WR on closed | final >= +1R | avg winner | expectancy | total R | max closed-R DD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SP V2 control | 126 / 127 | 44.44% | 16.67% | +1.101R | -0.067R | -8.453R | 16.514R |
| V3A known-default close | 128 / 128 | 44.53% | 17.97% | +1.143R | -0.047R | -5.979R | 13.698R |
| V3B small profit bank | 125 / 127 | 42.40% | 20.00% | +1.243R | -0.034R | -4.304R | 17.289R |
| V3C +3R lock | 125 / 127 | 44.00% | 27.20% | +1.213R | -0.027R | -3.391R | 16.475R |
| V3D structural bank | 125 / 127 | 42.40% | 22.40% | +1.229R | -0.040R | -5.022R | 17.289R |
| **V3E +2R lock-one bank** | **125 / 127** | **44.00%** | **32.80%** | **+1.225R** | **-0.022R** | **-2.750R** | **14.233R** |

Right-censored fills are not imputed.

Fill -> +1R:

```text
60 / 127 = 47.2%
```

## 4. Primary result

`V3E_BANK_2R_LOCK_ONE` is the **provisional SP leader**.

Its architecture separates two controls that should not be conflated:

```text
profit protection
= realized-profit banking

runner breathing room
= keep residual runner on original structural SL/TP geometry
```

At +2R it banks the minimum broker-valid extra volume required so the modeled aggregate fallback at the original normalized SL is at least `+1.05R`.

Observed closed +2R cohort:

```text
GOLD:
11 / 12 final >= +1R

BTCUSD:
31 / 31 final >= +1R
```

Where the V3E bank was broker-feasible and executed:

```text
GOLD:
8 / 8 final >= +1R

BTCUSD:
27 / 27 final >= +1R
```

This is the strongest direct D-152 result.

## 5. Promotion boundary

V3E is **not** frozen baseline authority.

Reasons:

1. evidence is still only GOLD25 + BTCUSD25;
2. BTC expectancy remains slightly negative;
3. V3E solves post-+2R economics, not Fill -> +1R survival;
4. independent period / market / direction validation is still required.

For subsequent Entry/EM research, V3E may be used as the **provisional post-+1R reference** so the best current SP architecture does not need to be re-solved in every experiment.

Do not rewrite `AGENTS_V2.md` or `EA_SPEC_V2.md` yet.

## 6. Demoted variants

### V3A — KNOWN_DEFAULT_CLOSE

Small expectancy improvement existed, but nominal price +1R full-close can realize below +1R after economic costs. If revisited, use economic net R rather than nominal price R.

### V3B — PROFIT_BANK

The `+0.05R` fallback target is too thin. Costs can turn some +2R-proven trades slightly negative.

### V3C — BANK_3R_LOCK

Raises `final >= +1R` incidence but cuts the GOLD tail too heavily and materially reduces expectancy / total R.

### V3D — STRUCTURAL_BANK

Current-M30 room at +2R did not validate as a sufficiently useful bank-strength discriminator. Do not tune another GOLD25/BTC25 threshold to rescue it.

## 7. Broker-volume infeasibility

Observed V3E bank-infeasible +2R cases:

```text
GOLD: 4
BTCUSD: 4
```

Seven of the eight later finished roughly between `+1.33R` and `+6.76R`; only one GOLD case finished below +1R, around `+0.291R`.

Therefore reject:

```text
bank infeasible -> full close
```

as a blanket fallback.

Current `KEEP_RUNNER` behavior remains the better research default.

## 8. Winner concentration

Approximate positive-R contribution of top three winners:

```text
GOLD:
SP V2 ~49%
V3E   ~33%

BTCUSD:
SP V2 ~28%
V3E   ~13%
```

V3E therefore reduces dependence on a few very large winners while keeping average winner >1R.

## 9. Why SP tuning pauses here

Current stage ceiling:

```text
GOLD Fill -> +1R = 56.6%
BTC Fill -> +1R  = 47.2%
```

Among +1R survivors, the SP family already converts roughly `93-95%` into positive aggregate outcomes.

Even with `95%` post-+1R positive conversion, a `70%` final WR requires approximately:

```text
Fill -> +1R survival ~= 73.7%
```

Therefore the primary bottleneck is now Entry survival, not additional same-sample SP tuning.

## 10. Frozen D-152 interpretation

```text
provisional SP reference = V3E BANK_2R_LOCK_ONE
V3A / V3B / V3C / V3D = demoted for now
blind +2R stop tightening = rejected
additional GOLD25/BTC25 SP threshold tuning = paused
next primary bottleneck = Entry survival
EM remains separate and experimental
```
