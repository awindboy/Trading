# Trading Journal Launcher

`launchers/TradingJournalLauncher.cmd`를 더블클릭하면 아래 3개가 함께 실행됩니다.

- XM Global MT5
- MT5 bridge server: `http://127.0.0.1:8765/health`
- Web trading journal: `http://127.0.0.1:5173/`

## 종료

런처 창에서 `q` 입력 후 Enter를 누르거나 Ctrl+C를 누르면 런처가 직접 띄운 MT5와 서버가 함께 종료됩니다.

창을 강제로 닫아도 Windows Job Object의 kill-on-close 설정으로 자식 프로세스가 같이 정리되도록 만들었습니다.

## 로그

로그는 `logs/` 폴더에 저장됩니다.

- `logs/mt5.log`
- `logs/bridge.log`
- `logs/web.log`

## MT5 백그라운드 실행

MT5는 완전한 headless/background 앱이 아니라 GUI 터미널입니다. Python API, EA, 로그인 세션이 MT5 터미널 실행 상태에 의존하므로 PC에 로그인된 상태에서 MT5가 떠 있어야 합니다.

런처는 MT5를 최소화 상태로 시작합니다. 실제 운영은 “PC 켜짐 + Windows 로그인 + MT5 최소화 + 런처 실행” 방식이 가장 안정적입니다.

## 옵션

PowerShell이나 CMD에서 직접 옵션을 줄 수도 있습니다.

```bat
launchers\TradingJournalLauncher.cmd --dry-run
launchers\TradingJournalLauncher.cmd --no-mt5
launchers\TradingJournalLauncher.cmd --mt5-path "C:\Program Files\XM Global MT5\terminal64.exe"
```
