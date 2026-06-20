import Link from "next/link";

export default function HomePage() {
  return (
    <main style={{ padding: 48 }}>
      <div className="card">
        <h1>Макроаналитика</h1>
        <p className="muted">Frontend scaffold. Лендинг — WordPress на /</p>
        <p>
          <Link href="/app" target="_top">Перейти в приложение →</Link>
        </p>
        <p>
          <Link href="/adminus" target="_top">Админка →</Link>
        </p>
      </div>
    </main>
  );
}
