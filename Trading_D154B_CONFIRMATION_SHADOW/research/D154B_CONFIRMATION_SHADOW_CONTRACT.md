# D-154B Post-Fill Confirmation Shadow Contract

Date: 2026-08-22  
Status: **LOCAL SHADOW RESEARCH / NOT STRATEGY AUTHORITY**  
Base Git HEAD remains `3bf78e1d34a6721b9fe32115f8f6af050babbda6`.

## Question

For baseline trades that actually Fill while M1 is `TRANSITION`, does waiting for the **first same-direction M1 INITIAL_BOS** and entering at the first executable tick after that causal bar close produce a materially better Fill -> +1R survival profile when the original normalized SL is retained?

## Population

Only actual V2 EXTERNAL_CONTINUATION fills where M1 is `TRANSITION` at actual Fill.

No other Fill-time state is changed or filtered.

## Causal trigger

After actual Fill and before the original trade reaches either +1R or original SL:

- first M1 INITIAL_BOS same direction -> arm one shadow confirmation candidate;
- first M1 INITIAL_BOS opposite direction -> record rejection class only;
- original +1R/SL first -> no confirmation candidate.

Only the first INITIAL_BOS is used. No second chance / retry within this phase.

## Shadow candidate geometry

- Entry: first executable market-side tick after the same-direction INITIAL_BOS becomes causally known.
- SL: original normalized SL frozen at baseline Fill.
- Risk: distance from new executable entry to original normalized SL.
- +1R: recomputed from the new entry and this risk.
- Structural objective: original frozen structural TP.
- If original structural TP provides <1R from the later entry, record `CANDIDATE_INFEASIBLE`; do not invent a closer TP or tighter SL.

## Observation after candidate arm

The candidate remains shadow-active until:

- new +1R,
- original normalized SL,
- or tester end.

HTF map support loss is logged as context, not used as an exit rule.

## Forbidden

- no real Entry delay
- no real order
- no SL/TP change
- no position sizing change
- no EM combination
- no R threshold search
- no second FVG/re-entry rule yet
- no same-sample promotion to baseline

## Promotion logic

D-154B can only justify further research if:

1. shadow +1R survival is materially improved;
2. relation direction does not collapse across GOLD/BTC and LONG/SHORT;
3. adequate structural objective room remains;
4. audit OFF/ON parity passes;
5. the result is later validated outside GOLD25/BTC25 before any real strategy variant.

Even a strong result remains a shadow mechanism hypothesis until cost-adjusted real execution is tested.
