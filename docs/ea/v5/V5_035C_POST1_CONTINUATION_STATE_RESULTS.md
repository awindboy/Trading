# V5-035C — Post-1R Continuation-State Falsification Results

Status: `COMPLETED / SHADOW-ONLY / NO RULE PROMOTION`
Date: `2026-08-27`
Preregistration SHA-256: `919b2e0ae03f22e55a37f14db4ef81b0b40f72e556e655b03e26e395080b5c43`

## Population

```text
clear +1R N                    223
conservative >=2R continuation 45.29%
```

At +1R only the latest completed 240m bar was used.
No threshold, conjunction, or score was searched.

## H1 — slow regime alive

Definition:

```text
direction * slow > 0
```

Pooled:

```text
alive       N 190 / >=2R 50.00%
not alive   N  33 / >=2R 18.18%
difference               +31.82pp
```

Market differences were positive in all four development markets.
Year differences were positive in 2023, 2024, and 2025.

But direction was not stable:

```text
SHORT difference   +3.14pp
LONG difference   +54.44pp
```

H1 remains an interesting descriptive hypothesis, not a rule.

## H2 — fast momentum aligned

Pooled difference:

```text
+7.33pp
```

The relationship was near zero or reversed in some markets and reversed by direction.

Classification: `WEAK / UNSTABLE`.

## H3 — price on favorable EMA20 side

Pooled difference:

```text
+8.02pp
```

It reversed in some markets and in 2025.

Classification: `WEAK / UNSTABLE`.

## Conclusion

The original First Cross oscillator/EMA state does not provide a sufficiently broad stable post-1R continuation
discriminator to justify adaptive management from this development set.

Do not create:
- slow-alive runner rules;
- direction exceptions;
- combined scores;
- new thresholds.
