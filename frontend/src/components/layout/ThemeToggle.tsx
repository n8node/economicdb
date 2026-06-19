"use client";

import { useEffect, useState } from "react";

export function ThemeToggle() {
  const [mode, setMode] = useState<"light" | "dark">("light");

  useEffect(() => {
    const saved = localStorage.getItem("macro_theme");
    if (saved === "dark") {
      setMode("dark");
      document.documentElement.setAttribute("data-theme", "dark");
    }
  }, []);

  function apply(next: "light" | "dark") {
    setMode(next);
    localStorage.setItem("macro_theme", next);
    if (next === "dark") {
      document.documentElement.setAttribute("data-theme", "dark");
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
  }

  return (
    <div className="theme-toggle">
      <button
        type="button"
        className={mode === "light" ? "active" : ""}
        aria-label="Светлая тема"
        onClick={() => apply("light")}
      >
        <i className="ti ti-sun" />
      </button>
      <button
        type="button"
        className={mode === "dark" ? "active" : ""}
        aria-label="Тёмная тема"
        onClick={() => apply("dark")}
      >
        <i className="ti ti-moon" />
      </button>
    </div>
  );
}
