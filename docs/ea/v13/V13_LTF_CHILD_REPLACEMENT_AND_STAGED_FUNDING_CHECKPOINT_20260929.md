# V13 LTF Child Replacement + Staged Funding Checkpoint — 2026-09-29

Status: `LTF REPLACEMENT PROMISING SHADOW / STAGED FUNDING NOT PROMOTED`

## Architecture tested

The key change is to stop restricting research to the old SA-1 add-on ledger. Every qualifying PHA-internal LTF pullback can create an independent Child opportunity.

### K0 — better-price LTF Child

```text
Child1 remains unchanged.
Old SA-1 add-on lane is removed.
LTF opportunity -> 1 unit entry.
Exit -> first later breach of prior survived correction envelope;
        otherwise opposite H4 HA flip.
```

### K1/K2 — staged funding

```text
initial LTF Child = 1 unit
if prior M30 impulse extreme is actually rebroken before exit:
    K1: add +1 unit
    K2: add +2 units
all units share the same first-breach/H4-flip exit horizon
```

No model is needed for the proof event.

## 2024-2026 dollar economics

```text
SA-1 actual-tick reference
Net +$2,791.87 / PF 1.215 / DD $971.77 / WR 50.17% / loss streak 10

K0: Child1 + LTF replacement
Net +$5,181.93 / PF 1.197 / DD $1,716.49 / WR 38.74%
Avg W +$27.12 / Avg L -$14.33 / payoff 1.89 / loss streak 22

K1: K0 + one proof unit
Net +$8,010.66 / PF 1.235 / DD $2,281.66 / WR 34.61%
Avg W +$40.49 / Avg L -$17.35 / payoff 2.33 / loss streak 25

K2: K0 + two proof units
Net +$10,839.39 / PF 1.256 / DD $2,846.83 / WR 33.71%
Avg W +$52.60 / Avg L -$21.30 / payoff 2.47 / loss streak 25
```

### Year net

```text
             2024        2025        2026
K0         +$289.25   +$2,113.78  +$2,778.90
K1         +$608.98   +$2,584.51  +$4,817.17
K2         +$928.71   +$3,055.24  +$6,855.44
```

## Why K0 is more important than K1/K2

K0 directly addresses the research hypothesis: create Children on PHA-internal pullbacks at better prices rather than chasing new completed H4s. It improves payoff dramatically relative to SA-1 add-ons.

K1/K2 improve consumed 2024-26 dollars but reintroduce a right-tail/low-WR profile and materially increase DD and loss streaks.

## Historical stress

LTF lane only, same mechanics on 2022/2023 consumed history:

```text
K0
2022 +$59.93  PF 1.031
2023 +$54.91  PF 1.027

K1
2022 -$170.19 PF 0.944
2023 -$148.51 PF 0.954

K2
2022 -$400.31 PF 0.906
2023 -$351.93 PF 0.921
```

This is the decisive warning: the broad better-price lane itself does not collapse historically, while aggressive proof funding does. Therefore staged funding is not authorized.

## Ordinary block quality

K0 replacement:

```text
10-trade positive 44.7%, median -$12.19
25-trade positive 49.2%, median  -$0.23
50-trade positive 56.7%, median +$34.45
100-trade positive 63.3%, median +$118.15
```

K1/K2 increase the tail but worsen short-block medians and loss streaks. This conflicts with V13's current ordinary-equity-first doctrine and is another reason not to promote them yet.
