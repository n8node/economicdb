"use client";

import { usePathname, useRouter } from "next/navigation";
import { logoutUser, type AppUser } from "@/lib/auth";

const NAV = [
  { href: "/app", label: "Обзор", icon: "ti-layout-dashboard", exact: true },
  { href: "/app/indicators", label: "Показатели", icon: "ti-list-search" },
  { href: "/app/compare", label: "Сравнение", icon: "ti-chart-line" },
  { href: "/app/calendar", label: "Календарь", icon: "ti-calendar-event" },
  { href: "/app/summaries", label: "AI-сводки", icon: "ti-sparkles" },
  { href: "/app/favorites", label: "Избранное", icon: "ti-star" },
];

type ProductSidebarProps = {
  user: AppUser;
  open?: boolean;
  onNavigate?: () => void;
  onClose?: () => void;
};

function userInitials(email: string): string {
  const name = email.split("@")[0]?.trim();
  if (!name) return "П";
  return name
    .split(/[._-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

export function ProductSidebar({ user, open = false, onNavigate, onClose }: ProductSidebarProps) {
  const pathname = usePathname();
  const router = useRouter();

  function handleLogout() {
    logoutUser();
    onClose?.();
    router.replace("/app/login");
  }

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

      <div className="sidebar-footer">
        <button type="button" className="user-row" onClick={handleLogout} title="Выйти из аккаунта">
          <div className="avatar" aria-hidden="true">
            {userInitials(user.email)}
          </div>
          <div className="user-meta">
            <div className="user-name">{user.email}</div>
            <div className="user-plan">{user.email_verified ? "Email подтверждён" : "Email не подтверждён"}</div>
          </div>
        </button>
      </div>
    </aside>
  );
}
