# V13 SA-1 MQL5 validation protocol

Date: `2026-09-28`
Status: `NEXT REQUIRED TESTER WORK`
Base GitHub `main`: `652dcd070206f04a51eb5a7451a253393b60ee03`
EA: `mt5/experts/V13SA1CleanContinuationEA.mq5`

## Tester setup

- Symbol: `GOLD#` on the same XMGlobal feed used by the current V13 actual-tick report.
- Model: `Every tick based on real ticks`.
- Research window: `2024-01-01` through canonical cutoff `2026-08-28 20:00` where the tester permits matching end-time semantics.
- Hedging account mode.
- Fixed `0.01` lot per Child first.
- `InpVerbose=true`.
- No risk sizing, optimization or parameter sweep.

## Compile gate

Before economics are accepted:

1. MetaEditor compile must complete without errors.
2. Tester initialization must print `V13SA1_READY`.
3. No `V13SA1_HALT` or unresolved state-reconciliation failure may occur in the canonical run.

## Admission parity checks

For sampled and then machine-parsed signals verify:

1. Child #1 always bypasses SA-1.
2. Same-color add-on opportunity emits `V13SA1_EVENT|ADMISSION`.
3. `raw_close_accept` uses the completed signal-H4 raw close versus the **same H4** HA close.
4. `no_opposite_wick` uses standard H4 HA geometry and the correct side mirror.
5. H1 HA is recursively warmed up and uses only completed H1 bars inside the signal H4.
6. `h1_no_opposition=1` only when every observed H1 color matches Journey direction.
7. A rejected signal does not increment `g_children`.
8. A later same-color H4 can still become the next successful Child until the cap of 10 successful entries.
9. No rejected historical signal is later inserted after future price is known.

## HA-9 management parity after admission

For every admitted add-on verify the existing HA-9 requirements:

1. proof target is the immediately preceding signal H4 raw favorable extreme;
2. proof window is exactly the following H4;
3. first tick of a new H4 cannot retroactively rescue an expired Child;
4. proof arms the lock, but lock cannot fire on that same proof observation;
5. LONG lock uses actual entry / signal high and Bid crossing; SHORT uses actual entry / signal low and Ask crossing;
6. unproven add-on closes on first executable print after the proof H4;
7. opposite H4 HA Journey reversal supersedes individual timeout/lock close;
8. no duplicate entry after retry ambiguity.

## Required Journal events

Archive the full Strategy Tester Journal containing at least:

```text
V13SA1_READY
V13SA1_EVENT|HA_CLOSE
V13SA1_EVENT|ADMISSION
V13SA1_EVENT|ENTRY
V13SA1_EVENT|PROOF
V13SA1_EVENT|LOCK_HIT
V13SA1_EVENT|PROOF_TIMEOUT_DUE
V13SA1_EVENT|CHILD_EXIT
V13SA1_EVENT|JOURNEY_CHILD_EXIT
V13SA1_EVENT|JOURNEY_START
V13SA1_EVENT|JOURNEY_END
V13SA1_RETRY
V13SA1_HALT
```

## Economic receipt

Report at minimum:

- total / Child1 / add-on counts;
- wins, losses, flats, non-flat WR;
- net, PF;
- realized chronological DD ordered by exit execution;
- maximum consecutive losses;
- exit reason counts;
- admission pass/reject counts and component counts;
- year and side slices;
- 10/25/50/100-trade block positive share and median P/L;
- top 1/3/5/10/20 profitable-Journey removal;
- actual SA-1 versus actual HA-9 comparator under the same tester economics.

## Stop-and-repair rule

If admission/event parity fails, repair semantics first. Do not change the three admission conditions, proof window, lock price, timeout, side-specific exceptions or sizing to compensate for a tester result.
