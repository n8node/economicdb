"use client";

import { useState } from "react";
import { ThemeToggle } from "./ThemeToggle";
import { apiFetch } from "@/lib/api";

type SearchHit = { id: string; name_ru: string; country: string; source: string };

type SearchBoxProps = {
  query: string;
  hits: SearchHit[];
  onSearch: (value: string) => void;
  onSelect: (hit: SearchHit) => void;
  onEnter: () => void;
  className?: string;
};

function SearchBox({ query, hits, onSearch, onSelect, onEnter, className = "" }: SearchBoxProps) {
  return (
    <div className={`search-box ${className}`.trim()} style={{ position: "relative" }}>
      <i className="ti ti-search" />
      <input
        type="text"
        placeholder="Найти показатель: инфляция, ставка, ВВП…"
        value={query}
        onChange={(e) => void onSearch(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") onEnter();
        }}
      />
      {hits.length > 0 && (
        <div className="search-dropdown card">
          {hits.map((hit) => (
            <button
              key={hit.id}
              type="button"
              className="search-hit"
              onClick={() => onSelect(hit)}
            >
              {hit.name_ru} <span className="meta">{hit.country.toUpperCase()}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

type ProductTopbarProps = {
  onMenuToggle: () => void;
};

export function ProductTopbar({ onMenuToggle }: ProductTopbarProps) {
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [searchOpen, setSearchOpen] = useState(false);

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

  const selectHit = (hit: SearchHit) => {
    setHits([]);
    setQuery(hit.name_ru);
    setSearchOpen(false);
    window.location.assign("/app/indicators");
  };

  const goToSearch = () => {
    if (hits[0]) {
      selectHit(hits[0]);
    } else if (query.trim()) {
      setSearchOpen(false);
      window.location.assign("/app/indicators");
    }
  };

  return (
    <>
      <div className="topbar">
        <div className="topbar-start">
          <button type="button" className="icon-btn menu-toggle" onClick={onMenuToggle} aria-label="Меню">
            <i className="ti ti-menu-2" />
          </button>
          <SearchBox
            query={query}
            hits={hits}
            onSearch={onSearch}
            onSelect={selectHit}
            onEnter={goToSearch}
          />
        </div>
        <div className="topbar-actions">
          <button
            type="button"
            className="icon-btn search-mobile-btn"
            onClick={() => setSearchOpen(true)}
            aria-label="Поиск"
          >
            <i className="ti ti-search" />
          </button>
          <ThemeToggle />
        </div>
      </div>

      {searchOpen && (
        <div className="search-mobile-overlay" onClick={() => setSearchOpen(false)}>
          <div className="search-mobile-panel" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="Поиск показателей">
            <div className="search-mobile-head">
              <span>Поиск показателей</span>
              <button type="button" className="icon-btn" onClick={() => setSearchOpen(false)} aria-label="Закрыть">
                <i className="ti ti-x" />
              </button>
            </div>
            <SearchBox
              query={query}
              hits={hits}
              onSearch={onSearch}
              onSelect={selectHit}
              onEnter={goToSearch}
              className="search-box--mobile"
            />
          </div>
        </div>
      )}
    </>
  );
}
