import { ThemeToggle } from "./ThemeToggle";

export function ProductTopbar() {
  return (
    <div className="topbar">
      <div className="search-box">
        <i className="ti ti-search" />
        <input type="text" placeholder="Найти показатель: инфляция, ставка, ВВП…" />
      </div>
      <div className="topbar-actions">
        <ThemeToggle />
        <button type="button" className="icon-btn" aria-label="Уведомления">
          <i className="ti ti-bell" />
          <span className="dot" />
        </button>
        <div className="avatar" style={{ cursor: "pointer" }}>
          АС
        </div>
      </div>
    </div>
  );
}
