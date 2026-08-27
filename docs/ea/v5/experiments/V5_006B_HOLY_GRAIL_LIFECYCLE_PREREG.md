# V5-006B — Holy Grail Independent-Opportunity Lifecycle Amendment

Status: PRE-REGISTERED AFTER V5-006A SAMPLING FAILURE / BEFORE V5-006B OUTCOME USE
Date: 2026-08-27

V5-006A is classified CONFOUNDED / DESIGN INSUFFICIENT because an unfilled fixed stop order could remain pending for
years and suppress all later setups. Its outcome table is consumed diagnostic and has no authority.

V5-006B preserves every published setup parameter and the V5-006A trend/pullback operationalization, but replaces the
pending-order lifecycle with an outcome-blind cycle reset.

## Setup cycle

1. Arm on ADX(14)>30 and rising with the frozen direction operationalization.
2. Wait for the first EMA20 touch.
3. Freeze one Holy Grail setup at that touch.
4. Do not create another setup until a NEW completed bar again satisfies an ADX arm condition.
5. That new arm bar closes the old pending-order cycle and simultaneously starts a new trend cycle.

## Pending entry order

The touch-bar trigger remains active from the touch-bar close until the close of the next fresh ADX arm bar.

If the trigger trades before that arm bar closes, the fill is valid.
If it has not filled by that arm-bar close, cancel it.

This removes outcome-dependent/years-long suppression without introducing a tuned bar-count expiry.

## Trade outcome

Once filled, the trade's frozen structural target/stop resolve independently even if a later setup forms.
This stage measures setup mechanics, not portfolio overlap.

All other V5-006A rules remain unchanged:
- 15/30/60/120m all reported;
- ADX30 / EMA20 fixed;
- no R:R filter;
- target recent pre-pullback extreme;
- stop pullback swing;
- M1 execution ordering pessimistic;
- one-spread Level-A cost;
- no re-entry extension.

Promotion requires robust >=50% realized WR, median target >1R, and positive cost-adjusted expectancy across
market/year/direction groups. No threshold rescue.
