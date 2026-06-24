"use client";

import { usePathname } from "next/navigation";

const NAV = [
  { href: "/app", label: "Обзор", icon: "ti-layout-dashboard", exact: true },
  { href: "/app/indicators", label: "Показатели", icon: "ti-list-search" },
  { href: "/app/compare", label: "Сравнение", icon: "ti-chart-line" },
  { href: "/app/calendar", label: "Календарь", icon: "ti-calendar-event" },
  { href: "/app/summaries", label: "AI-сводки", icon: "ti-sparkles" },
  { href: "/app/favorites", label: "Избранное", icon: "ti-star" },
];

type ProductSidebarProps = {
  open?: boolean;
  onNavigate?: () => void;
  onClose?: () => void;
};

export function ProductSidebar({ open = false, onNavigate, onClose }: ProductSidebarProps) {
  const pathname = usePathname();

  return (
    <aside className={`sidebar${open ? " is-open" : ""}`}>
      <div className="sidebar-header">
        <div className="brand">
          <div className="brand-mark">М</div>
          <span className="brand-name">Макроаналитика</span>
        </div>
        <button type="button" className="icon-btn sidebar-close" onClick={onClose} aria-label="Закрыть меню">
          <i className="ti ti-x" />
        </button>
      </div>

      <nav className="nav-group">
        {NAV.map((item) => {
          const active = item.exact ? pathname === item.href : pathname.startsWith(item.href);
          return (
            <a
              key={item.href}
              href={item.href}
              target="_top"
              className={`nav-item${active ? " active" : ""}`}
              onClick={onNavigate}
            >
              <i className={`ti ${item.icon}`} />
              <span>{item.label}</span>
            </a>
          );
        })}
      </nav>
    </aside>
  );
}
