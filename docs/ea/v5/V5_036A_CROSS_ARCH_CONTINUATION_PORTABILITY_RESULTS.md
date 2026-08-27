# V5-036A — Cross-Architecture Continuation-State Portability Results

Status: `COMPLETED / STAGE-0 PORTABLE / STAGE-1 TRANSFER FAIL`
Date: `2026-08-27`
Strategy authority: `NONE`
Production authority: `NONE`
Parent contract: `V5_036A_CROSS_ARCH_CONTINUATION_PORTABILITY_CONTRACT.md`
Implementation freeze: `V5_036A_EXACT_M30_PORTABILITY_IMPLEMENTATION_FREEZE.md`

## Question

Does the V3 D-145 M30 `protected -> external` maturity state represent an Entry-independent continuation mechanism that can be defined causally and transferred unchanged to the V5 First Cross +1R population?

Inherited directional prediction:

```text
median one_r_m30_range_progress(+2R runner)
<
median one_r_m30_range_progress(exhaust before +2R)
```

No threshold, score, market veto, direction veto, or management change was allowed.

## Stage 0 — portability audit

Classification: `PORTABLE AS A MEASUREMENT DEFINITION`.

Exact code review of the frozen V1 structure engine established that:
- M30 trend, owner, protected and external objects live in the global `V1StructureState`;
- confirmed waves and structure breaks update those objects from closed price bars;
- Root/FVG/scenario construction consumes structure events as downstream side effects;
- the D-146 metric does not require Root ID, FVG ID, or scenario-owned structure identity.

Therefore the concept can be measured on a First Cross trade without importing the V3 Entry architecture.

The transfer implementation reproduced the exact V1 M30 state semantics, including pre-bar structure-break ordering and causal 3-bar wave confirmation. A generic pivot approximation was not used.

### Initialization / non-backfill QA

Frozen +1R population: `223`.

Canonical valid M30 state:

```text
122 / 223 = 54.7085%
```

Coverage by market:

```text
BTCUSD#   38 / 75
GOLD#     35 / 57
USDJPY#   25 / 47
XAUEUR#   24 / 44
```

State-only replay was restarted 7, 14, 30 and 60 days later. Wherever both canonical and delayed-start replay had a valid state, trend/protected/external matched exactly for every delayed start.

No additional warm-up exclusion was introduced.

Implementation-freeze SHA-256:

```text
d80c5d80caf391d570e58c579a6db41524c69e3b38a049f775e59f585795043d
```

## Stage 1 — inherited transfer falsification

Valid population: `122`.

Pooled result:

```text
+2R runners N                 59
exhaust N                     63
runner median progress        1.007361
exhaust median progress       0.964935
runner - exhaust median gap  +0.042426
inherited sign                FALSE
```

The pooled relationship is reversed relative to D-145.

### Market breadth

| Market | N | Runner N | Exhaust N | Runner median | Exhaust median | Inherited sign |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| BTCUSD# | 38 | 18 | 20 | 0.941167 | 0.966904 | TRUE |
| GOLD# | 35 | 13 | 22 | 1.000000 | 1.003934 | TRUE |
| USDJPY# | 25 | 12 | 13 | 1.016991 | 0.964539 | FALSE |
| XAUEUR# | 24 | 16 | 8 | 1.058855 | 0.697649 | FALSE |

Only `2 / 4` comparable markets preserve the inherited sign. The GOLD# difference is very small; no threshold is introduced to reinterpret it.

### Year breadth

| Year | N | Runner N | Exhaust N | Runner median | Exhaust median | Inherited sign |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 2023 | 40 | 23 | 17 | 0.859441 | 0.994407 | TRUE |
| 2024 | 41 | 16 | 25 | 1.033128 | 0.966109 | FALSE |
| 2025 | 41 | 20 | 21 | 1.008596 | 0.918574 | FALSE |

Only 2023 preserves the inherited sign. Both later years reverse it.

### Direction breadth

| Direction | N | Runner N | Exhaust N | Runner median | Exhaust median | Inherited sign |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| LONG | 71 | 34 | 37 | 1.003863 | 0.964935 | FALSE |
| SHORT | 51 | 25 | 26 | 1.023013 | 0.936404 | FALSE |

Both directions reverse the D-145 prediction.

Comparable breadth:

```text
comparable cells   9
supporting cells   3
STRONG TRANSFER    FALSE
```

Transfer-ledger SHA-256:

```text
29d7db046f1892ae954752f8d55ca9214748329a920960c92da082d3b86fb275
```

Summary JSON SHA-256:

```text
b4752105c7c8bb47392dee9f2277142174c8f27bf0208e08bd900a6cbcbfa60b
```

## Interpretation

The measurement itself is Entry-independent enough to be transported, but its predictive relationship is not.

This distinction matters:

```text
portable observable
!=
portable edge
```

D-145's M30 maturity relation was stable inside the V3 continuation architecture. It did not reproduce as a broad continuation discriminator inside First Cross.

The transfer failure is especially material because:
- pooled sign reverses;
- 2024 and 2025 reverse;
- LONG and SHORT both reverse;
- XAUEUR# reverses strongly.

No market or direction may be removed to rescue the relationship.

## Classification / action

```text
STAGE 0: PORTABLE MEASUREMENT
STAGE 1: CROSS-ARCHITECTURE TRANSFER FAIL

D-145 M30 maturity is NOT supported as an
Entry-independent continuation mechanism.
```

Under the preregistered V5-036A contract:
- close First Cross payoff-rescue research;
- do not tune a progress threshold;
- do not select markets/directions from this result;
- do not create a management rule from this development transfer;
- reopen success-first discovery under the D-180 payoff objective.

V5-030A and V5-034A remain preserved research history only. GOLD# 2021 remains untouched.
