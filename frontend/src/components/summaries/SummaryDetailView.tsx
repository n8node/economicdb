"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { SECTION_TITLES, fetchSummary, type SummaryDetail } from "@/lib/summaries";

export function SummaryDetailView({ id }: { id: string }) {
  const [data, setData] = useState<SummaryDetail | null>(null);

  useEffect(() => {
    fetchSummary(id).then(setData).catch(() => setData(null));
  }, [id]);

  if (!data) {
    return (
      <div className="content summaries-page">
        <div className="card card-pad"><p className="meta">Загрузка…</p></div>
      </div>
    );
  }

  return (
    <div className="content summaries-page">
      <Link href="/app/summaries" className="btn ghost" style={{ marginBottom: 12 }}>
        ← Архив
      </Link>
      <p className="meta">{data.period_label} · {data.reading_minutes} мин чтения</p>
      <h1>{data.headline}</h1>

      {Object.entries(data.sections).map(([key, text]) => (
        <section key={key} className="card card-pad" style={{ marginTop: 14 }}>
          <h2>{SECTION_TITLES[key] || key}</h2>
          <p>{text}</p>
        </section>
      ))}

      {Object.keys(data.citations).length > 0 && (
        <details className="card card-pad" style={{ marginTop: 14 }}>
          <summary>Источники и citations</summary>
          <ul>
            {Object.entries(data.citations).map(([key, c]) => (
              <li key={key}>
                {c.label}: {c.value} ({c.source})
              </li>
            ))}
          </ul>
        </details>
      )}

      <p className="ai-disclaimer" style={{ marginTop: 16 }}>
        Сгенерировано AI на основе официальных данных. Не является инвестиционной рекомендацией.
      </p>
    </div>
  );
}
