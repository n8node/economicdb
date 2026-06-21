"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  CATEGORY_LABELS,
  IMPORTANCE_LABELS,
  fetchCalendarEvent,
  type CalendarEventDetail,
  type CalendarIndicatorStats,
} from "@/lib/calendar";

const COUNTRY_LABELS: Record<string, string> = {
  ru: "Россия",
  us: "США",
  eu: "Еврозона",
};

const SOURCE_TAG_CLASS: Record<string, string> = {
  cbr: "cbr",
  rosstat: "rosstat",
  fred: "fred",
  ecb: "ecb",
  eurostat: "ecb",
  oecd: "ecb",
};

const SOURCE_LABELS: Record<string, string> = {
  cbr: "Банк России",
  rosstat: "Росстат",
  fred: "FRED",
  ecb: "ECB",
  eurostat: "Eurostat",
  oecd: "OECD",
};

function StatsGrid({ stats }: { stats: CalendarIndicatorStats }) {
  return (
    <div className="cal-modal-stats">
      <div className="cal-stat-box">
        <p className="cal-stat-label">Мин.</p>
        <p className="cal-stat-value">{stats.min}</p>
      </div>
      <div className="cal-stat-box">
        <p className="cal-stat-label">Макс.</p>
        <p className="cal-stat-value">{stats.max}</p>
      </div>
      <div className="cal-stat-box">
        <p className="cal-stat-label">Среднее</p>
        <p className="cal-stat-value">{stats.avg}</p>
      </div>
      <div className="cal-stat-box">
        <p className="cal-stat-label">Медиана</p>
        <p className="cal-stat-value">{stats.median}</p>
      </div>
      <div className="cal-stat-box">
        <p className="cal-stat-label">Изменение</p>
        <p className="cal-stat-value">{stats.change}</p>
      </div>
      <div className="cal-stat-box">
        <p className="cal-stat-label">CAGR</p>
        <p className="cal-stat-value">{stats.cagr ?? "—"}</p>
      </div>
      <div className="cal-stat-box">
        <p className="cal-stat-label">Волатильность</p>
        <p className="cal-stat-value">{stats.volatility}</p>
      </div>
      <div className="cal-stat-box">
        <p className="cal-stat-label">Выше текущего</p>
        <p className="cal-stat-value">{stats.pct_above_current}</p>
      </div>
    </div>
  );
}

type EventModalProps = {
  eventId: string | null;
  onClose: () => void;
};

export function EventModal({ eventId, onClose }: EventModalProps) {
  const [detail, setDetail] = useState<CalendarEventDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!eventId) {
      setDetail(null);
      return;
    }
    setLoading(true);
    fetchCalendarEvent(eventId)
      .then(setDetail)
      .catch(() => setDetail(null))
      .finally(() => setLoading(false));
  }, [eventId]);

  useEffect(() => {
    if (!eventId) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [eventId, onClose]);

  if (!eventId) return null;

  return (
    <div className="cal-modal-overlay" onClick={onClose} role="presentation">
      <div
        className="cal-modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="cal-modal-title"
      >
        <div className="cal-modal-accent" aria-hidden />
        <button type="button" className="cal-modal-close" onClick={onClose} aria-label="Закрыть">
          <i className="ti ti-x" />
        </button>

        {loading || !detail ? (
          <div className="cal-modal-loading">
            <i className="ti ti-loader-2 cal-spin" />
            <p className="meta">Загрузка события…</p>
          </div>
        ) : (
          <>
            <div className="cal-modal-head">
              <div className="cal-modal-badges">
                <span className={`importance-badge ${detail.importance}`}>
                  {IMPORTANCE_LABELS[detail.importance] || detail.importance}
                </span>
                <span className="country-flag">{COUNTRY_LABELS[detail.country] || detail.country.toUpperCase()}</span>
                <span className={`source-tag ${SOURCE_TAG_CLASS[detail.source] || ""}`}>
                  {SOURCE_LABELS[detail.source] || detail.source}
                </span>
                {detail.status === "upcoming" ? (
                  <span className="cal-modal-status upcoming">Предстоящее</span>
                ) : (
                  <span className="cal-modal-status past">Прошедшее</span>
                )}
              </div>
              <h2 id="cal-modal-title">{detail.title_ru}</h2>
              <p className="cal-modal-time">
                <i className="ti ti-clock" /> {detail.scheduled_label}
              </p>
              <p className="meta cal-modal-category">
                {CATEGORY_LABELS[detail.category] || detail.category}
              </p>
            </div>

            {detail.indicator_stats ? (
              <>
                <p className="meta cal-modal-stats-note">Статистика по ряду показателя за 5 лет</p>
                <StatsGrid stats={detail.indicator_stats} />
              </>
            ) : detail.actual ? (
              <div className="cal-modal-metrics">
                <div className="cal-modal-metric">
                  <span className="meta">Факт</span>
                  <p className="metric-value">{detail.actual}</p>
                </div>
              </div>
            ) : (
              <p className="meta cal-modal-empty-stats">Нет связанного показателя для статистики</p>
            )}

            {detail.linked_indicator_id && (
              <Link href={`/app/indicators/${detail.linked_indicator_id}`} className="cal-modal-link" onClick={onClose}>
                <i className="ti ti-chart-line" />
                Открыть показатель в каталоге
              </Link>
            )}

            <p className="ai-disclaimer cal-modal-disclaimer">
              Статистика считается по историческому ряду связанного показателя (окно 5 лет до даты события).
            </p>
          </>
        )}
      </div>
    </div>
  );
}
