# V3 Development Handoff

Last updated: `2026-08-27`
Repository base before V3 bootstrap: `0e7b1d5b39de1126394e88f85abf87cde167fc84`
Current phase: `V3-003F DUAL RELOAD DISCOVERY FREEZE COMPLETE / 2022 VALIDATION NEXT`
V1: `FROZEN`
V2: `PAUSED / PRESERVED CONTROL`
2021: `KEEP UNTOUCHED`

## Startup order

On every V3 session:

1. Check latest GitHub commit.
2. Read root `AGENTS.md`.
3. Read `docs/ea/v3/AGENTS_V3.md`.
4. Read root `docs/ea/HANDOFF.md`.
5. Read this file.
6. Read `RESEARCH_STATE_V3.md`.
7. Read `V3_RAW_DATA_LAB_PROTOCOL.md`.
8. Read `BACKLOG_V3.md`.
9. Inspect the latest V3 experiment/result documents and code.

If chat conflicts with GitHub, GitHub wins.

## Why V3 exists

V2 successfully separated execution, Entry survival, winner continuation and exit
architecture, but current deterministic Entry generation remains sparse and unstable.

Recent GOLD frequency:

```text
2024: 52 fills
2025: 55 fills
```

FULL_AUDIT showed the scarcity is not simply lack of market activity:

```text
2025 GOLD#
804 PLAN
466 Root contact
363 Sweep accepted
165 current CHOCH
68 distinct execution geometries
55 Fill
```

The current chain therefore compresses a much larger reaction population.

V3 does not assume this compression is correct.

## D155 lesson carried into V3

D155 found a semantic tension:

- mentor research describes small-timeframe `live structure` transition and allows
  a role for M5/M1;
- current deterministic V2 is M1-only and scenario CHOCH depends on the inherited
  global protected-structure detector;
- the three-opposite-colour-candle wave detector is an operational formalization,
  not something V3 must preserve.

This does not authorize a replacement trigger by itself.

It motivates rebuilding the opportunity universe from raw market data instead of
studying only V2 fills.

## Active data allocation

```text
GOLD# 2023-2025
    V3 discovery/development

2022
    validation vault

2021
    untouched
```

Initial discovery starts with M1 bars.

Tick data is requested only after candidate hypotheses survive fast replay.

## Immediate task

User provides:

```text
GOLD# M1 CSV
2023-01-01 through 2025-12-31
broker/server timestamps
OHLC + tick volume + real volume + spread
```

Preferred: one CSV per year or one continuous CSV, compressed in ZIP.

Do not upload internal HCC/TKC binaries as the primary exchange format unless
explicitly requested. Export broker data to CSV first.

After upload:

1. verify date coverage and row ordering;
2. identify broker-server timezone/session discontinuities;
3. verify spread field and symbol precision;
4. rebuild M5/M15/M30/H1/H4 from M1;
5. build candidate swing/liquidity/sweep/zone/trigger universe;
6. produce the first opportunity-density census;
7. only then begin strategy-family experiments.

## V2 disposition

Do not delete V2.

V2 remains the reference for:
- deterministic causal infrastructure;
- execution behavior;
- D151/D154 instrumentation;
- SP/V3E exit work;
- prior negative results;
- comparison against any eventual V3 candidate.

Do not continue D154P/D155 filter mining while V3-001 is active unless explicitly
reopened.

## Result-document rule

Every major V3 experiment gets its own immutable result document.

Phase changes update this HANDOFF.

Important V3 architectural decisions append to root `docs/ea/DECISIONS.md`.

## V3-002 / V3-003 routing update ??2026-08-25

The first GOLD-only offline discovery cycle is now synthesized in:

```text
V3_002_GOLD_OFFLINE_RESEARCH_SYNTHESIS.md
```

The main result is a **fundamental research pivot**, not a promoted Entry rule.

Key conclusions:
- sweep alone has almost no alpha;
- local structure acceptance matters more than sweep alone;
- FVG may remain a displacement footprint, but mandatory FVG-retest Entry is not supported;
- event geometry without direction/state context has no stable directional edge;
- fixed momentum-horizon direction and trade-level ML classification did not generalize;
- selective continuation when HTF context and reaction agree remains promising but sparse and temporally unstable;
- bad quarters represent different failure mechanisms;
- broad SL widening is not authorized;
- winner continuation remains a separate useful research problem.

Active next phase:

```text
V3-003 GOLD AUCTION-STATE RECONSTRUCTION
```

Read:
1. `V3_002_GOLD_OFFLINE_RESEARCH_SYNTHESIS.md`
2. `V3_003_GOLD_AUCTION_STATE_RECONSTRUCTION_PLAN.md`
3. `V3_RESEARCH_GOVERNANCE_ADDENDUM.md`

Current scope is **GOLD FIRST**.

The previously prepared cross-market exporter is deferred. Do not pivot the active research
line to other markets before GOLD has either:
- a coherent candidate architecture; or
- a documented structural ceiling followed by explicit user approval.

2022 remains the validation vault.
2021 remains untouched.



## V3-003C routing update — 2026-08-26

Read:

```text
V3_003C_RELOAD_STATE_ACCEPTANCE_RESULTS.md
```

V3-003C produced the first fully reproducible reload-continuation development candidate in
this V3 line.

Reference interaction:

```text
active higher delivery state
+
intermediate persistent-liquidity reaction
+
decisive local M5 acceptance
```

where decisive acceptance means:

```text
acceptance beyond the actually broken M5 structure level
>
source-liquidity penetration beyond the swept level
```

Reference M15-k2 Level-A results:

```text
2023 40 / 60.0%
2024 29 / 65.5%
2025 27 / 63.0%
```

Exact mirrors are materially weaker in all three years.

Important authority boundary:
- delivery state alone is not promoted;
- local acceptance alone is not promoted;
- the observed development edge is the interaction;
- no production Entry/SL/TP/EA change is authorized;
- no quarter/session/direction/objective-room veto is authorized;
- forced reversal remains unapproved.

Freeze the exact reference as:

```text
V3_RELOAD_CANDIDATE_A
```

for future comparison. New correction-completion ideas must be separate variants and must
not rewrite Candidate A.

2022 remains closed until independent validation is intentionally run under the frozen
candidate. 2021 remains untouched.
## V3-003D routing update — 2026-08-26

Read first:

```text
V3_003D_DUAL_RELOAD_MODULE_RESEARCH_SYNTHESIS.md
```

Current active research is no longer "find one final reload rule".

The reload line is now split into two **parallel research modules**:

```text
MODULE L — LOW-R / HIGH-WR
    virtual Candidate-A failure
    -> higher context survives
    -> deeper intermediate liquidity
    -> atomic same-bar sweep/recovery
    -> fresh M5 re-acceptance
    -> real high-precision Entry

MODULE H — HIGH-R / LOW-WR
    Candidate A
    -> clean M1 ownership path
    -> post-trigger structural pullback
    -> same sweep-extreme SL
    -> 5R asymmetric payoff research
```

Important routing boundaries:

- `V3_RELOAD_CANDIDATE_A` remains the frozen common development benchmark.
- Module L and Module H are **research candidates only**.
- Current-session Module L/H numbers are discovery evidence until dedicated scripts and
  immutable ledgers are committed and reproduce them.
- Do not collapse Module L and Module H into one score/filter.
- Do not reuse Module-L variables as Module-H gates or vice versa without independent
  stage-specific validation.
- Do not loosen M5 correction-completion merely to increase trade count.
- Do not treat delayed recovery as equivalent to atomic same-bar rejection.
- Do not restore mandatory FVG-retest Entry.
- Do not widen SL merely because higher context survives after a stop.
- Do not treat fixed 10R as a proven mentor objective.
- Do not start compression-breakout / failed-auction-reversal modules yet; the user wants
  the two current reload modules researched more deeply first.
- 2022 remains closed.
- 2021 remains untouched.
- No production EA change is authorized.

The next session's first concrete task is **reproducibility**, not another strategy idea:
commit dedicated Module-L / Module-H replay scripts and physical event ledgers, then continue
their separate failure-taxonomy and non-overfit improvement work.

## V3-003E routing update — 2026-08-26

Read immediately after V3-003D:

```text
V3_003E_DUAL_RELOAD_REPRO_AND_IMPROVEMENT_RESULTS.md
```

V3-003E supersedes the stale V3-003D statement that Module L/H replay parity is still the
next research task.

The integrated replay is now committed as:

```text
scripts/v3_003e_dual_module_repro.py
```

with immutable discovery ledgers under:

```text
docs/ea/v3/ledgers/
```

Required startup parity:

```text
Candidate A:
2023 40
2024 29
2025 27

Module L:
11 physical trades
11 checkpoint hits
10 full +1R hits
1 exact-mirror checkpoint
7 residual +2R hits under current payoff

Module H base k2 / 50%:
48 fills
14 TP5
31 SL
3 BE

Module H direct-transfer:
44 fills
14 TP5
27 SL
3 BE

Module H direct-transfer + not-BOTH shadow:
40 fills
14 TP5
23 SL
3 BE

H -> L recovery links:
5
4 net-positive after current L payoff
```

Current Module-L primary payoff:

```text
checkpoint=min(1R,0.5 D1 ATR)
-> realize 50%
-> residual BE
-> residual +2R
```

Current Module-H research hierarchy:

```text
H0 broken-level retest
H1 50% accepted-leg pullback
H2 direct M1 ownership-transfer eligibility
H3 direct + BOTH-exclusion SHADOW ONLY
```

`direct transfer` has stronger evidence than `BOTH exclusion`.
Do not freeze BOTH exclusion yet because the reference H-fill sample does not provide a
meaningful independent 2025 BOTH test.

The previous session ended with **two H experiments started but unfinished**:

1. body-close back through the original swept-liquidity level as a stronger post-fill H
   invalidation;
2. +2R existing-50%-fraction protection before +3R-BE / +5R.

Resume those two experiments first after parity verification. Do not assume either result.

Other market-state modules remain deferred. 2022 remains CLOSED. 2021 remains untouched.
No production EA change is authorized.

## V3-003F routing update — 2026-08-27

Read first:

```text
V3_003F_DUAL_RELOAD_DISCOVERY_FREEZE.md
V3_003F_VALIDATION_CONTRACT.md
```

The 2023-2025 dual-reload discovery cycle is intentionally stopped.

Frozen Level-A validation candidate:

```text
V3_DUAL_RELOAD_CANDIDATE_B
```

Candidate B uses:
- Candidate-A M15 adaptive k=2 substrate;
- Module H2 direct-transfer with 50% pullback;
- H +3R 25% harvest, residual BE, final +5R;
- primary Module L protected-runner architecture;
- same-direction coexistence allowed / opposite-direction coexistence blocked.

Important corrections/final decisions:
- the two interrupted H experiments are complete and rejected as primary improvements;
- H3/BOTH remains shadow-only because no 2025 BOTH observation exists even in the mentor-wave cross-check;
- previous standalone-L/non-overlap wording was too strong: H/L and H/H active exposure overlaps exist;
- exposure ordering is now explicit for validation;
- do not mine another 2023-2025 gate or payoff tweak before 2022 validation.

Next strategy-research action is the frozen one-time 2022 Level-A validation. Do not retune on failure.
2021 remains untouched. No EA change is authorized.
