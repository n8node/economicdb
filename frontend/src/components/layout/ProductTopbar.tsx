"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ThemeToggle } from "./ThemeToggle";
import { apiFetch } from "@/lib/api";

type SearchHit = { id: string; name_ru: string; country: string; source: string };

export function ProductTopbar() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<SearchHit[]>([]);

  const onSearch = async (value: string) => {
    setQuery(value);
    if (value.trim().length < 2) {
      setHits([]);
      return;
    }
    try {
      const res = await apiFetch<SearchHit[]>(`/indicators/search?q=${encodeURIComponent(value)}`);
      setHits(res);
    } catch {
      setHits([]);
    }
  };

  return (
    <div className="topbar">
      <div className="search-box" style={{ position: "relative" }}>
        <i className="ti ti-search" />
        <input
          type="text"
          placeholder="Найти показатель: инфляция, ставка, ВВП…"
          value={query}
          onChange={(e) => void onSearch(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && hits[0]) router.push("/app/indicators");
          }}
        />
        {hits.length > 0 && (
          <div className="search-dropdown card">
            {hits.map((hit) => (
              <button
                key={hit.id}
                type="button"
                className="search-hit"
                onClick={() => {
                  setHits([]);
                  setQuery(hit.name_ru);
                  router.push("/app/indicators");
                }}
              >
                {hit.name_ru} <span className="meta">{hit.country.toUpperCase()}</span>
              </button>
            ))}
          </div>
        )}
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
