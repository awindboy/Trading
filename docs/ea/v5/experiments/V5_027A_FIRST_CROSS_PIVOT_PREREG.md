# V5-027A First Cross Price-Structure Confirmation
Status: FROZEN BEFORE OUTCOME ANALYSIS
Date: 2026-08-27
Parent: V5-026A source reproduction.

Reason: V5-026A used the oscillator pullback bar itself as the price trigger. Raschke's source explicitly says First Cross is analogous to a first higher low/lower high and that the oscillator is only an initial condition; price must trigger entry. V5-027A adds the minimum causal swing confirmation rather than an outcome-tuned filter.

Oscillator/regime population unchanged from V5-026A.
After the first fast-line zero pullback while slow remains on trend side:
- Long: identify the first 3-bar pivot low (low[k] < low[k-1] and low[k] < low[k+1]), available only at completion of k+1; require pivot low > reversal-regime low.
- Short: first 3-bar pivot high analog, require pivot high < reversal-regime high.
- Place entry stop one point beyond the completed confirmation bar k+1 high/low.
- Stop one point beyond the pivot extreme.
- Cancel if slow crosses zero against regime or reversal-regime extreme invalidates before fill.
- Only first qualifying pivot per oscillator First Cross.

Management families remain frozen:
A structural retest of the impulse extreme before pullback.
B EMA20 trend lifecycle with +1R breakeven activation.
All 15/30/60/120m/1D and four markets reported. No threshold tuning.
