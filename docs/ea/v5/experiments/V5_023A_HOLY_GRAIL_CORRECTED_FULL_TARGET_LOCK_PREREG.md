# V5-023A — Source-Corrected Holy Grail Full Target-Locked Runner Pre-registration

Status: `PRE-REGISTERED BEFORE V5-023A OUTCOME ANALYSIS`
Date: `2026-08-27`
Parents: `V5-017A full target-lock runner`, `V5-020A previous-bar trigger correction`
Strategy authority: `NONE`

## Why

V5-017A was frozen before the source-trigger correction but was not used to authorize any candidate. V5-020A showed
that the literal previous-bar trigger raises the probability of reaching the published prior-swing objective while
reducing its R multiple. The already-frozen V5-017A lifecycle directly addresses that source-described branch:
once the prior swing is retested, either the move fails there or a new continuation leg begins.

This phase does not invent a new exit. It applies the previously frozen full target-lock lifecycle to the corrected
source entry.

## Population

Exactly V5-020A filled first attempts. No target_R, market, session, direction, timeframe, ADX, EMA, or stop-width filter.

## Management

Before target:
- original V5-020A structural stop;
- target = frozen prior-swing objective;
- stop-first = -1R.

If target is reached first:
- realize no partial at target;
- beginning with the NEXT M1 bar, move the full-position stop to the target price;
- thereafter ratchet the stop one-way with completed signal-timeframe EMA20 exactly as V5-017A;
- if an EMA update crosses through the market, exit at the completed signal-bar close;
- adverse gaps through active stop fill conservatively at M1 open;
- no fixed runner target;
- one recorded-spread Level-A cost once.

Thus a normal non-gap target-first trade cannot finish below the published target_R gross.

## Promotion gate

At one timeframe:
- net-positive WR >=50% pooled and in >=18/24 adequate groups;
- average gross winner >1R pooled and median group;
- pooled and median-group net EV >0;
- net EV >0 in >=18/24 adequate groups;
- no single market/year necessary;
- neighboring timeframe no material expectancy sign reversal.

Failure closes this lifecycle; no partial fraction, EMA length, target, or timeframe tuning.
