# V13 HA-5 causal raw-swing observation contract

Date: `2026-09-27`
Status: `FROZEN BEFORE MEASUREMENT / OBSERVATION ONLY`

## Question

Can actual traded-price swing structure distinguish a real Standard-H4 HA
Journey transition from a temporary H1-opposition warning, beyond the H4 HA
body/Delta/wick and raw-close information already observed in HA-1..HA-4D?
This is *not* an attempt to predict a destination or build a fractal entry.

## Source, clock and population

- GOLD# raw M1 is streamed chronologically from the 2022 warm-up through the
  frozen `2026-08-28 20:00` H4 execution-open cutoff. Rebuild H4 OHLC from
  that M1 prefix; the exported H4 file is parity reference only.
- Evaluate the unchanged Standard-H4 Baseline-0 decision sequence from
  HA-4C/D, joined by H4 signal time, side and Journey. Its decision features
  and future labels remain physically separate.
- Primary population is every in-window Standard-H4 decision with a completed
  next-bar/three-bar outcome. Report no-level coverage, years, sides, Journey
  birth/continuation and >=10-bar Journey exposure.

## One fixed swing definition

Use a strict five-completed-H4-bar pivot: pivot high of bar `i-2` is greater
than the highs of `i-4`, `i-3`, `i-1`, `i`; pivot low is strictly less than
the corresponding four lows. Equal highs/lows do *not* confirm a pivot.
The pivot becomes known only after bar `i` completes at the next actual M1
print. This 2-left/2-right construction is a named measurement convention,
not an optimized lookback or an assertion of exact platform-indicator parity.

At the decision following bar `i`, classify bar `i` against the **latest pivot
high and low that were already confirmed before bar `i` began**. Only *after*
that classification may the newly confirmed pivot at `i-2` replace a level
for future H4 bars. This prevents a current bar from retrospectively testing
a level that was not known when that bar formed.

## Causal level interaction

For the current H4 Journey, the favorable/progress boundary is the last
confirmed raw high for LONG, raw low for SHORT. The adverse boundary is the
last confirmed raw low for LONG, raw high for SHORT. Mirror the definitions
exactly by side. For each boundary, describe the completed raw H4 bar as:

- `no_level`: no prior confirmed boundary;
- `no_break`: neither its directional extreme nor its close exceeded it;
- `probe_rejected`: directional high/low exceeded it but close did not;
- `fresh_close_beyond`: close exceeded it and the previous close did not
  exceed this *same* active boundary;
- `held_close_beyond`: current and previous closes exceeded the same active
  boundary;
- `return_inside`: previous close exceeded the same active boundary, but
  current close did not.

Strict price comparisons define exceedance; touching exactly is not a break.
When the active boundary changed since the previous decision, do not call a
current close `held` or `return_inside` based on the new level's history.
Record when both favorable and adverse boundaries are exceeded in the same
H4 bar; M1 OHLC does not establish their intrabar order.

Record level confirmation age and decision-time distance in units of the
median range of the last 20 completed H4 bars. This is a volatility-aware
coordinate, never a gate, stop or TP. The first 19 in-window decisions may
use preceding warm-up ranges; missing values remain missing.

## Predeclared comparison

1. Overall and continuation-only frequencies of each favorable/adverse
   interaction and the joint event when both boundaries are exceeded.
   For compact, predeclared descriptive contrasts, combine favorable
   `probe_rejected`/`return_inside` as `progress_rejection_or_return`, and
   adverse `fresh_close_beyond`/`held_close_beyond` as
   `adverse_close_beyond`. These are not trading labels or gates.
2. Within the H1 path states `no_opposition`, `repaired`, and the two forms
   of ending opposition, compare next-H4 flip, flip within three H4 bars,
   future-defined peak-already-past label, remaining favorable excursion and
   false warnings. An ending-H1-opposed state is not an exit by itself.
3. Compare raw-structure contrasts within comparable H4 body/range and
   raw-close display bins, and within H4 Delta contraction / wick state where
   support allows. Report overlap coverage and sensitivity to binning; do not
   infer a full-population independent effect from non-overlap.
4. At the Journey grain, show whether structure would mark the 88 long
   Journeys and how much favorable movement remains after such marks.
5. Show year/side diagnostics, not selected-period optimization.

Future-label data may describe outcomes only after decision features are
frozen. No threshold, score, veto, entry, exit, SL, sizing, EA or MT5 economic
claim is authorized by this stage. All 2024-2026 observations are already-
consumed development evidence.
