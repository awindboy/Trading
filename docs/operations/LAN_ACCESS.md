# Trading Journal LAN Access

PC, 패드, 폰에서 같은 매매일지를 쓰려면 PC에서 아래 두 서버를 켭니다.

```bash
npm run dev
npm run mt5
```

같은 Wi-Fi의 다른 기기에서는 PC의 IPv4 주소로 접속합니다.

```powershell
ipconfig
```

예를 들어 PC IPv4가 `192.168.0.25`라면 폰/패드에서 아래 주소를 엽니다.

```text
http://192.168.0.25:5173/
```

웹앱은 접속한 호스트를 기준으로 `http://<PC-IP>:8765` 브리지에 자동 연결합니다.

매매일지는 브리지 서버의 아래 파일에 공용 저장됩니다.

```text
data/journal.json
```

브리지가 꺼져 있으면 해당 브라우저의 `localStorage`에 임시 저장됩니다. 여러 기기에서 같은 기록을 공유하려면 `npm run mt5` 브리지를 켜둔 상태로 사용하세요.

Windows 방화벽에서 Node.js 또는 Python 네트워크 접근 허용을 묻는 창이 뜨면 같은 개인 네트워크에서 허용해야 폰과 패드가 접속할 수 있습니다.
