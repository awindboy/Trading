from __future__ import annotations

import shutil
from pathlib import Path

try:
    import MetaTrader5 as mt5
except Exception as exc:
    raise SystemExit(f"MetaTrader5 package is not available: {exc}") from exc


ROOT = Path(__file__).resolve().parents[1]
EA_SOURCE = ROOT / "mt5" / "experts" / "TradeJournalExporterEA.mq5"


def main() -> None:
    if not EA_SOURCE.exists():
        raise SystemExit(f"EA source not found: {EA_SOURCE}")

    if not mt5.initialize():
        raise SystemExit(f"MT5 initialize failed: {mt5.last_error()}")

    terminal = mt5.terminal_info()
    if terminal is None:
        raise SystemExit(f"terminal_info failed: {mt5.last_error()}")

    data_path = Path(terminal._asdict()["data_path"])
    experts_dir = data_path / "MQL5" / "Experts"
    target = experts_dir / EA_SOURCE.name
    experts_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(EA_SOURCE, target)

    print(f"Installed EA: {target}")
    print("Open MetaEditor, compile TradeJournalExporterEA.mq5, then attach it to any MT5 chart.")
    print(f"EA events will be written under: {data_path / 'MQL5' / 'Files' / 'trading_journal'}")


if __name__ == "__main__":
    main()
