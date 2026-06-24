"use client";

import { AppLink as Link } from "@/components/AppLink";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { AdminUser, clearAdminToken, fetchAdminMe } from "@/lib/auth";

export function AdminShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [admin, setAdmin] = useState<AdminUser | null>(null);
  const [checking, setChecking] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const closeSidebar = useCallback(() => setSidebarOpen(false), []);

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

  useEffect(() => {
    document.body.style.overflow = sidebarOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [sidebarOpen]);

  useEffect(() => {
    const onResize = () => {
      if (window.innerWidth > 768) setSidebarOpen(false);
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

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
    { href: "/adminus/calendar", label: "Календарь" },
    { href: "/adminus/providers", label: "Провайдеры данных" },
    { href: "/adminus/users", label: "Пользователи" },
    { href: "/adminus/settings", label: "Настройки" },
  ];

  return (
    <div className={`admin-shell${sidebarOpen ? " sidebar-open" : ""}`}>
      {sidebarOpen && (
        <button
          type="button"
          className="admin-sidebar-backdrop"
          onClick={closeSidebar}
          aria-label="Закрыть меню"
        />
      )}
      <aside className={`admin-sidebar${sidebarOpen ? " is-open" : ""}`}>
        <div className="admin-sidebar-head">
          <h2>Adminus</h2>
          <button type="button" className="admin-btn admin-sidebar-close" onClick={closeSidebar} aria-label="Закрыть меню">
            <i className="ti ti-x" />
          </button>
        </div>
        <nav>
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              target="_top"
              className={pathname === item.href || pathname.startsWith(`${item.href}/`) ? "active" : ""}
              onClick={closeSidebar}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="admin-main">
        <div className="admin-top">
          <div className="admin-top-start">
            <button
              type="button"
              className="admin-btn admin-menu-toggle"
              onClick={() => setSidebarOpen((v) => !v)}
              aria-label="Меню"
            >
              <i className="ti ti-menu-2" />
            </button>
            <span className="muted admin-email">{admin.email}</span>
          </div>
          <button type="button" className="admin-btn" onClick={logout}>
            Выйти
          </button>
        </div>
        {children}
      </main>
    </div>
  );
}
