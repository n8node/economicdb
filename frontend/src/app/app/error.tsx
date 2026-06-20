"use client";

import { useEffect } from "react";

export default function AppError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[app] render error:", error);
  }, [error]);

  return (
    <div className="content">
      <div className="card card-pad">
        <h1 style={{ marginTop: 0 }}>Ошибка отображения страницы</h1>
        <p className="meta">
          Это не обязательно проблема backend — сбой мог произойти в интерфейсе. Нажмите «Повторить»
          или обновите страницу (Ctrl+Shift+R).
        </p>
        {process.env.NODE_ENV === "development" ? (
          <p className="meta" style={{ fontFamily: "var(--font-mono)", fontSize: 12 }}>
            {error.message}
          </p>
        ) : null}
        <button type="button" className="btn primary" onClick={() => reset()}>
          Повторить
        </button>
      </div>
    </div>
  );
}
