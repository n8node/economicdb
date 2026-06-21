"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  CATEGORY_LABELS,
  IMPORTANCE_LABELS,
  fetchCalendarEvent,
  type CalendarEventDetail,
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

function surpriseClass(direction: string | null) {
  if (direction === "up") return "surprise-up";
  if (direction === "down") return "surprise-down";
  return "surprise-flat";
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

            <div className="cal-modal-metrics">
              <div className="cal-modal-metric">
                <span className="meta">Факт</span>
                <p className="metric-value">{detail.actual ?? "—"}</p>
              </div>
              <div className="cal-modal-metric">
                <span className="meta">Прогноз</span>
                <p className="metric-value">{detail.forecast ?? "—"}</p>
              </div>
              <div className="cal-modal-metric">
                <span className="meta">Предыдущее</span>
                <p className="metric-value">{detail.previous ?? "—"}</p>
              </div>
              <div className="cal-modal-metric">
                <span className="meta">Сюрприз</span>
                <p className={`metric-value ${surpriseClass(detail.surprise_direction)}`}>
                  {detail.surprise ?? "—"}
                </p>
              </div>
            </div>

            {detail.linked_indicator_id && (
              <Link href={`/app/indicators/${detail.linked_indicator_id}`} className="cal-modal-link" onClick={onClose}>
                <i className="ti ti-chart-line" />
                Открыть показатель в каталоге
              </Link>
            )}

            <p className="ai-disclaimer cal-modal-disclaimer">
              Прогноз/consensus часто «—» — универсального бесплатного источника нет. Факты подтягиваются из рядов
              показателей после публикации.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
