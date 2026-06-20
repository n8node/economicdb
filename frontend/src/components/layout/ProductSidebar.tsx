"use client";

import { usePathname } from "next/navigation";

const NAV = [
  { href: "/app", label: "Обзор", icon: "ti-layout-dashboard", exact: true },
  { href: "/app/indicators", label: "Показатели", icon: "ti-list-search" },
  { href: "/app/compare", label: "Сравнение", icon: "ti-chart-line" },
  { href: "/app/calendar", label: "Календарь", icon: "ti-calendar-event" },
  { href: "/app/summaries", label: "AI-сводки", icon: "ti-sparkles" },
  { href: "/app/favorites", label: "Избранное", icon: "ti-star" },
  { href: "/app/alerts", label: "Алерты", icon: "ti-bell" },
  { href: "/app/settings", label: "Настройки", icon: "ti-settings" },
];

export function ProductSidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">М</div>
        <span className="brand-name">Макроаналитика</span>
      </div>

      <nav className="nav-group">
        {NAV.map((item) => {
          const active = item.exact ? pathname === item.href : pathname.startsWith(item.href);
          return (
            <a key={item.href} href={item.href} className={`nav-item${active ? " active" : ""}`}>
              <i className={`ti ${item.icon}`} />
              <span>{item.label}</span>
            </a>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="user-row">
          <div className="avatar">АС</div>
          <div className="user-meta">
            <p className="user-name">Анна Соколова</p>
            <p className="user-plan">Тариф Pro</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
