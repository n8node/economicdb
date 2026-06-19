"use client";

export default function AppError({ reset }: { error: Error; reset: () => void }) {
  return (
    <div className="content">
      <div className="card card-pad">
        <h1 style={{ marginTop: 0 }}>Не удалось загрузить данные</h1>
        <p className="meta">Проверьте, что backend запущен, или попробуйте обновить страницу.</p>
        <button type="button" className="btn primary" onClick={() => reset()}>
          Повторить
        </button>
      </div>
    </div>
  );
}
