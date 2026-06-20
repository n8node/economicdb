"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { MiniSparkline } from "@/components/indicators/MiniSparkline";
import type { DashboardOverview } from "@/lib/dashboard";

const DELTA_ICON: Record<string, string> = {
  up: "ti-arrow-up-right",
  down: "ti-arrow-down-right",
  flat: "ti-minus",
};

export function DashboardView({ data }: { data: DashboardOverview }) {
  const router = useRouter();

  return (
    <div className="content">
      <div className="page-head">
        <div>
          <h1>Обзор</h1>
          <p className="meta">Данные обновлены {data.updated_at}</p>
        </div>
        <button type="button" className="btn" onClick={() => router.refresh()}>
          <i className="ti ti-refresh" />
          Обновить
        </button>
      </div>

      <div className="kpi-grid">
        {data.kpis.map((kpi) => (
          <div key={kpi.label} className="kpi-card">
            <p className="kpi-label">{kpi.label}</p>
            <p className="kpi-value">{kpi.value}</p>
            <span className={`delta ${kpi.delta_direction}`}>
              <i className={`ti ${DELTA_ICON[kpi.delta_direction]}`} />
              {kpi.delta}
            </span>
            <div className="kpi-spark">
              <MiniSparkline values={kpi.sparkline || []} width={120} height={32} />
            </div>
          </div>
        ))}
      </div>

      <div className="row-2col">
        <div className="card ai-card card-pad">
          <div className="card-head">
            <span className="ai-badge">
              <i className="ti ti-sparkles" />
              AI-сводка
            </span>
            <span className="period">{data.ai_summary.period}</span>
          </div>
          <p className="ai-headline">{data.ai_summary.headline}</p>
          <ul className="ai-bullets">
            {data.ai_summary.bullets.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <Link href="/app/summaries/ws_2026_w25" target="_top" className="btn primary">
            Читать полностью
          </Link>
          <p className="ai-disclaimer">
            Сгенерировано AI на основе официальных данных. Не является инвестиционной рекомендацией.
          </p>
        </div>

        <div className="card card-pad">
          <div className="card-head">
            <p className="card-title">События недели</p>
          </div>
          {data.calendar_events.map((event) => (
            <div key={event.title} className="event-row">
              <div>
                <p className="event-title">{event.title}</p>
                <p className="event-time">{event.time}</p>
              </div>
              <span className={`country-badge ${event.country}`}>{event.country.toUpperCase()}</span>
            </div>
          ))}
          <Link href="/app/calendar" target="_top" className="btn" style={{ width: "100%", marginTop: 14, justifyContent: "center" }}>
            Весь календарь
          </Link>
        </div>
      </div>

      <div style={{ marginBottom: 22 }}>
        <p className="section-title">
          Мои избранные показатели
          <Link href="/app/favorites" target="_top" className="btn ghost">
            Все <i className="ti ti-arrow-right" />
          </Link>
        </p>
        <div className="fav-grid">
          {data.favorites.map((item) => (
            <div key={item.label} className="fav-card">
              <div className="fav-top">
                <p className="fav-label">{item.label}</p>
                <button type="button" className="star-btn active" aria-label="В избранном">
                  <i className="ti ti-star-filled" />
                </button>
              </div>
              <p className="fav-value">{item.value}</p>
              <span className={`delta ${item.delta_direction}`} style={{ fontSize: 11.5 }}>
                {item.delta}
              </span>
              <div>
                <span className={`source-tag ${item.source}`}>
                  {item.source === "cbr" && "Банк России"}
                  {item.source === "rosstat" && "Росстат"}
                  {item.source === "fred" && "FRED"}
                  {item.source === "oecd" && "OECD"}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card card-pad">
        <p className="section-title">Что изменилось</p>
        {data.changes.map((change) => (
          <div key={change.text} className="change-row">
            <div className={`change-icon ${change.direction}`}>
              <i className={`ti ${DELTA_ICON[change.direction]}`} />
            </div>
            <div>
              <p className="change-text">{change.text}</p>
              <p className="change-meta">{change.meta}</p>
            </div>
          </div>
        ))}
      </div>

      <footer className="app-footer">
        Данные предоставлены Банком России, Росстатом, FRED, IMF, OECD, ECB/Eurostat.
      </footer>
    </div>
  );
}
