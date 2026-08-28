# V6 Development Handoff

Last updated: `2026-08-29`  
Expected base GitHub HEAD for this overlay: `982839b0a1ea166fc534272f2024a72cedfb8326`  
Current phase: `V6-003 DIRECTIONAL-PRIOR EXTERNAL-VALIDATION PREP`  
Current production authority: `NONE`  
Current promoted production candidate: `NONE`  
Current research benchmark: `MENV-004 PRETRADE SCALE x ACCEPTANCE H`  
Current directional validation candidate: `P2 H1 DISP24 x MENV HIGH_HIGH`  
Untouched reserve: `GOLD 2021`

## 1. Mandatory startup

Read in order:

1. latest GitHub HEAD;
2. root `AGENTS.md`;
3. root `docs/ea/HANDOFF.md`;
4. `docs/ea/WORKFLOW_AND_ZIP_HANDOFF.md`;
5. `docs/ea/v6/AGENTS_V6.md`;
6. this handoff;
7. `RESEARCH_STATE_V6.md`;
8. `V6_002_MULTI_ENVIRONMENT_RESEARCH_RESULTS.md`;
9. `V6_003A_DIRECTIONAL_PRIOR_RESEARCH_CONTRACT.md`;
10. `V6_003A_DIRECTIONAL_PRIOR_ATLAS_FREEZE.md`;
11. `V6_003A_DIRECTIONAL_PRIOR_RESULTS.md`;
12. `DECISIONS_V6.md`;
13. `BACKLOG_V6.md`.

GitHub wins over chat memory.

## 2. Permanent research frame

Consumed research panel:

```text
GOLD 2022-2025
XAUEUR 2023-2025
USDJPY 2023-2025
BTCUSD 2023-2025
```

GOLD 2021 remains untouched.

V3 remains deterministic substrate/control, not universal truth. No outcome-driven market selection, threshold rescue, H/L inversion, or cross-stage variable migration.

## 3. Current benchmark

MENV-004:

```text
620 broad-direct causal-valid
540 state-valid
163 HIGH_HIGH parents
151 fills
144 exposure accepted
48 positive
WR 33.33%
avg positive +3.484R
EV +0.494792R
total +71.25R
12/13 market-years positive
```

MENV-004 state:

```text
scale      = planned H risk / causal completed D1 ATR14
acceptance = M5 acceptance margin / same D1 ATR14

HIGH_HIGH =
    scale > earlier same-market median(scale)
AND acceptance > earlier same-market median(acceptance)
```

History warmup remains 20.

## 4. Critical V6-003A implementation correction

Directional-prior work re-established the benchmark from raw M1 before interpreting outcomes.

Correct D1 rule:

```text
calendar D1 resample
-> ATR14
-> each D1 ATR becomes available at next calendar-day boundary
```

Do not add a separate rule that removes the first observed D1 bar merely because its raw history begins away from midnight.

Correct pending H fill rule:

```text
first eligible M1 index =
searchsorted(trigger_time, side="right")
```

The pending order cannot fill on the trigger timestamp M1.

With these rules, every 13-environment MENV result row matches authority exactly.

## 5. V6-003A frozen atlas

Before the local event finalizes direction, at `sweep_time`:

```text
P1 H1 DMI14 direction
P2 H1 24-bar signed displacement
S1 H1 BOS owner
S2 M30 BOS owner
S3 H1/M30 concordant owner
```

Counts over 620:

```text
P1 202 aligned / 418 opposed
P2 220 aligned / 400 opposed
S1 223 aligned / 397 opposed
S2 166 aligned / 454 opposed
S3 119 aligned / 350 opposed / 151 neutral
```

P1/P2 absolute direction agreement = 84.52%.

## 6. V6-003A result

### P1 closed

P1 broad raw-path aligned/opposed:

```text
+1R 46.88% / 46.45%
+3R 24.48% / 23.10%
+5R 16.15% / 15.99%
```

When P1 and P2 disagree, simple displacement wins clearly.

Do not try P1 ADX gates, magnitudes or nearby H1 windows to rescue it.

### P2 broad not promoted

P2 broad:

```text
ALIGNED 210 fills:
+1 49.05% / +3 26.67% / +5 18.57%

OPPOSED 376:
+1 45.21% / +3 21.81% / +5 14.63%
```

Broad recurrence is too weak and the effect is SHORT-concentrated.

### P2 x HIGH_HIGH retained for external validation

Within 151 HIGH_HIGH fills:

```text
P2 ALIGNED N53:
+1 58.49%
+3 41.51%
+5 35.85%

P2 OPPOSED N98:
+1 50.00%
+3 28.57%
+5 19.39%
```

+5R aligned-minus-opposed:
- BTCUSD +26.15pp
- GOLD +20.11pp
- USDJPY +18.05pp
- XAUEUR -2.75pp

This is best interpreted as a possible **cross-scale continuation-capacity** interaction.

It is not validated.

## 7. Why no strategy was frozen

The exact accepted MENV split is:

```text
P2 aligned: N51 / WR 41.18% / avg+ 3.786R / EV +0.971R
P2 opposed: N93 / WR 29.03% / avg+ 3.250R / EV +0.234R
```

An aligned-only strategy would collapse 144 -> 51 and still miss the 50% WR target.

The required complementary OPPOSED mechanism was tested rather than assumed. After local structural failure, prior-direction 24h endpoint is positive only 45.6% in HIGH_HIGH P2-opposed cases. Automatic inversion is closed.

Therefore V6-D032 is respected: no disguised veto is promoted.

## 8. Statistical / falsification status

For P2 aligned-minus-opposed inside HIGH_HIGH:

```text
+5R observed delta +16.46pp
13-environment cluster bootstrap 95% approximately +0.18pp to +33.16pp
market-year x direction stratified permutation one-sided p approximately 0.061
```

This is suggestive but not independent proof.

Continuous scale/acceptance is somewhat stronger in aligned events, so residual MENV-strength confounding remains plausible.


## 9. V6-003B/C — actual direction-first indicator research

The earlier V6-003A pass was not sufficient because it mostly classified an already-directed event as aligned/opposed.

V6-003B corrected the architecture:

```text
completed HTF prior -> LONG / SHORT / NEUTRAL
-> later local sweep/M5 structure confirms prior-direction timing
-> structural Entry/SL
```

The pre-direct local universe contains 1391 geometry-valid reactions: 620 direct-transfer and 771 non-direct.

### Broad recovery test failed

Using a prior to own direction did **not** make `m1_direct_transfer` disposable.

Broad accepted EV:
- H1 DMI: -0.128R
- H1/H4 DMI: -0.106R
- H1/H4 MACD: -0.020R
- H1 DISP24: -0.027R
- H1/M30 structure: -0.018R

Do not remove direct local-transfer quality to manufacture N.

### Direct-confirmation direction priors

Unconditional direct event control:

```text
560 accepted / EV -0.055R
```

Direction-first direct:

```text
MACD H1/H4: 146 accepted / EV +0.110R
DISP24:      209 accepted / EV +0.133R
RSI14 H1/H4:117 accepted / EV +0.150R
```

So a causal prior can separate direction before local confirmation.

But named indicators do not survive simpler controls.

RSI14 H1/H4 and same-period DISP14 H1/H4 agree 99.18%; DISP14 direct is stronger:

```text
90 accepted
WR 30.0%
avg+ 3.25R
EV +0.275R
total +24.75R
```

Only 8/13 market-years are positive and several cells are tiny. This is a clue, not authority.

Read `V6_003BC_DIRECTION_FIRST_INDICATOR_RESULTS.md` before further direction work.

## 10. Current conclusion

Closed as independent direction edges on this consumed panel:
- H1/H4 DMI;
- H1/H4 MACD;
- H1/H4 Aroon25;
- H1/H4 Vortex14;
- H1/H4 RSI14.

Reason: none provides convincing recurrent information beyond simpler signed price displacement.

Do not rescue with nearby windows, RSI 70/30, ADX gates or indicator voting.

The surviving architectural clue is **multi-horizon directional persistence**, not a named conventional indicator.

## 11. Exact next task

Do not return to exit tuning and do not run another conventional-indicator tournament.

Next child must preregister a directional-state mechanism explaining continuation versus reversal of multi-horizon persistence before outcomes.

Requirements:
1. preserve direction-first causal timestamp at sweep time;
2. retain direct local structure as timing/geometry unless separately disproved;
3. do not tune DISP14/24 windows;
4. explicitly model why prior persistence should continue or fail under local counter-move / volatility regime;
5. use the same 13 consumed environments for falsification only;
6. seek additional outcome-blind data before promotion;
7. keep GOLD 2021 untouched.

No production authority exists.

## 12. New reproducibility files

- `V6_003B_DIRECTION_FIRST_FREEZE_PRE_OUTCOME.md`
- `V6_003C_CONVENTIONAL_DIRECTION_ATLAS_FREEZE.md`
- `V6_003C_RSI_SIMPLER_CONTROL_FREEZE.md`
- `V6_003BC_DIRECTION_FIRST_INDICATOR_RESULTS.md`
- `scripts/v6_003b_direction_first.py`
- `scripts/v6_003c_attach_and_test.py`
- `scripts/v6_003c_rsi_control.py`
- corresponding V6-003B/C ledgers under `docs/ea/v6/ledgers/`.

## 13. Hard restrictions

- no GOLD 2021;
- no conventional indicator period/threshold rescue;
- no RSI 70/30 rescue on consumed data;
- no displacement-window tournament;
- no dropping direct-transfer merely to increase N;
- no indicator-only Entry;
- no automatic opposed inversion;
- no production EA change;
- no exit tuning in this phase.
