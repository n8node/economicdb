"use client";

export function NetworkStaleBanner() {
  return (
    <div className="session-stale-banner session-stale-banner--inline" role="alert">
      <div className="session-stale-banner__card">
        <p className="session-stale-banner__title">Соединение прервано</p>
        <p className="session-stale-banner__hint">
          Сеть Windows могла «зависнуть после простоя». Нажмите кнопку или обновите страницу (Ctrl+Shift+R).
        </p>
        <button
          type="button"
          className="btn primary session-stale-banner__action"
          onClick={() => {
            window.location.href = `/app?_fresh=${Date.now()}`;
          }}
        >
          Перезагрузить
        </button>
      </div>
    </div>
  );
}
