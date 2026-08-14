# Trading Journal External Access

외부에서도 접속하려면 가장 안전한 방식은 Tailscale 사설망 접속입니다.

이 PC의 현재 Tailscale IP:

```text
100.73.110.68
```

PC에서 서버를 켭니다.

```bash
npm run dev
npm run mt5
```

외부 기기에서 할 일:

1. 폰, 패드, 노트북에 Tailscale을 설치합니다.
2. 이 PC와 같은 Tailscale 계정으로 로그인합니다.
3. 아래 주소로 접속합니다.

```text
http://100.73.110.68:5173/
```

웹앱은 같은 Tailscale IP 기준으로 브리지에도 자동 연결합니다.

```text
http://100.73.110.68:8765/
```

## Why Tailscale

- 공유기 포트포워딩이 필요 없습니다.
- 공용 인터넷에 MT5 주문 API를 직접 노출하지 않습니다.
- 집 밖, 카페, 모바일 데이터에서도 같은 사설망처럼 접속할 수 있습니다.

## Avoid Plain Public Port Forwarding

이 앱에는 MT5 주문 미리보기와 실주문 전송 API가 포함되어 있습니다. 공유기에서 `5173`, `8765`를 그대로 포트포워딩해 공개 인터넷에 노출하는 방식은 권장하지 않습니다.

정말 공개 URL이 필요하면 Cloudflare Tunnel, Tailscale Funnel, ngrok 같은 터널을 쓰되 반드시 접근 인증을 붙여야 합니다.
