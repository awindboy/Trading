# V9 Event-Driven AI Entry + Position Review Checkpoint

Date: `2026-09-13`  
Status: `CONSUMED-DATA SCHEDULER FEASIBILITY ACCEPTED / ACTION SEMANTICS NOT YET FROZEN`  
Base GitHub HEAD: `ce9ab2651cf6112e36aebbf1fb549f7a5f3e7b8f`  
Production authority: `NONE`  
EA authority: `NONE`  
Market: `GOLD# ONLY`  
2024: `CONSUMED POSTMORTEM DATA`  
Future-hidden: `2025-07 LOCKED`  
Final reserve: `GOLD# 2021 UNTOUCHED`

## 1. Decision reached by this study

The exploratory ML direction is **retired from the active V9 research path**.

No ML model from the exploratory feasibility work receives strategy, scheduler, production, or validation authority. Do not spend the next research cycle improving an ML direction classifier or ML AI-call sentinel.

The active architecture to research is now:

```text
V9 Grammar / deterministic structure
-> deterministic Child candidate
-> AI called at every entry candidate
-> AI decides TRADE / WAIT / NO TRADE and trade-specific plan
-> if position opens, runtime guards Hard SL continuously
-> simple deterministic management events wake AI
-> AI decides HOLD / EXIT / REMAP from full causal context
```

This checkpoint accepts **the research direction and scheduler feasibility**, not final entry/exit strategy quality.

## 2. Why the architecture changed

The 2024 postmortem showed two different problems.

### Fast failures

```text
45 Hard-SL trades
<= 60 minutes from fill
MFE < 0.25R
```

Under the event family tested here, **0 / 45** received a management wake event before death.

Therefore these trades cannot primarily be solved by better post-entry scheduling. The main opportunity is before risk is paid:

> deterministic authorization should generate a trade candidate, while AI should decide whether the candidate is actually worth taking at that location and with that structural falsification.

### Trades that first worked and later died

```text
21 Hard-SL trades reached >= +1R first
```

The old structural REVIEW/REMAP scheduler reached only `1 / 21` of them before death.

These are precisely the cases where simple progression events can give AI another causal look without turning the event into an automatic trade rule.

## 3. Permanent distinction: event != action

The most important finding is:

```text
EVENT
= reason to wake AI
!= EXIT
!= TP
!= BE
!= trailing-stop movement
!= direction reversal
```

The event scheduler allocates **attention** only.

Hard SL remains a separate deterministic runtime guard and keeps priority over discretionary AI review.

## 4. Candidate management wake events tested

The 2024 consumed replay was re-indexed with the following research event families.

### A. Existing structural review/remap

Existing v1 runtime gates such as structural damage / Parent loss / remap.

### B. Positive integer-R first crossing

Examples:

```text
+1R first reached
+2R first reached
+3R first reached
...
```

This is **not a minimum-R rule and not TP authority**.

`R` is already defined by the Child's frozen pre-entry structural Hard-SL risk. A new positive integer crossing is used only as an operational progression checkpoint.

### C. First favorable liquidity delivery

First causally known favorable M5 swing/liquidity landmark delivered while the Child is alive.

This is a stage-transition review candidate, not an exit condition.

Calling on every favorable liquidity raid is rejected as too chatty: the 305 closed 2024 trades contained `2,716` favorable liquidity deliveries.

### D. First post-delivery completed-M15 non-support

After a favorable delivery has occurred, the first completed M15 state that no longer supports the Child direction.

This is a stronger progression-question event:

> has the Child role completed, or is this merely a repair inside a still-valid larger continuation?

It is still review-only.

## 5. 2024 scheduler feasibility result

Closed 2024 trade universe:

```text
305 resolved trades
103 winners
202 losses
153 Hard SL
21 MFE>=1R then Hard SL
```

### Event-family coverage

| Event family | Batched management calls | Trades called | 1R+ giveback losses reached | Winner trades reached |
|---|---:|---:|---:|---:|
| Existing structural review only | 154 | 153 | 1 / 21 | 103 |
| Positive integer-R milestones | 305 | 109 | 21 / 21 | 79 |
| First favorable delivery | 195 | 195 | 14 / 21 | 101 |
| Post-delivery M15 non-support | 166 | 166 | 10 / 21 | 80 |

The event-reason count for R milestones is `314`; minute-level batching reduces that to `305` calls because multiple R levels can be crossed in the same minute.

### Proposed research scheduler union

Candidate union:

```text
existing structural review/remap
+ positive integer-R first crossings
+ first favorable liquidity delivery
+ first post-delivery M15 non-support
```

Result under same-Child / same-minute batching:

```text
raw event reasons                     829
batched management calls              798
trades with >=1 management call       215 / 305
1R+ giveback Hard-SL coverage          21 / 21
Hard-SL trades with management call    63 / 153
winner trades with management call    103 / 103
```

If the 305 actually filled entries are used as a **lower bound** for one entry-AI call per trade, the observed 2024 workload becomes:

```text
305 entry calls (filled-entry lower bound)
+ 798 management calls
= 1,103 calls/year
≈ 4.38 calls per 252-day proxy
```

Actual candidate-level entry calls may be higher because rejected/waited/unfilled candidates are not represented by the completed-trade ledger.

This call volume does not justify an ML scheduler at this stage.

## 6. Giveback timing

For the 21 trades that reached >= +1R and later hit Hard SL, the first proposed review event occurred before the final stop in every case.

First-review-to-stop lead time using causal event timestamps / M1 timing proxy:

```text
median   ~37.86 minutes
mean    ~127.70 minutes
> 5 min       18 / 21
> 15 min      13 / 21
<= 5 min       3 / 21
```

Two cases had +1R and Hard SL inside the same M1 minute. Exact supplied 2024 tick order was inspected:

```text
2024OOS-COU0063
+1R ASK crossing  15:30:03.611
Hard SL           15:30:51.013
separation        47.402 sec

2024OOS-WIT0065
+1R ASK crossing  15:30:01.648
Hard SL           15:30:12.603
separation        10.955 sec
```

Therefore a wake event creates a causal review opportunity but does not guarantee that a remote AI service can respond before Hard SL.

Do not create a fixed service-latency market threshold from these two examples. Hard SL remains independent.

## 7. Why automatic actions are rejected

### Fixed R TP counterfactual

2024 actual:

```text
+20.51R
```

If every trade that ever reached the level had been automatically closed there:

```text
+1R fixed TP -> -31.88R
+2R fixed TP ->  -8.47R
+3R fixed TP ->  -4.98R
```

This destroys the large-winner mechanism.

### Automatic exit at post-delivery M15 non-support

There were `165` resolved trades with a usable counterfactual price at the first such event.

```text
actual result on those trades       +88.47R
auto-exit counterfactual             +44.36R
delta                                -44.11R
```

For winner trades carrying this event:

```text
actual                              +150.98R
counterfactual auto-exit             +42.39R
```

For loss trades carrying this event:

```text
actual                               -62.51R
counterfactual auto-exit              +1.97R
```

The event strongly helps identify trades worth reviewing, but **the same event occurs inside large winners**. This is exactly why the AI layer exists.

## 8. Paired causal evidence

Two representative COUNTER shorts demonstrate the distinction.

### `2024OOS-COU0307` — giveback loss

```text
entry: 2704.56
MFE: +3.60R
final: -1.02R Hard SL
```

Wake sequence:

```text
15:06  +1R
15:24  first favorable delivery
15:27  +2R
16:27  +3R
17:00  post-delivery M15 non-support
```

At the 17:00 causal snapshot the trade was still around `+1.74R` by the stored counterfactual executable reference, after meaningful counter delivery and subsequent local re-acceptance pressure.

### `2024OOS-COU0330` — large winner

```text
entry: 2716.51
MFE: +10.72R
realized: +7.80R
```

Wake sequence began:

```text
12:00  first favorable delivery
12:08  +1R
12:45  post-delivery M15 non-support
13:07  +2R
...
17:42  +10R
20:00  existing structural review
```

At the same nominal `post-delivery M15 non-support` event, the stored executable counterfactual was only about `+0.30R`, yet the Child later expanded above +10R MFE.

Therefore the scheduler event is useful, but the event name itself cannot determine the action.

## 9. Large-winner call burden

Under the proposed union, the top 20 realized winners would receive approximately `6` to `22` management calls each, with median about `10`.

This is acceptable as a first research design because the total annual call count remains modest, but bursts can occur during very fast movement.

For example, a +20R-MFE winner crossed many R milestones within minutes.

Therefore the next runtime design must not spawn parallel AI requests for the same Child.

Research requirement:

```text
same causal batch -> one request with multiple reason codes
AI request already pending -> later non-Hard-SL reasons must be coalesced/supersede the stale request, not create parallel calls
Hard SL -> remains independent and immediate
```

The exact pending-request supersession protocol is **not frozen by this checkpoint** because it must remain consistent with existing exact structural-staleness rules.

## 10. Entry-side architecture decision for next research

The previous deterministic strategy authorization should now be treated as a **candidate generator** in the next research phase, not proof that the order should be placed automatically.

Research target:

```text
Grammar / Parent / Child candidate
-> AI entry review every candidate
-> AI may:
   TRADE / ARM
   WAIT
   NO TRADE
```

The AI must evaluate at least:

- current Parent/H4/H1/M15/M5 context;
- whether the Child-side auction is actually accepted at the execution location;
- whether repair is actually complete for WITH_PARENT;
- whether a COUNTER Local-Bridge is actually opening rather than being absorbed by Parent acceleration;
- meaningful code-owned entry geometry;
- meaningful code-owned structural falsification / Hard SL;
- route / destination expectation;
- whether paying the proposed structural risk is reasonable in the current context.

AI cannot invent freehand coordinates. Code owns exact geometry.

Hard SL is fixed before entry and never widened.

An opposite direction is not invented merely because AI dislikes the supplied candidate. It requires causally available structure/geometry for that side.

## 11. ML direction retired

The exploratory ML feasibility track is not incorporated into authority.

Current decision:

```text
ML direction oracle            RETIRED
ML AI-call sentinel            RETIRED FOR CURRENT PHASE
ML trade action authority      NONE
```

Reason:

- entry candidate call volume is already small enough to call AI directly;
- position management can be covered by explicit causal events at modest call volume;
- deterministic wake reasons are easier to audit, replay, and debug;
- an ML scheduler adds training/drift/label complexity before there is evidence it is needed.

ML may only be reconsidered later if the accepted deterministic scheduler proves operationally insufficient. Do not continue it by default.

## 12. What is accepted vs not accepted

Accepted as research direction:

- AI review at every deterministic entry candidate;
- deterministic event-driven position review;
- positive integer-R crossings as review-only progression events;
- first favorable delivery as review-only event;
- post-delivery M15 non-support as review-only event;
- existing structural review/remap retained;
- event batching/coalescing is required;
- Hard SL remains independent;
- ML track retired.

Not yet accepted:

- exact entry AI action schema / prompt;
- AI-selected Entry/SL/route/risk contract;
- exact event packet and rendering contract;
- whether every candidate event family survives paired chart study;
- pending-request supersession mechanics;
- price-shock event definition;
- production/live authority;
- future-hidden performance.

## 13. Price-shock idea

A generic `large movement` wake event is intentionally **not frozen yet**.

Do not invent:

```text
X dollars in N minutes
ATR multiple threshold
fixed candle-size percentile
```

without consumed evidence.

Positive R milestones already provide a simple risk-normalized wakeup for large favorable movement. A separate `PRICE_SHOCK_REVIEW` should be added only if it can be defined causally and structurally and adds information beyond the current scheduler.

## 14. Data status

No future-hidden data was opened for this study.

```text
2024       CONSUMED POSTMORTEM DATA
2025H1     CONSUMED ANSWER-SHEET DATA
2026JF     CONSUMED ANSWER-SHEET DATA
2025-07    LOCKED
2021       UNTOUCHED FINAL RESERVE
```

The future-hidden gate remains `NOT SATISFIED`.
