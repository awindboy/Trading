# V13 HA-9 — add-on proof/lock action receipt

Date: `2026-09-28`
Status: `CONSUMED DEVELOPMENT / BREAKTHROUGH ACTION CANDIDATE / MT5 VALIDATION PENDING`
Contract: `../V13_HA9_ADDON_PROOF_LOCK_ACTION_CONTRACT_20260928.md`
Audit: `research/v13/ha9_addon_proof_lock_audit.py`
Market/window: `GOLD#`, 2024-01-01 through 2026-08-28 available history

## 1. Structural parity

The audit reconstructs the unchanged Baseline-0 economics first:

```text
closed Journeys: 965
closed Children: 3,858
Baseline net:    +8,147.11 GOLD price points
Baseline wins:   1,430
Baseline losses: 2,427
Baseline flats:  1
```

The result is an M1/H4 idealized research reconstruction, not an actual-tick MT5
report and not dollar P/L.

## 2. Primary result under the current V13 objective

With Child #1 unchanged and proof/lock/timeout applied only to Child #2..#10:

| Metric | Baseline 0 | HA-9 candidate | Change |
| --- | ---: | ---: | ---: |
| Children | 3,858 | 3,858 | 0 |
| Winning Children | 1,430 | **2,151** | +721 |
| Losing Children | 2,427 | **1,685** | **-742 (-30.6%)** |
| Flat | 1 | 22 | +21 |
| Non-flat win rate | 37.08% | **56.07%** | **+18.99 pp** |
| Net points | +8,147.11 | +3,946.06 | -4,201.05 |
| Profit Factor | 1.19995 | 1.17634 | -0.02361 |
| Trade-sequence max DD | 3,756.99 | **1,283.65** | **-65.8%** |
| Max consecutive losses | 25 | **14** | **-44.0%** |

The reduction in total net points is real and is not hidden. Under the current
loss-frequency-first objective it is a secondary cost, not an automatic veto.

## 3. Year diagnostics

| Year | Baseline net | HA-9 net | Baseline win rate | HA-9 win rate | HA-9 PF |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2024 | -359.23 | **+37.15** | 33.02% | **54.03%** | 1.0082 |
| 2025 | +4,506.73 | **+1,867.48** | 40.17% | **58.29%** | 1.2517 |
| 2026 | +3,999.61 | **+2,041.43** | 38.69% | **55.91%** | 1.1953 |

The important change is that the ordinary Child stream becomes majority-winning
in all three year slices; 2024 moves from negative to slightly positive in the
idealized reconstruction.

## 4. Typical-block quality

Chronological non-overlapping trade blocks:

| Block | Baseline positive share | HA-9 positive share | Baseline median | HA-9 median |
| --- | ---: | ---: | ---: | ---: |
| 10 trades | 40.0% | **50.65%** | -25.56 | **+0.85** |
| 25 trades | 47.40% | **57.79%** | -14.86 | **+17.18** |
| 50 trades | 51.95% | **61.04%** | +5.96 | **+18.65** |
| 100 trades | 55.26% | **71.05%** | +84.44 | +69.93 |

The 25- and 50-trade medians are especially relevant to the revised objective:
the typical block moves from flat/downward to positive.

Monthly positive-month count stays 22/32 for both variants, but the worst month
improves from `-1,386.77` to `-427.47` points.

## 5. Large-winner trimming

This is now a robustness diagnostic rather than a veto rule.

After removing the most profitable Journeys from each variant independently:

| Top profitable Journeys removed | Baseline | HA-9 |
| --- | ---: | ---: |
| 1 | +5,028.99 | +2,796.03 |
| 3 | +862.83 | +2,039.59 |
| 5 | **-1,504.63** | **+1,426.97** |
| 10 | **-5,785.30** | **+74.26** |
| 20 | -12,586.28 | -2,246.10 |

The candidate is therefore materially less dependent on the very largest
Journeys even though it deliberately gives up a large amount of their upside.

## 6. Mechanism ablation

Breakout-lock without the one-H4 timeout already changes the loss distribution,
but the timeout is important for ordinary-path stability:

```text
lock only:
  wins 2,114 / losses 1,723 / flats 21
  non-flat win rate 55.10%
  net +4,250.83
  trade-sequence DD 2,056.69
  2024 net -366.95

lock + one-H4 timeout:
  wins 2,151 / losses 1,685 / flats 22
  non-flat win rate 56.07%
  net +3,946.06
  trade-sequence DD 1,283.65
  2024 net +37.15
```

So the timeout is not included because it maximizes total net. It is included
because it reduces unresolved ordinary losses and materially smooths the trade
stream.

## 7. Exit decomposition

```text
BREAKOUT_LOCK: 1,509 Children
PROOF_TIMEOUT:  1,355 Children
ordinary HA exit: 994 Children
```

Child #1 is unchanged and remains under ordinary HA Journey exit.

## 8. Limitations

- Entire 2024-2026 sample is consumed development history.
- M1 OHLC cannot reveal exact tick order inside a minute. The audit therefore
  activates the lock only after the proof M1 and uses gap-aware adverse fills.
- Spread, slippage, swap, commissions, broker stop/freeze mechanics and order
  rejection are not in this idealized price-point receipt.
- The new EA uses next-tick virtual locks and market closes, so actual-tick
  tester economics may differ from M1 reconstruction.
- No threshold/window optimization is justified from this receipt.

## 9. Reproduction hashes

```text
GOLD# H4 source: 5e12fa91f974c0f15e340ea8116bd9168fc6821e6309592cee1a7e197675de09
GOLD# M1 source: 626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2
audit script:    2b460a844ba913037cf7851ae35a48cf5efc2cc88eab066b32ee194c2b7b59d6
summary JSON:    2cf023fa97d191eb8721aaa7c7026e95d6f9dc2d0aa000017622a7253339333e
```

The hashes above describe the executed audit at receipt creation. If the audit
script or summary is edited after this receipt, regenerate the receipt hashes.
