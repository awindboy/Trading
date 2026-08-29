# V6-003E — MT5 Role-Core Research EA Reproduction Contract

Status: `IMPLEMENTATION HANDOFF / PARITY-FIRST / NO PRODUCTION AUTHORITY`  
Date: `2026-08-29`  
Expected GitHub base HEAD: `545f7756e357c03b06561d2090b7055815fd56b0`  
EA: `mt5/experts/MentorDeterministicV6EA.mq5`  
Build identity: `V6_003E_ROLE_CORE_R0`

## Purpose

Implement the frozen V6-003D research control in a new, isolated Strategy-Tester-only EA while preserving V1/V2 history.

The EA is **not** a promoted production strategy. Its first job is to make MT5 emit a causal event ledger that can be compared against the offline V3/V6 research pipeline before any profitability claim is accepted.

Frozen module semantics:

```text
H:
DIRECT + D24 aligned + MENV HIGH_HIGH
-> 50% pullback
-> sweep-extreme SL
-> +3R realize 25%
-> residual BE
-> +5R final

L1:
DIRECT + D14=D24=local
-> H-authorized parent excluded
-> market Entry
-> sweep-extreme SL
-> +1R or 240 active M1 bars

L2:
ONE_RENEG (event -> opposite -> event)
+ D24 aligned
-> market Entry
-> sweep-extreme SL
-> +1R or 240 active M1 bars
```

## R0 reconstruction choices

The final V6-003D scratch script was not committed to GitHub. Therefore R0 reconstructs the final definitions from the committed V3 substrate, V6 pre-outcome freezes, result ledgers, and V6-003D authority.

The following are explicit and must be parity-tested rather than silently treated as proven identical:

1. `D14` and `D24` are signed displacement of the latest completed H1 close versus 14 and 24 completed H1 bars earlier.
2. `D24 age` counts consecutive completed H1 bars with the current D24 sign; it is logged only and has **no gate authority**.
3. `DIRECT` requires pre-sweep M1 BOS owner opposite the event and exactly one owner transition, into the event direction, by M5 trigger.
4. `ONE_RENEG` requires the exact three-transition path `event -> opposite -> event` from the same pre-sweep opposite owner.
5. MENV uses every prior same-symbol DIRECT opportunity with valid H geometry and completed D1 ATR; current state is classified before current scale/acceptance are appended.
6. H R0 uses a **virtual pending touch** and sends a market order at the first later tick touching the planned limit, after checking parent terminal and fill-time opposite exposure. This preserves causal routing and exposure checks but is not the final broker-pending execution implementation.

Any mismatch against the offline event ledger is an implementation problem to diagnose, not evidence about strategy profitability.

## Exact inherited substrate

The EA ports the committed V3 causal substrate:

```text
M15 adaptive directional change, k=2
ATR = simple rolling ATR14 of PRIOR completed M15 bars
-> persistent liquidity until first M1 penetration
-> same-M1 close recovery
-> pre-sweep completed M5 owner opposite reaction
-> sweep extreme remains intact
-> first completed M5 BOS-owner transition toward reaction
```

M1/M5 BOS owner uses k=2 confirmed pivots and completed-bar closes.

## MENV

At trigger, for DIRECT valid H geometry:

```text
chart_limit = trigger_close - dir * 0.5 * abs(trigger_close - broken_M5_level)

LONG  executable planned limit = chart_limit + trigger spread
SHORT executable planned limit = chart_limit

LONG  planned SL = sweep extreme
SHORT planned SL = sweep extreme + trigger spread

scale      = planned risk / completed D1 SMA ATR14
acceptance = ((trigger_close - broken_M5_level) * dir) / completed D1 SMA ATR14
```

Reference history is all prior eligible DIRECT opportunities, not prior fills.

After 20 prior observations:

```text
HIGH_SCALE  = scale > expanding prior median(scale)
HIGH_ACCEPT = acceptance > expanding prior median(acceptance)
HIGH_HIGH   = both true
```

## Execution boundary

- Hard-blocked outside MT5 Strategy Tester.
- Executing R0 requires a hedging account because same-direction overlap is allowed and independent tickets must remain distinguishable.
- Opposite-direction live exposure is blocked.
- H authorization is frozen at trigger. If H is authorized and later does not fill, L1 is **not** resurrected.
- L holding cap counts generated M1 bars, so weekend/session closure does not consume the 4 active hours.
- Spread/commission/slippage/swap remain real tester economics; the event CSV also logs planned price-R geometry.

## Required first test

Do **not** start with a new validation market.

First compile and run a consumed control where offline counts are already known. Recommended first parity sequence:

1. GOLD 2023-2025, full continuous run with enough earlier tester history to initialize bars.
2. Compare `RECOVERY`, `M5_TRIGGER`, `ROUTE_STATE`, H/L route counts and fills against the offline ledger.
3. Only after causal parity is understood, run external markets.

Use `Every tick based on real ticks` where available.

The R0 EA deliberately does not reconstruct pre-test-start DC/opportunity history. Therefore tester `From` must start early enough to provide warmup; for a claim-grade year comparison, include the required earlier history rather than starting exactly at the first target trade.

## Required acceptance gates

Before using MT5 P/L as strategy evidence:

```text
compile errors = 0
unexpected live-trading capability = 0
source/event timing audited
DIRECT / ONE_RENEG parity audited
D14/D24 parity audited
MENV expanding-history parity audited
H/L routing parity audited
Entry / SL / lifecycle parity audited
right-censored cases not force-labeled
```

R0 is a reproduction instrument first and a backtest engine second.
