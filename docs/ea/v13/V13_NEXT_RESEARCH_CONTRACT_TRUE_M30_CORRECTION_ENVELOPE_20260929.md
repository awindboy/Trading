# V13 Historical Research Contract — True Raw-M30 Correction Envelope — 2026-09-29

> Completed and rejected as a broad replacement: the all-M30 envelope was
> weaker than the POI-linked lane. See the full chronicle and current q75/q50
> receipt. Do not treat this as the next-work instruction.

Status: `COMPLETED HISTORICAL CONTRACT / BROAD ALL-M30 VARIANT REJECTED`

## Objective

Repair the strongest current LTF mechanism before adding another model or sizing rule.

The current envelope is based on M30 correction episodes that intersect the POI/opportunity pipeline. That can omit valid raw corrections and distort the runner's demonstrated tolerance.

## Required build

For every H4 HA same-color run:

1. process raw M30 bars causally;
2. maintain confirmed primary-direction M30 swing structure;
3. identify every primary impulse and subsequent correction, whether or not a POI is touched;
4. record correction depth, ATR180-normalized depth, duration and resolution;
5. mark a correction as `SURVIVED` only after price causally re-expands through its prior primary extreme before the H4 HA flip;
6. maintain the maximum depth of already-survived corrections as the current envelope;
7. never update the envelope with future success before that success is known.

## Re-test in this order

### A. Descriptive parity

Compare old POI-linked envelope vs true all-correction envelope:

- coverage;
- first breach timestamps;
- breach-before-H4-flip frequency;
- year/side stability;
- remaining MFE and giveback after breach.

### B. K0 LTF Child lane

Keep the entry universe and 1-unit semantics fixed. Change only the runner protection envelope implementation. Report dollars first:

- Net, PF, DD, W/L/flat, non-flat WR;
- Avg W, Avg L, payoff;
- max loss streak;
- 10/25/50/100 trade-block quality;
- year slices;
- top-1/3/5/10/20 profitable H4-run trimmed P/L.

### C. Replacement architecture

Keep Child1 unchanged and replace SA-1 add-ons with the updated LTF lane. Compare directly with SA-1 actual reference.

### D. Only then staged funding

Re-test K1 proof add only after K0 is stable. K2 is downstream and should not be tested first. No ML sizing before K1 survives historical stress.

## Causal prohibitions

- no future swing confirmation before the right bars close;
- no future correction success used to set the current envelope;
- no hindsight Child recovery;
- no fixed Fibonacci/min-R/ATR stop/cooldown/retry threshold created to rescue the result;
- no side/year/ordinal exception;
- do not use 2022/23 as an untouched OOS claim; it is already consumed stress evidence.

## Validation gate

If an updated K0/replacement candidate remains attractive, produce a dedicated MQL5 research EA and run MT5 `Every tick based on real ticks`. Until then all LTF economics remain research proxies rather than execution authority.
