# V13 Intra-HA LTF Pullback + POI Anatomy Checkpoint — 2026-09-29

Status: `CONSUMED-DATA CAUSAL RESEARCH / NOT STRATEGY AUTHORITY`

## Question

H4 Heikin-Ashi intentionally hides smaller raw-price pullbacks. The study therefore keeps H4 HA as the PHA/Parent trend container but observes **raw M30/M15** structure inside a same-color H4 HA run.

The purpose is twofold:

1. identify early runner deterioration before H4 HA flips;
2. create Children at better prices inside a PHA instead of adding after price has already extended into another completed H4.

## Causal LTF representation

- M30 primary swings use the historical V9 confirmed-pivot idea: two left bars + two right bars; a pivot is usable only after both right bars complete.
- M15 POI geometry reuses the V9 mechanical FVG/OB definitions rather than inventing discretionary rectangles.
- All magnitude variables may be stored in raw price and H4 ATR180-normalized form.
- Same-timestamp overlapping FVG/OB objects are clustered into one market opportunity for execution studies.
- No Fibonacci threshold, ATR offset, minimum-R, cooldown, retry limit or side/year exception is introduced.

## Anatomy result

The useful state is not "POI exists". The useful representation is:

```text
M30 impulse
-> M30 raw pullback location/depth
-> M15 fresh POI interaction
-> reaction/acceptance state
-> re-expansion or H4 reversal
```

Earlier object-level diagnostics showed that, at comparable pullback depth, primary-direction POI rejection is materially more continuation-like than acceptance-through. But this is **context**, not a hard entry rule; year-by-year strategy economics showed no stable rule such as `REJECT = always trade` or `ACCEPT = always veto`.

## Dynamic correction envelope

A stronger parameter-free coordinate emerged:

```text
prior survived correction envelope
= maximum depth already survived by earlier successful correction cycles
  in the current H4 HA run

current correction <= prior envelope
= within previously demonstrated tolerance

current correction > prior envelope
= first deterioration beyond previously demonstrated tolerance
```

This avoids fixed 38.2/50/61.8% or ATR thresholds.

The current implementation is still incomplete because the envelope is derived from POI-linked M30 episodes. The next research must build it from **all raw M30 corrections**, whether or not a qualifying POI interaction occurred.

## First-breach protection

Waiting until a POI is fully accepted was too late. A more effective protection event was simply the first later correction that breaches the prior survived envelope. If no such event occurs, fallback remains the opposite H4 HA flip.

This event materially improved the LTF lane relative to the older H4-flip-only hold and became the current LTF exit representation.

See:

- `results/v13_ltf_first_breach_clusters.csv`
- `results/v13_ltf_staged_proof.csv`
- `research/v13/rebuild_first_breach_ml.py`
