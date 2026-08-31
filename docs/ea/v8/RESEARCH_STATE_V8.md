# V8 Research State

Status: `ACTIVE / V8-A FROZEN + V8-B LOCAL-SEQUENTIAL RESEARCH`
Date: `2026-08-31`
Production authority: `NONE`
EA authority: `NONE`
Direction authority: `NONE`

## V8-A

`FROZEN / POSITIVE OPEN-DEVELOPMENT EVIDENCE`

Target:

```text
P(reach C0 +/-10 within 15m / 30m / 60m)
```

V8-A remains direction-free.

## V8-B1

`INVALIDATED_BY_HTF_LOOKAHEAD / CLOSED`

Do not deploy old coefficients.

## External direction branch

`DE-SCOPED`

Not active.

## Current V8-B branch

`LOCAL / SEQUENTIAL DIRECTION TARGET RESEARCH`

The project tested whether direction becomes learnable when the target itself is narrowed in the same spirit as V8-A.

### Failed or weak local targets

- 5/10/15/30/60m future-close sign;
- future local slope;
- up/down excursion dominance;
- +/-1, +/-2, +/-3 micro barriers;
- V8-A-weighted direction loss;
- future-magnitude-weighted direction loss;
- simple WAIT 1/3/5m -> recenter -> endpoint sign.

These remained near chance or weakened materially by 2025/2026.

### Independent touch formulation

2024 individual probabilities for `+10 touched` and `-10 touched` were learnable, but the directional difference between them weakened in later years. This indicates substantial shared movement-intensity information.

### Weakest surviving direction clue

The 15m exclusive-direction target:

```text
+10 only
vs
-10 only
```

produced approximately:

```text
2024 0.603
2025 0.556
2026 0.535
```

A simple recent-15m direction-efficiency baseline was roughly:

```text
0.639 / 0.577 / 0.531
```

This is not sufficient for direction authority.

## Sequential result

Fully recentered:

```text
WAIT 1/3/5m
new C0
predict next 5/10/15m endpoint sign
```

remained around AUC 0.50-0.52.

Therefore simple post-event confirmation by endpoint sign is rejected.

## Immediate active test

Combine:

- fixed WAIT 1/3/5m;
- mandatory recentering;
- next 15m `+10 only` vs `-10 only` exclusive direction target;
- full-population evaluation afterward.

## Reserve

`GOLD# 2021 = LOCKED / UNTOUCHED`
