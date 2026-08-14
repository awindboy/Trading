from __future__ import annotations

import shutil
from pathlib import Path

try:
    import MetaTrader5 as mt5
except Exception as exc:
    raise SystemExit(f"MetaTrader5 package is not available: {exc}") from exc


ROOT = Path(__file__).resolve().parents[1]
INDICATOR_SOURCE = ROOT / "mt5" / "indicators" / "ICTCockpitIndicator.mq5"


def main() -> None:
    if not INDICATOR_SOURCE.exists():
        raise SystemExit(f"Indicator source not found: {INDICATOR_SOURCE}")

    if not mt5.initialize():
        raise SystemExit(f"MT5 initialize failed: {mt5.last_error()}")

    terminal = mt5.terminal_info()
    if terminal is None:
        raise SystemExit(f"terminal_info failed: {mt5.last_error()}")

    data_path = Path(terminal._asdict()["data_path"])
    indicators_dir = data_path / "MQL5" / "Indicators"
    target = indicators_dir / INDICATOR_SOURCE.name
    indicators_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(INDICATOR_SOURCE, target)

    compiled_source = INDICATOR_SOURCE.with_suffix(".ex5")
    if compiled_source.exists():
        shutil.copy2(compiled_source, indicators_dir / compiled_source.name)

    print(f"Installed indicator source: {target}")
    if compiled_source.exists():
        print(f"Installed compiled indicator: {indicators_dir / compiled_source.name}")
    else:
        print("Compiled .ex5 was not found. Open MetaEditor and compile ICTCockpitIndicator.mq5.")
    print("In MT5, refresh Navigator > Indicators, then attach ICTCockpitIndicator to a chart.")


if __name__ == "__main__":
    main()
