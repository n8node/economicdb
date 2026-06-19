import Link from "next/link";

export default function HomePage() {
  return (
    <main style={{ padding: 48 }}>
      <div className="card">
        <h1>Макроаналитика</h1>
        <p className="muted">Frontend scaffold. Лендинг — WordPress на /</p>
        <p>
          <Link href="/app">Перейти в приложение →</Link>
        </p>
        <p>
          <Link href="/adminus">Админка →</Link>
        </p>
      </div>
    </main>
  );
}
