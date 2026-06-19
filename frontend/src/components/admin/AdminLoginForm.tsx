"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { adminLogin } from "@/lib/auth";

export function AdminLoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("erman.ai@yandex.ru");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await adminLogin(email, password);
      router.push("/adminus/dashboard");
      router.refresh();
    } catch {
      setError("Неверный email или пароль");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="admin-form" onSubmit={onSubmit}>
      {error ? <div className="admin-error">{error}</div> : null}
      <label htmlFor="email">Email</label>
      <input
        id="email"
        type="email"
        autoComplete="username"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <label htmlFor="password">Пароль</label>
      <input
        id="password"
        type="password"
        autoComplete="current-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      <button type="submit" disabled={loading}>
        {loading ? "Вход…" : "Войти"}
      </button>
    </form>
  );
}
