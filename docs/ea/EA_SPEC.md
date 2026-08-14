# Mentor Baseline EA Specification

Status: DRAFT
Authority: `AGENTS.md`

## Rule Classification

- D — deterministic as currently specified
- H — heuristic threshold/definition must be chosen
- U — unresolved discretionary rule
- X — excluded from baseline

## 1. Timeframes

Map:
- H1
- M30

Refinement:
- M30
- M15
- M5

Correction context:
- M5

Trigger:
- M1

H4 is excluded from the baseline.

Only information available from closed bars may authorize a decision.

## 2. Market Structure

Status: TBD

Inputs:
- H1/M30/M15/M5/M1 OHLC

Outputs:
- external protected high
- external protected low
- internal swings
- trend direction
- dealing range
- EQ

Deterministic definition:
TBD after comparison with:
- `mentor_engine/structure.py`
- `ICTCockpitIndicator.mq5`
- `MentorScenarioTraderEA.mq5`

## 3. Liquidity

Status: TBD

Required semantic condition:
A liquidity level must represent a plausible participant stop pool.

Supported concepts from current research:
- external swing
- defended range edge
- reaction trap
- trendline cluster
- meaningful internal liquidity

Recent pivot alone is insufficient.

Deterministic implementation:
TBD.

## 4. HTF Root OB

Status: TBD

Must:
- exist before trigger
- be near meaningful structure
- originate displacement
- cause meaningful structure delivery/body break
- remain fresh/valid
- align with objective direction

HTF FVG alone cannot be the initial source.

Implementation:
TBD.

## 5. Causal LTF Refinement

Status: TBD

At least one child OB is required.

Child must:
- share direction
- overlap / be contained / belong to adjacent substructure
- explain the same price event
- belong to the same displacement
- have valid formation timing
- create lower-TF structure delivery

Implementation:
TBD.

## 6. Sweep

Status: TBD

Candidate definition:
wick/liquidity penetration followed by recovery without a valid body structure break.

Additional maturity rules:
TBD.

## 7. M1 CHoCH

Status: TBD

Must:
- happen after refined source contact
- break meaningful live M1 structure
- use body close
- belong to expected correction/reaction

Implementation:
TBD.

## 8. Entry

Baseline:
causal execution OB retest.

Exact price:
TBD.

Variants such as initial FVG entry are excluded from baseline unless explicitly promoted later.

## 9. Stop Loss

Must lie beyond:
- sweep extreme
- entry zone distal boundary
- applicable causal source invalidation

Broker spread/tick/stops-level handling:
TBD.

## 10. Objective / TP

Scenario scopes:
- EXTERNAL_CONTINUATION
- INTERNAL_ROTATION
- EXTERNAL_REVERSAL

TP must follow the frozen objective family defined before entry.

Exact deterministic objective selection:
TBD.

## 11. Pending Order Cancellation

Current contract includes:
- source invalidation
- objective delivery before fill
- entry zone consumption / invalidation
- new opposing owner where applicable

Exact state machine:
TBD.

## 12. Explicitly Excluded From Baseline

- AI judgment
- weighted quality scoring
- arbitrary RR fallback
- maximum-R target replacement
- arbitrary time exits
- mandatory extra BOS after CHoCH
- FVG add-on
- discretionary partial profit
- live trading