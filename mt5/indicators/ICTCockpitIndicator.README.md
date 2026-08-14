# MT5 ICT Cockpit Indicator

`ICTCockpitIndicator.mq5` is the MT5 port of the TradingView ICT cockpit indicator.

It draws:

- `BSL` / `SSL` liquidity lines
- `BSL Sweep` / `SSL Sweep`
- dotted `BOS` / `CHoCH` structure lines at the broken swing level
- bullish / bearish `FVG` zones
- bullish / bearish `OB` zones
- `EQ` premium / discount reference lines
- strict `ICT Long` / `ICT Short` setup labels
- latest setup entry-zone, SL, and TP guide lines

Compile check:

```powershell
& "C:\Program Files\XM Global MT5\MetaEditor64.exe" /compile:"C:\Users\awind\OneDrive\문서\Trading\mt5\indicators\ICTCockpitIndicator.mq5" /log:"C:\Users\awind\OneDrive\문서\Trading\mt5\indicators\ICTCockpitIndicator.compile.log"
```

Install into the active MT5 terminal:

```powershell
npm run install-mt5-indicator
```

Then in MT5, refresh `Navigator > Indicators` and attach `ICTCockpitIndicator` to the chart.
