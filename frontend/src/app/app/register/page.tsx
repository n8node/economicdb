import { AuthForm } from "@/components/auth/AuthForm";

export default function RegisterPage() {
  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="auth-brand">
          <div className="brand-mark">М</div>
          <span>Макроаналитика</span>
        </div>
        <h1>Регистрация</h1>
        <p className="auth-muted">Создайте аккаунт для доступа к аналитике и сохранения настроек.</p>
        <AuthForm mode="register" />
      </section>
    </main>
  );
}
