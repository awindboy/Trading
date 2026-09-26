# V13 Baseline 0 execution revision 13.002

User-authorized repair, 2026-09-26. Research/tester only, no production authority.
This supersedes 13.001's halt-on-any-failure policy. HA, H4, fixed lot, max ten,
no SL/TP, and opposite-color exit semantics are unchanged. Execution timing on
failed requests necessarily changes; compare all variants using this revision.

## Defects repaired

- Same-color entry and close-all failures permanently halted the EA.
- First-entry failure logged PENDING but no tick-driven retry existed.
- A failed close after some successes left fewer positions than the cumulative
  Child count; the old equality check made resuming impossible.
- CopyRates failure could mark an H4 boundary consumed without updating HA.

## Explicit recovery contract

- Synchronous CTrade responses MARKET_CLOSED, REQUOTE, PRICE_CHANGED, PRICE_OFF,
  TOO_MANY_REQUESTS can retry only when position state confirms no change.
- Retry on ticks after 1, 2, 4, 8, 16, then at most every 30 broker seconds.
  No Sleep loop, new strategy input, or fitted trading cooldown.
- One pending entry per latest completed H4 signal. Count a Child only after
  DONE, one additional own hedging position, and the full requested volume.
- On the next completed H4, expire an unfilled old entry. Do not batch missed
  bars or backfill orders at old prices. Use the latest signal at current Bid/Ask.
- Exit has priority. Once an opposite-color exit is required, keep closing the
  remaining tickets; already closed tickets are not closed again. DONE_PARTIAL
  on an exit can retry the smaller confirmed remaining volume.
- Never reverse while an old own position remains. If HA changes during a
  delayed close, finish the latched close, then begin in the latest HA direction.
- History read failure leaves the boundary unconsumed. Reconstruct newly
  available completed bars in order, but execute only the latest pending intent.
- TIMEOUT, PLACED, CONNECTION ambiguity after sending, partial ENTRY, invalid
  volume, no money, disabled trading and unknown/permanent errors remain HALT.
  Do not blindly resend when a request may already have filled. This repair is
  not a complete asynchronous order-reconciliation or restart-recovery system.
- Log retries, expired entries, fills, remaining exits and final pending state.
  An unresolved pending action at test end must be disclosed in the receipt.

Successful transient recovery is not automatically an invalid run. Any HALT,
unreconciled position state or incomplete history still invalidates execution.
Retain the Journal to distinguish execution delay from strategy performance.

## Validation

MetaEditor compilation: production and fault-injection harness have zero errors
and zero warnings. A separate portable MT5 tester (build 5836) executed the real
EA functions against fake trade/position APIs: 17 assertions passed, zero failed,
zero broker orders. Covers transient first/additional entries, retry throttling,
duplicate prevention, partial/remaining close, close-before-reverse, stale-signal
expiry, color changes during close, max ten, permanent/ambiguous errors and
history catch-up intent handling. It does not simulate CopyRates failure itself.

Harness: `mt5/tests/V13ExecutionRecoveryTest.mq5`. It runs on EURUSD only as a
test clock, not a strategy comparison. The dedicated audit terminal does not
have GOLD#, so no GOLD# full-window actual-tick economics were run here.
Official Baseline-0 economic report is still pending on the user's GOLD# setup.

## Official platform references

- [Trade-server result codes](https://www.mql5.com/en/docs/constants/errorswarnings/enum_trade_return_codes)
- [CTrade PositionClose and server-result verification](https://www.mql5.com/en/docs/standardlibrary/tradeclasses/ctrade/ctradepositionclose)
