# V12 Phase-1F Parent target-succession contract

Date frozen: `2026-09-24`

Status: `CONSUMED-DEVELOPMENT MECHANISM STUDY / NO TRADE OR SIZING AUTHORITY`

Contract: `v12-phase1f-parent-target-succession-v1`

## Question

Phase 1F tests whether the unresolved V10 state is better described by the
Parent's current objective than by another broad admission filter. It separates:

- an active Parent with an unfinished directional target;
- a completed target for which the next completed-H4 reframe has not yet
  established a successor;
- an actually invalidated Parent;
- no active Parent.

The study does not change V10 admission, exits, Hard SL, units, or Phase-1C
carry. It asks which stopped units and which `>=5R` right-tail capital occupy
each state.

## Frozen target construction

Every Phase-1B canonical journey starts with a monotonic directional progress
frontier at its causal activation price. The origin C1 midpoint and opposite
edge are considered first, in that order, only if they remain strictly ahead
of the frontier when selected.

After a selected target completes, no replacement is inferred intrabar. The
first later completed H4 is an explicit reframe. If no successor exists, every
later completed H4 may reframe again while the same Parent remains active.

An external successor must be an active one-use level from the already-frozen
`PREVIOUS_H4`, `PREVIOUS_DAY`, `PREVIOUS_WEEK`, or `PREVIOUS_MONTH` inventory.
It must be strictly beyond the directional progress frontier. The nearest
price wins. All active objects at the same point-rounded price form one target
cluster, so family names neither break ties nor create a hidden importance
score.

For LONG the frontier can only rise; for SHORT it can only fall. At a reframe it
incorporates the prior frontier, the completed target, and the causal completed-
H4 close. This prevents a retracement from relabeling an already traversed
price as a new forward objective.

## Causal timing

- internal C1 targets complete on their first causal M1 touch;
- external targets complete on the Phase-1B strict point-rounded M1 breach;
- a completion timestamp equal to a query timestamp is still unfinished at
  that M1 open because the intraminute touch was not yet known;
- Parent end is exclusive; a target event stamped at the same Parent-end M1
  cannot rescue or extend the old Parent;
- target decision and target outcome ledgers remain physically separate.

The study derives exact level birth and consumption from the byte-frozen
Phase-1B causal pack. It does not load later price data or reconstruct a new
visual level topology.

## Required joins

The target state is attached without changing actions to:

1. all 1,649 selected V10 Children;
2. all 2,234 Phase-1B FAST flips and their linked k1 outcomes;
3. all Phase-1C bridge and repair observations;
4. the frozen Phase-1E session, weekday, event, and H20 interaction fields.

Every economic table must report stopped exposure and retained right-tail
capital together. The 35-Child H20 aligned pre-USD moderate/high 30-60 minute
cell is carried unchanged and decomposed by target state. No best consumed-data
cell may be promoted.

## Interpretation boundary

`TARGET_UNFINISHED` is a description, not permission to hold or add. Likewise,
`TARGET_COMPLETE_REFRAME_PENDING` is not an automatic exit, and
`PARENT_INVALIDATED` does not authorize the opposite direction. Phase 1F may
show that the states are useful or that this deterministic inventory is too
dense, too broad, or economically non-selective. All such outcomes are valid.

No target state, family, distance, session, weekday, event, HA transition, or
interaction receives veto, delay, exit, sizing, EA, or production authority.
All observations through `2026-09-18 23:57` remain consumed development
evidence, and `GOLD# 2021` remains sealed.
