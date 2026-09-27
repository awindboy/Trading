# V13 HA-9 — add-on one-H4 proof + breakout-lock action contract

Date: `2026-09-28`
Status: `FROZEN ACTION CANDIDATE / CONSUMED DEVELOPMENT / MT5 ACTUAL-TICK VALIDATION PENDING`
Base GitHub `main`: `29e0073e57553d8fe1fd14b843daf09164a7a248`
Comparator: frozen V13 Baseline 0

## 1. Mechanism

Baseline 0 enters one Child after every completed same-color H4 HA bar, up to 10.
Its weak point is that many add-on Children are allowed to remain open even when
the immediately following raw-price H4 fails to prove directional continuation;
and after a favorable breakout has occurred, the Child can still round-trip back
into a loss before the eventual HA reversal.

HA-9 changes **only management of Child #2..#10**.

Child #1, Journey definition, standard H4 HA construction, opposite-HA Journey
close/reverse, fixed unit size and maximum of 10 successful Child entries remain
unchanged.

## 2. Add-on proof target

For an add-on caused by a completed same-color signal H4:

- LONG proof target = that signal H4's raw `HIGH`;
- SHORT proof target = that signal H4's raw `LOW`.

The add-on still enters at the first executable price of the following H4, as in
Baseline 0.

The **proof window is exactly that following H4**.

Proof requires a strict raw-price breakout:

```text
LONG:  raw price > signal-H4 HIGH
SHORT: raw price < signal-H4 LOW
```

No ATR multiple, tick count, percentile, optimized distance or ML score is used.

## 3. If proof occurs — breakout lock

When proof occurs, define:

```text
LONG lock  = max(actual Child entry, signal-H4 HIGH)
SHORT lock = min(actual Child entry, signal-H4 LOW)
```

The lock is not allowed to trigger inside the same observation that first proves
the breakout.

- Research M1 reconstruction: lock becomes active from the next M1 bar.
- Real-tick EA: lock becomes active from the next `OnTick` after proof.

Once active, a retrace through the lock closes **only that Child**.

There is no initial Hard SL before proof.

## 4. If proof does not occur — one-H4 timeout

At the first executable print after the proof H4 completes, an add-on that never
strictly crossed its proof target closes at market.

If the same boundary is also the ordinary opposite-HA Journey exit, the Journey
close has priority and there is no duplicate close.

## 5. Child counting and Journey behavior

- `MAX_CHILDREN = 10` still means maximum 10 **successful Child entries**.
- An add-on closed early is not backfilled.
- A later same-color H4 may still create the next numbered Child while the
  Journey remains alive.
- Existing open Children are unaffected by a later Child's timeout/lock event.
- Opposite completed H4 HA closes all remaining Journey positions and starts the
  opposite Journey after close-all, as before.

## 6. Causal / execution requirements

- Only completed H4 signal high/low can define the proof target.
- The first tick of a new H4 cannot retroactively prove the previous Child's
  expired one-H4 proof window.
- Research stop fills are gap-aware: if an M1 opens beyond the virtual lock, use
  that M1 open rather than the more favorable lock price.
- The EA uses live Bid to observe raw breakout; after proof it uses Bid for LONG
  lock crossing and Ask for SHORT lock crossing, then closes at market.
- No closed Child may be resurrected after later price action.

## 7. Evaluation doctrine

Use `V13_OBJECTIVE_AND_EVALUATION_UPDATE_20260928.md`.

Primary diagnostics are loss-count reduction, win rate, consecutive losses,
chronological trade-stream DD, rolling/block positivity, year stability and
Top-N profitable-Journey-trimmed P/L. Right-tail loss is reported as a trade-off,
not an automatic veto.

## 8. Authority boundary

HA-9 is the first V13 action candidate with a large change in ordinary trade
quality on consumed history, but it is **not production authority**.

Required next evidence:

1. MetaEditor compile of `mt5/experts/V13HAProofLockMax10EA.mq5`;
2. Strategy Tester `Every tick based on real ticks` on the canonical window;
3. event-ledger parity against the causal research audit;
4. spread/slippage and virtual-lock execution review;
5. only then consider sizing/capital work.

Do not optimize the one-H4 window or proof price on the same consumed history to
rescue a failed tester result.
