import { AuthForm } from "@/components/auth/AuthForm";

export default function LoginPage() {
  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="auth-brand">
          <div className="brand-mark">М</div>
          <span>Макроаналитика</span>
        </div>
        <h1>Вход</h1>
        <p className="auth-muted">Войдите, чтобы продолжить работу с макроэкономической аналитикой.</p>
        <AuthForm mode="login" />
      </section>
    </main>
  );
}
