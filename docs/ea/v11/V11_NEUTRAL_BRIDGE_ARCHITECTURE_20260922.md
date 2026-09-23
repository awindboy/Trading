# V11 neutral-bridge architecture

Last synchronized: `2026-09-22`

## Status

`RESEARCH ARCHITECTURE / OBSERVATION ONLY / NO TRADE OR SIZING AUTHORITY`

V11 is not a Wave-based filter placed on top of V10. Its intended structural change is to separate termination of the old Child from authorization of an opposite Child.

```text
ACTIVE JOURNEY
-> completed NHA interrupts the active Child
-> NEUTRAL BRIDGE
   -> old direction resumes
   -> opposite direction establishes an independent journey
   -> neither side earns authorization
```

An NHA is therefore evidence that the old participation attempt has been interrupted. It is not, by itself, proof that the opposite PHA should receive risk.

## Why Wave Candle belongs here

The Wave Candle is useful only if the M5 process inside the bridge distinguishes efficient directional settlement from rotation that merely changes the H4 HA color. The candidate information is:

- price progress in the prospective direction;
- path efficiency of that progress after causal volatility normalization;
- settlement relative to the completed NHA and the prior journey;
- the liquidity event, if any, that explains why the prior journey stopped.

Static contour shape, generic H4-route existence, and elapsed time alone are not sufficient authorization semantics.

## Research contract

- Start with the first valid FAST k1 after a completed opposite HA.
- Freeze the prospective Hard SL before the bridge begins.
- If that Hard SL is touched before a review checkpoint, the prospective opposite Child is dead; later recovery cannot rescue it.
- Rebuild completed M5 and H4 directly from one chronological raw-M1 stream.
- Freeze bridge observations only at their causal checkpoint.
- Treat fixed 60/120/180-minute reviews as mechanism probes, not cooldown rules.
- Do not convert consumed-data thresholds, quantiles, or risk simulations into authority.
- Audit LONG/SHORT and liquidity-era stability separately.

## Rejected candidate semantic

The initial diagnostic proposed:

> The prospective direction must show positive raw progress, and that progress must be achieved with enough path efficiency to look like an independent journey rather than another rotation inside the old journey.

The post-stop sequence audit rejected this as a selective gate. It prevented many baseline stops only by skipping hundreds of baseline non-stops and large positive R. Completed-NHA departure preserved expectancy better but did not materially control repeat-stop chains. The neutral bridge remains an open research question; it has no retained authorization semantic and is not ready for future validation.
