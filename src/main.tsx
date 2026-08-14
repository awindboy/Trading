import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import ReplayApp from "./replay/ReplayApp";
import "./styles.css";

function bridgeErrorUrl() {
  const host = window.location.hostname && window.location.hostname !== "localhost" ? window.location.hostname : "127.0.0.1";
  return `http://${host}:8765/client-error`;
}

function reportClientError(error: Error, info?: React.ErrorInfo) {
  const payload = {
    message: error.message,
    stack: error.stack,
    componentStack: info?.componentStack,
    href: window.location.href,
    userAgent: navigator.userAgent,
    at: new Date().toISOString(),
  };
  fetch(bridgeErrorUrl(), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).catch(() => undefined);
}

function clearLocalJournalCache() {
  Object.keys(localStorage)
    .filter((key) => key.startsWith("trading-journal"))
    .forEach((key) => localStorage.removeItem(key));
  window.location.href = `${window.location.pathname}?v=${Date.now()}`;
}

type ErrorBoundaryState = {
  error: Error | null;
};

class ErrorBoundary extends React.Component<React.PropsWithChildren, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("Trade Ledger render failed", error, info);
    reportClientError(error, info);
  }

  render() {
    if (!this.state.error) return this.props.children;

    return (
      <main className="app-error-screen">
        <section>
          <strong>화면을 불러오지 못했습니다.</strong>
          <p>{this.state.error.message || "브라우저 렌더링 중 오류가 발생했습니다."}</p>
          <div>
            <button type="button" onClick={() => window.location.reload()}>
              새로고침
            </button>
            <button type="button" className="secondary" onClick={clearLocalJournalCache}>
              로컬 캐시 초기화
            </button>
          </div>
        </section>
      </main>
    );
  }
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      {window.location.pathname.startsWith("/replay") ? <ReplayApp /> : <App />}
    </ErrorBoundary>
  </React.StrictMode>,
);
