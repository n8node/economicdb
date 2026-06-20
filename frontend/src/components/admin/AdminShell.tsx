"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AdminUser, clearAdminToken, fetchAdminMe } from "@/lib/auth";

export function AdminShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [admin, setAdmin] = useState<AdminUser | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    fetchAdminMe()
      .then((user) => {
        if (!user) {
          router.replace("/adminus");
          return;
        }
        setAdmin(user);
      })
      .finally(() => setChecking(false));
  }, [router]);

  function logout() {
    clearAdminToken();
    router.push("/adminus");
  }

  if (checking) {
    return (
      <div className="admin-page">
        <p>Проверка доступа…</p>
      </div>
    );
  }

  if (!admin) return null;

  const nav = [
    { href: "/adminus/dashboard", label: "Обзор" },
    { href: "/adminus/data", label: "Данные и ETL" },
    { href: "/adminus/providers", label: "Провайдеры данных" },
    { href: "/adminus/settings", label: "Настройки" },
  ];

  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <h2 style={{ fontSize: 16, margin: "0 0 16px" }}>Adminus</h2>
        <nav>
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              target="_top"
              className={pathname === item.href || pathname.startsWith(`${item.href}/`) ? "active" : ""}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="admin-main">
        <div className="admin-top">
          <span className="muted">{admin.email}</span>
          <button type="button" className="admin-btn" onClick={logout}>
            Выйти
          </button>
        </div>
        {children}
      </main>
    </div>
  );
}
