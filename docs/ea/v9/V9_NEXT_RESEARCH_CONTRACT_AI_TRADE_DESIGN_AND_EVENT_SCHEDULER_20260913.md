# V9 Next Research Contract — AI Trade Design + Deterministic Event Scheduler

Date: `2026-09-13`  
Status: `ACTIVE NEXT RESEARCH CONTRACT / ML TRACK RETIRED / FUTURE-HIDDEN LOCKED`  
Base GitHub HEAD: `ce9ab2651cf6112e36aebbf1fb549f7a5f3e7b8f`  
Market: `GOLD# ONLY`  
Production authority: `NONE`  
EA authority: `NONE`  
2024: `CONSUMED POSTMORTEM DATA`  
Future-hidden: `2025-07 LOCKED`  
Final reserve: `GOLD# 2021 UNTOUCHED`

## 1. Superseding research direction

This contract supersedes the active-next-work sequence in:

`V9_NEXT_RESEARCH_CONTRACT_GRAMMAR_LOSS_CONVERSION_20260913.md`

where they conflict.

The previous entry-acceptance / delivery / campaign-exhaustion questions remain useful semantic questions, but the architecture is now explicit:

```text
DETERMINISTIC GRAMMAR / OBJECT ENGINE
-> TRADE CANDIDATE
-> AI ENTRY TRADE-DESIGN CALL
-> runtime execution + independent Hard SL
-> deterministic review wake events
-> AI HOLD / EXIT / REMAP
```

The project will **not** continue the exploratory ML scheduler/direction work in the current phase.

## 2. Research thesis

The 2024 replay did not test a fully discretionary AI trader at entry.

It mostly tested:

```text
Grammar
-> mechanical branch authorization
-> mechanical execution geometry
-> precommitted structural origin
-> late AI review
```

The next question is:

> Can the same Grammar become materially more useful when AI is allowed to judge each candidate as a complete trade thesis before risk is paid, and then is called again at simple objective progression/structure events while the position is alive?

The scheduler should be simple, auditable, causal, and cheap enough that ML is unnecessary unless later evidence proves otherwise.

## 3. Workstream A — Entry AI on every candidate

### Candidate authority

Deterministic runtime remains authoritative for:

- causal market state;
- object existence / lifecycle;
- Parent/Child context;
- code-owned candidate coordinates;
- executable order reporting;
- Hard-SL enforcement.

But a strategy candidate is no longer assumed to equal an order decision in this research phase.

### AI entry questions

For each candidate, chart-native AI must decide:

```text
TRADE / ARM
WAIT
NO TRADE
```

and state a trade thesis covering:

1. Child direction and branch meaning;
2. whether arrival at the candidate location is actually accepted by the Child side;
3. whether the relevant repair/bridge is genuinely active;
4. selected code-owned entry geometry;
5. selected code-owned structural falsification / Hard SL;
6. route / first meaningful destination / larger continuation possibility;
7. why the structural risk is worth paying now;
8. what future market information would require review.

### Direction constraint

AI may reject a deterministic candidate.

AI does not get authority to invent the opposite trade from nothing. A different direction requires causally available code-owned candidate geometry and a valid Parent/Child story.

### Hard SL

Retain permanently:

```text
selected before entry
code-owned exact coordinate
never widened
stopped Child is dead
later price never rescues it
```

## 4. Workstream B — Research scheduler v2 candidate

While a Child is open, runtime continuously guards price and watches objective events.

### Candidate wake reasons

```text
R_MILESTONE
FIRST_FAVORABLE_DELIVERY
POST_DELIVERY_M15_NONSUPPORT
EXISTING_STRUCTURAL_REVIEW
REMAP_REQUIRED
```

Existing Parent/H1/launch-anchor semantics remain intact.

### R milestone semantics

Use first crossing of each **positive integer multiple of the Child's frozen initial risk** as a progression wake reason.

Example:

```text
+1R first cross
+2R first cross
+3R first cross
...
```

This is operational scheduling only.

It must never mean:

```text
minimum-R
fixed TP
BE movement
trailing stop
forced partial close
```

### First favorable delivery

Only the first causally known favorable liquidity delivery is a default delivery wake candidate in v2 research.

Do not call AI on every raid by default; 2024 produced `2,716` such events across 305 resolved trades.

### Post-delivery M15 non-support

After favorable delivery, the first completed M15 state that no longer supports the Child side is a progression-review candidate.

It asks whether:

```text
role complete / Parent-side reacceptance
vs
ordinary repair inside a continuing winner
```

It is never an automatic exit.

### Existing structural events

Retain current review/remap semantics for:

- launch-anchor damage;
- H1 branch terminal conditions already encoded;
- Parent authority loss / remap;
- other accepted structural damage reasons.

## 5. Event batching / concurrency contract to research

Multiple reasons can arrive together.

Required principle:

```text
one Child + one causal information batch
-> one AI request
-> reason_codes[] contains every event
```

Do not spawn one request per reason.

If a second review reason appears while a request for the same Child is still in flight, the current exact-staleness authority must be preserved.

Research the following fail-safe behavior:

```text
new material causal fact
-> old request becomes stale/superseded
-> no parallel conflicting actions
-> build one newest request
```

The exact cancel/supersede/rebuild state machine must be implemented and consumed-tested before it is frozen.

Hard SL remains independent during any AI latency or outage.

## 6. Workstream C — Paired causal AI study at event times

The next semantic study should no longer look only at entry or final outcome.

For every selected event, show AI only the chart/state known at that event.

Mandatory paired groups:

### Giveback losses

All `21` trades that reached `>= +1R` and later hit Hard SL.

### Large winners

At least the long-tail winners that create current expectancy, including examples such as:

- `2024OOS-COU0114`;
- `2024OOS-WIT0080`;
- `2024OOS-COU0330`;
- `2024OOS-COU0236`;
- other top realized-R trades needed for branch balance.

### Questions at each call

AI must answer from causal context:

```text
What is the current Child role?
Has the original thesis strengthened, weakened, or remained unresolved?
Is favorable delivery transit or role completion?
Is the Parent side re-accepting price?
Has a new destination opened?
HOLD / EXIT / REMAP?
```

No later outcome can appear in the packet.

## 7. Workstream D — Entry fast-loss study through actual AI calls

The 45 fast/no-progress Hard-SL trades are the primary entry-AI stress set.

Because the tested management scheduler generated `0 / 45` pre-stop management reviews, they must be studied at the entry decision itself.

Compare against robust winners with similar deterministic authorization context.

The study must not convert a descriptive feature into a mandatory filter such as:

```text
M5 against Child -> reject
H4 agreement < 3 -> reject
specific OB/FVG type -> reject
```

The AI should use the full causal chart and explain whether the pitch is worth taking.

## 8. Workstream E — Trade-specific SL / route / risk

The next entry packet must expose enough code-owned alternatives for AI to decide whether a meaningful trade can be constructed.

Research questions:

```text
Which structural boundary actually falsifies this Child thesis?
Is that boundary too close because the local auction is still noisy?
Is it so far away that the current Child role does not justify the risk?
Where is the first meaningful route/destination?
Should the answer therefore be WAIT / NO TRADE instead of changing the SL after entry?
```

Do not introduce a universal minimum-R threshold.

Do not widen a live Hard SL.

If no meaningful pre-entry falsification exists, `NO TRADE / WAIT` is allowed.

## 9. Workstream F — Position-management AI action study

At management wake events, current action vocabulary remains initially:

```text
HOLD
EXIT
REMAP
```

Do not add partial-close, automatic stop movement, or trailing authority until separate evidence justifies it.

Every decision must preserve:

- Parent/Child separation;
- no hindsight rescue;
- large-winner participation;
- explicit `UNRESOLVED` when context is unclear;
- code-owned coordinates;
- Hard-SL priority.

## 10. Price shock candidate

Do not add a generic price-shock trigger yet.

A future `PRICE_SHOCK_REVIEW` must show incremental value beyond:

- R progression;
- liquidity delivery;
- completed M15/H1/H4 structure;
- existing review/remap events.

Do not define it with an arbitrary dollar, ATR, percentile, or time threshold merely because it fits 2024.

## 11. What to measure

For every consumed replay, report at least:

### Entry layer

- deterministic candidates presented to AI;
- TRADE / WAIT / NO TRADE counts;
- filled trades;
- fast/no-progress Hard SL retained versus avoided;
- branch split;
- selected structural-risk distribution;
- rejected-candidate later outcome only as postmortem, never backfill authority.

### Management layer

- management calls per trade/day;
- reason-code counts;
- batched/coalesced calls;
- AI latency edge cases;
- +1R/+2R/+3R giveback outcomes;
- large-winner preservation;
- HOLD / EXIT / REMAP counts;
- Hard SL before AI response;
- stale/superseded response counts.

### Performance

- total R;
- PF;
- drawdown;
- branch results;
- monthly stress;
- top-winner dependence;
- commission/swap/latency caveats.

## 12. No automatic event actions

The following remain explicitly unauthorized:

- +1R/+2R/+3R automatic TP;
- automatic BE after any R milestone;
- automatic trailing;
- automatic exit on favorable delivery;
- automatic exit on post-delivery M15 non-support;
- all-liquidity-raid AI calls;
- fixed retry/cooldown;
- ML gate around AI calls;
- arbitrary large-movement threshold.

2024 counterfactual evidence shows why: automatic rules can improve the losing subset while destroying more value in large winners.

## 13. ML retirement

The exploratory ML feasibility results are not part of the active research chain.

Do not add them to Resume order as authority.
Do not tune or productionize them.
Do not use their outputs to authorize trade direction or AI calls.

Only reconsider ML after the deterministic event-driven architecture is fully measured and a concrete operational deficiency remains.

## 14. Implementation sequence

```text
1. freeze entry-candidate AI request semantics
2. freeze entry chart-native MAP/TRIGGER attachment
3. build consumed causal entry-AI replay harness
4. implement research-only scheduler-v2 wake reasons
5. implement same-batch event coalescing
6. implement pending-request stale/supersede/rebuild behavior
7. run paired event-time AI study on 21 givebacks + large winners
8. run 45 fast-loss entry study + comparable winners
9. replay full 2024 consumed period with real AI decisions
10. replay 2025H1 + 2026JF consumed periods for causal/semantic robustness
11. freeze packet/chart/prompt/model-role/runtime hashes only after counterexample review
12. explicitly reconsider the future-hidden gate
```

## 15. Future-hidden gate

No hidden-data status changes in this contract.

```text
2025-07 = LOCKED
2021    = UNTOUCHED
```

The gate remains `NOT SATISFIED` until the AI entry trade-design contract, event-driven position-management contract, chart attachment, action semantics, and consumed replay are frozen and validated.

## 2026-09-13 superseded active scope

<!-- V9_CONTINUOUS_STATE_ACTION_POLICY_PIVOT_20260913 -->

This contract is retained as historical/downstream research evidence. Its active-next-work sequence is superseded by:

`V9_NEXT_RESEARCH_CONTRACT_CONTINUOUS_STATE_ACTION_POLICY_20260913.md`

Entry/management blind studies, event coalescing, stale-request safety, and Hard-SL independence remain useful inputs to the newer policy work. Do not continue setup-centric optimization before the unified policy decision-sufficiency study.

