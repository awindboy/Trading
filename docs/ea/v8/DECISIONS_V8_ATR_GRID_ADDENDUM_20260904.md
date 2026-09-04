# V8 Decisions Addendum — ATR Grid Direction-Error Absorber

Date: `2026-09-04`
Status: `ACTIVE RESEARCH DECISIONS`
Production authority: `NONE`
Market: `GOLD# ONLY`
Source Git HEAD: `bbe30f7d23d13def712ad53117df9e8bc42a5e2e`

## Decision 1 — Initial direction remains the bottleneck

Repeated direct direction research did not produce a broad, robust initial-direction edge.

Therefore do not keep adding confirmation gates merely to obtain a smaller profitable subset.

The active research branch instead asks whether staged ATR exposure can absorb normal initial-direction error and concentrate the difficult problem into the smaller opposite one-way tail.

## Decision 2 — EV is an action framework, not a direction generator

Every-M1 EV, rolling EV, direct P(win) x payoff and continuous sizing did not manufacture missing direction information.

Use EV to compare concrete actions once a meaningful state exists.

Do not claim that an EV formulation solves direction merely because it is more mathematically general.

## Decision 3 — Sparse delayed states remain components only

The positive t10 unresolved/favorable state is preserved.

It is not the final solution because its coverage is too small relative to fresh75.

All future reports must keep the original campaign denominator visible.

## Decision 4 — Micro first-touch direction is invalidated

The apparent M1 micro first-touch edge did not survive exact tick.

A symmetric directional reference must be separated from actual Bid/Ask execution.

Do not promote the old micro-first-touch result.

## Decision 5 — Direction-free bilateral structures are downgraded

Simultaneous hedge/straddle, simple stop-and-reverse and continuous trend-follow variants did not provide robust economics.

Do not reopen them without a new mechanism.

## Decision 6 — ATR grid is a direction-error absorber, not an independent generic grid system

The intended use is:

- P15 authorizes a near-term movement campaign;
- initial direction may be weak;
- staged ATR entries absorb normal adverse rotation;
- weighted BE is the rescue objective;
- genuine opposite continuation is the dangerous tail;
- validated continuation may create a separate winner/add opportunity.

Do not reinterpret the branch as a generic always-on mean-reversion grid.

## Decision 7 — Micro-grid candle slicing is rejected

The early `0.08S` / tiny BE-profit grid was conceptually too small.

It created high apparent WR but weak payoff and execution sensitivity.

Do not return to micro spacing unless explicitly studying execution mechanics.

## Decision 8 — Multi-hour overexpansion is rejected as the default V8 grid

The branch temporarily expanded to 3-24h holdings.

This drifted away from P15's supported near-term semantics.

Longer holding can increase BE recovery mechanically while mixing new trend regimes.

Do not use long holding merely to improve the rescue rate.

## Decision 9 — M1 is screening, tick is execution authority

For staged entries:

- M1 cannot determine intrabar add/BE ordering;
- exact tick is mandatory for candidate P/L.

Tick gaps remain right-censored.

## Decision 10 — Causal timestamp must be explicit

For every feature/action:

- declare the exact last legal feature timestamp;
- declare the first possible execution timestamp.

The discovered 1-minute look-ahead invalidated affected results and is now a permanent guardrail.

## Decision 11 — Report actual dollars

R alone is insufficient for the current grid research.

Every report must decompose actual dollar P/L by outcome.

Required categories include:

- direct/protected TP;
- BE rescue;
- grid-before-winner;
- early cut;
- flip;
- hard loss.

## Decision 12 — Spread claims require zero-spread same-path control

Do not attribute failure to spread without proving:

- actual-spread result;
- zero-spread same-tick-path result;
- direct cost difference;
- outcome-classification difference.

## Decision 13 — `+1S` is a progress milestone, not automatic final TP

The current protected-winner architecture moves the final objective to around `+1.5S`.

This improved winner economics in 2024 P0 tick but remains unproven as final production payoff.

## Decision 14 — BE means rescue, not continuation

A weighted-BE touch does not automatically justify keeping the entire basket open.

Default interpretation:

> the rescue objective has been achieved.

Any continued exposure requires independent continuation evidence.

## Decision 15 — High-Q is better suited to a separate continuation action

Same-direction High-Q inside a campaign showed encouraging sparse development evidence.

However moving the existing base target farther to +3S worsened results.

Therefore, if reused, High-Q should be tested as a separate additional continuation tranche after base/rescue economics are secured.

## Decision 16 — No fixed timeout is required

Forced 45/60m exits created many artificial timeouts.

Removing the clock entirely also exposed large one-way tails.

The strategy should not be controlled by an arbitrary clock.

Elapsed time may be a hazard feature.

Exit should be price/state driven.

## Decision 17 — TP / BE / SL are different economic populations

Current conceptual decomposition:

- TP = direction correct and sustained;
- BE = direction initially wrong/noisy but rotation rescues;
- SL = direction wrong and price evolves into genuine opposite continuation.

The highest-value research target is the SL population.

## Decision 18 — Deep adverse state is the key branchpoint

The third tranche / about `-0.8S` is the current focused branchpoint.

Before that point, hard-loss behavior is much less concentrated.

After that point, the population splits roughly between BE recovery and hard loss.

The next model/action research starts here, not at arbitrary global checkpoints.

## Decision 19 — Future opposite move is diagnostic only

About 78-80% of current hard-loss events later exhibit an opposite-direction +1.5S diagnostic move.

This supports the interpretation that many SLs are genuine wrong-direction events.

It is never legal as a causal feature.

## Decision 20 — Campaign RR includes all tranche exposure

Equal `1:1:1` staged exposure in the current scaffold creates 2.4S basket loss at the -1.2S boundary.

A +1.5S first-unit winner therefore has only 0.625 gross reward/risk.

Do not judge RR from first-entry price distance.

## Decision 21 — Preserve price room; test exposure reshaping

A tighter price stop damaged normal BE recovery.

Therefore the next branch is not simply "move the stop closer".

Test:

- fixed size;
- decreasing size;
- martingale;
- state-based reduction/exit/flip.

## Decision 22 — Mandatory sizing controls

Fixed:

    1 : 1 : 1

Decreasing:

    1 : 0.5 : 0.25
    1 : 0.5 : 0.5
    1 : 0.25 : 0.25

Martingale:

    1 : 2 : 4

The `1 : 0.25 : 0.25` branch is an important 1:1 gross campaign-risk reference under the current -1.2S boundary.

The martingale branch must be judged by tail loss and exposure, not BE rate.

## Decision 23 — Sequential learning must advance with time

2025 validation:

- train on data through 2024 only.

2026 validation:

- retrain using 2024+2025.

Do not keep 2024-only training through 2026 when 2025 is available.

## Decision 24 — 2025 exact tick becomes mandatory next evidence

The user has supplied 2025 GOLD tick data in project sources.

Before using it:

- verify file identity;
- verify period/timezone;
- verify Bid/Ask;
- verify gaps;
- fail closed on incomplete coverage.

2025 is the key exact-tick validation for the current branch.

## Decision 25 — Next action is action EV, not another standalone classifier

At deep adverse state compare:

    HOLD
    REDUCE
    EXIT
    FLIP

The target is actual future dollar P/L under each action.

AUC may be reported only as secondary evidence.

The strategy objective is to preserve normal BE rescues while converting some hard losses into smaller losses or opposite winners.
