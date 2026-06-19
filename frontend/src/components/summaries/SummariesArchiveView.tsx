"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchSummaries, type SummaryListItem } from "@/lib/summaries";

export function SummariesArchiveView() {
  const [items, setItems] = useState<SummaryListItem[]>([]);
  const [region, setRegion] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchSummaries(region || undefined)
      .then((res) => setItems(res.items))
      .finally(() => setLoading(false));
  }, [region]);

  return (
    <div className="content summaries-page">
      <div className="page-head">
        <div>
          <h1>AI-сводки</h1>
          <p className="meta">Еженедельные narrative-сводки на русском (facts-first)</p>
        </div>
      </div>

      <div className="filter-bar">
        {["", "ru", "us", "eu"].map((tag) => (
          <button
            key={tag || "all"}
            type="button"
            className={`pill ${region === tag ? "active" : ""}`}
            onClick={() => setRegion(tag)}
          >
            {tag === "" ? "Все" : tag.toUpperCase()}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="card card-pad"><p className="meta">Загрузка…</p></div>
      ) : (
        <div className="summary-grid">
          {items.map((item, idx) => (
            <Link key={item.id} href={`/app/summaries/${item.id}`} className={`summary-card card card-pad ${idx === 0 ? "pinned" : ""}`}>
              <p className="meta">{item.period_label}</p>
              <h2>{item.headline}</h2>
              <p className="meta">{Math.max(1, Math.round(item.word_count / 200))} мин · {item.source_count} источников</p>
              <span className="ai-badge"><i className="ti ti-sparkles" /> AI</span>
            </Link>
          ))}
        </div>
      )}

      <p className="ai-disclaimer" style={{ marginTop: 16 }}>
        Сгенерировано AI на основе официальных данных. Не является инвестиционной рекомендацией.
      </p>
    </div>
  );
}
