"use client";

import { useCallback, useEffect, useState } from "react";
import { ProductSidebar } from "./ProductSidebar";
import { ProductTopbar } from "./ProductTopbar";

export function ProductShell({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const closeSidebar = useCallback(() => setSidebarOpen(false), []);

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

  return (
    <div className={`app${sidebarOpen ? " sidebar-open" : ""}`}>
      {sidebarOpen && (
        <button
          type="button"
          className="sidebar-backdrop"
          onClick={closeSidebar}
          aria-label="Закрыть меню"
        />
      )}
      <ProductSidebar open={sidebarOpen} onNavigate={closeSidebar} onClose={closeSidebar} />
      <div className="main">
        <ProductTopbar onMenuToggle={() => setSidebarOpen((v) => !v)} />
        {children}
      </div>
    </div>
  );
}
