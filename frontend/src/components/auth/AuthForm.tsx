"use client";

import { FormEvent, useMemo, useState } from "react";
import { AppLink as Link } from "@/components/AppLink";
import { useRouter } from "next/navigation";
import { loginUser, registerUser } from "@/lib/auth";

type AuthMode = "login" | "register";

type PasswordRule = {
  label: string;
  passed: boolean;
};

function passwordRules(password: string): PasswordRule[] {
  return [
    { label: "Не менее 8 символов", passed: password.length >= 8 },
    { label: "Строчная буква (a-z)", passed: /[a-z]/.test(password) },
    { label: "Заглавная буква (A-Z)", passed: /[A-Z]/.test(password) },
    { label: "Цифра (0-9)", passed: /\d/.test(password) },
    { label: "Спецсимвол (!@#$...)", passed: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password) },
  ];
}

function strengthLabel(score: number): string {
  if (score <= 1) return "Слабый";
  if (score <= 3) return "Средний";
  if (score === 4) return "Хороший";
  return "Отличный";
}

export function AuthForm({ mode }: { mode: AuthMode }) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [consent, setConsent] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const rules = useMemo(() => passwordRules(password), [password]);
  const score = rules.filter((rule) => rule.passed).length;
  const requiredRulesPassed = rules.slice(0, 4).every((rule) => rule.passed);
  const passwordsMatch = password === confirmPassword;
  const isRegister = mode === "register";
  const canSubmit = isRegister
    ? Boolean(email && requiredRulesPassed && passwordsMatch && confirmPassword && consent && !loading)
    : Boolean(email && password && !loading);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!canSubmit) return;

    setError("");
    setLoading(true);
    try {
      if (isRegister) {
        await registerUser(email, password);
      } else {
        await loginUser(email, password);
      }
      const params = new URLSearchParams(window.location.search);
      const next = params.get("next") || "/app";
      router.replace(next.startsWith("/app") ? next : "/app");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось выполнить запрос");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={onSubmit}>
      {error ? <div className="auth-error">{error}</div> : null}

      <label htmlFor="email">Email</label>
      <input
        id="email"
        type="email"
        autoComplete="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        required
      />

      <label htmlFor="password">Пароль</label>
      <div className="auth-password-field">
        <input
          id="password"
          type={showPassword ? "text" : "password"}
          autoComplete={isRegister ? "new-password" : "current-password"}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />
        <button type="button" onClick={() => setShowPassword((value) => !value)} aria-label="Показать пароль">
          <i className={`ti ${showPassword ? "ti-eye-off" : "ti-eye"}`} />
        </button>
      </div>

      {isRegister ? (
        <>
          <div className="auth-strength" aria-label={`Надежность пароля: ${strengthLabel(score)}`}>
            {[0, 1, 2, 3].map((index) => (
              <span key={index} className={index < Math.min(score, 4) ? "active" : ""} />
            ))}
          </div>
          <p className="auth-strength-label">{strengthLabel(score)}</p>
          <ul className="auth-rules">
            {rules.map((rule) => (
              <li key={rule.label} className={rule.passed ? "passed" : ""}>
                <i className={`ti ${rule.passed ? "ti-circle-check" : "ti-circle"}`} />
                {rule.label}
              </li>
            ))}
          </ul>

          <label htmlFor="confirm-password">Подтвердите пароль</label>
          <div className="auth-password-field">
            <input
              id="confirm-password"
              type={showConfirmPassword ? "text" : "password"}
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              required
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword((value) => !value)}
              aria-label="Показать подтверждение пароля"
            >
              <i className={`ti ${showConfirmPassword ? "ti-eye-off" : "ti-eye"}`} />
            </button>
          </div>
          {confirmPassword && !passwordsMatch ? <p className="auth-hint error">Пароли не совпадают</p> : null}

          <label className="auth-checkbox">
            <input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} />
            <span>
              Согласие с{" "}
              <a href="/privacy" target="_blank" rel="noreferrer">
                политикой обработки персональных данных
              </a>
            </span>
          </label>
        </>
      ) : null}

      <button type="submit" className="auth-submit" disabled={!canSubmit}>
        {loading ? (isRegister ? "Регистрация…" : "Вход…") : isRegister ? "Зарегистрироваться" : "Войти"}
      </button>

      <p className="auth-switch">
        {isRegister ? "Уже есть аккаунт? " : "Нет аккаунта? "}
        <Link href={isRegister ? "/app/login" : "/app/register"}>{isRegister ? "Войти" : "Зарегистрироваться"}</Link>
      </p>
    </form>
  );
}
