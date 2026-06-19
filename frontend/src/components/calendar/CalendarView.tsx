"use client";

import { useEffect, useState } from "react";
import {
  CATEGORY_LABELS,
  IMPORTANCE_LABELS,
  calendarIcsUrl,
  fetchCalendarEvent,
  fetchCalendarEvents,
  type CalendarEvent,
  type CalendarEventDetail,
  type CalendarFilters,
} from "@/lib/calendar";
import { SOURCE_LABELS } from "@/lib/indicators";

function EventDrawer({ eventId, onClose }: { eventId: string | null; onClose: () => void }) {
  const [detail, setDetail] = useState<CalendarEventDetail | null>(null);

  useEffect(() => {
    if (!eventId) {
      setDetail(null);
      return;
    }
    fetchCalendarEvent(eventId).then(setDetail).catch(() => setDetail(null));
  }, [eventId]);

  if (!eventId) return null;

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <aside className="event-drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-head">
          <h2>{detail?.title_ru || "Загрузка…"}</h2>
          <button type="button" className="row-icon-btn" onClick={onClose} aria-label="Закрыть">
            <i className="ti ti-x" />
          </button>
        </div>
        {detail && (
          <>
            <p className="meta">{detail.scheduled_label}</p>
            <div className="drawer-grid">
              <div><span className="meta">Факт</span><p>{detail.actual ?? "—"}</p></div>
              <div><span className="meta">Прогноз</span><p>{detail.forecast ?? "—"}</p></div>
              <div><span className="meta">Предыдущее</span><p>{detail.previous ?? "—"}</p></div>
              <div><span className="meta">Сюрприз</span><p>{detail.surprise ?? "—"}</p></div>
            </div>
            <p className="meta">Источник: {SOURCE_LABELS[detail.source] || detail.source}</p>
            <p className="ai-disclaimer">Прогноз/consensus часто «—» для tier C (ручной ввод в админке).</p>
          </>
        )}
      </aside>
    </div>
  );
}

export function CalendarView() {
  const [view, setView] = useState<"list" | "week" | "month">("list");
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [filters, setFilters] = useState<CalendarFilters>({});
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchCalendarEvents(filters)
      .then((res) => setEvents(res.items))
      .finally(() => setLoading(false));
  }, [filters]);

  const toggleFilter = (group: keyof CalendarFilters, value: string) => {
    setFilters((prev) => {
      const current = (prev[group] as string[] | undefined) || [];
      const next = current.includes(value) ? current.filter((x) => x !== value) : [...current, value];
      return { ...prev, [group]: next.length ? next : undefined };
    });
  };

  const grouped = events.reduce<Record<string, CalendarEvent[]>>((acc, event) => {
    const day = event.scheduled_label.split(",")[0];
    acc[day] = acc[day] || [];
    acc[day].push(event);
    return acc;
  }, {});

  return (
    <div className="content calendar-page">
      <div className="page-head">
        <div>
          <h1>Календарь</h1>
          <p className="meta">{events.length} событий</p>
        </div>
        <div className="head-actions">
          <a className="btn" href={calendarIcsUrl()} download="macro-calendar.ics">
            <i className="ti ti-calendar-down" /> Экспорт ICS
          </a>
        </div>
      </div>
      <p className="tz-note">Всё время указано по Москве (МСК, UTC+3)</p>

      <div className="toolbar-row">
        <div className="seg">
          {(["list", "week", "month"] as const).map((mode) => (
            <button key={mode} type="button" className={view === mode ? "active" : ""} onClick={() => setView(mode)}>
              {mode === "list" ? "Список" : mode === "week" ? "Неделя" : "Месяц"}
            </button>
          ))}
        </div>
      </div>

      <div className="filter-bar">
        {(["ru", "us", "eu"] as const).map((c) => (
          <button
            key={c}
            type="button"
            className={`pill ${filters.country?.includes(c) ? "active" : ""}`}
            onClick={() => toggleFilter("country", c)}
          >
            {c.toUpperCase()}
          </button>
        ))}
        {(["upcoming", "past"] as const).map((s) => (
          <button
            key={s}
            type="button"
            className={`pill ${filters.status === s ? "active" : ""}`}
            onClick={() => setFilters((prev) => ({ ...prev, status: prev.status === s ? undefined : s }))}
          >
            {s === "upcoming" ? "Предстоящие" : "Прошедшие"}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="card card-pad"><p className="meta">Загрузка…</p></div>
      ) : events.length === 0 ? (
        <div className="card card-pad empty-state"><p>Нет событий по выбранным фильтрам.</p></div>
      ) : view === "list" ? (
        <div className="event-list">
          {Object.entries(grouped).map(([day, dayEvents]) => (
            <section key={day} className="day-group card card-pad">
              <h3>{day}</h3>
              {dayEvents.map((event) => (
                <button key={event.id} type="button" className="event-row" onClick={() => setSelectedId(event.id)}>
                  <span className={`importance ${event.importance}`} />
                  <div>
                    <strong>{event.title_ru}</strong>
                    <p className="meta">
                      {event.scheduled_label} · {IMPORTANCE_LABELS[event.importance]} · {CATEGORY_LABELS[event.category] || event.category}
                    </p>
                  </div>
                  <span className="country-flag">{event.country.toUpperCase()}</span>
                  {event.status === "past" && (
                    <span className="event-values">
                      {event.actual ?? "—"} / {event.forecast ?? "—"}
                    </span>
                  )}
                </button>
              ))}
            </section>
          ))}
        </div>
      ) : (
        <div className="card card-pad grid-view">
          {events.map((event) => (
            <button key={event.id} type="button" className="grid-event" onClick={() => setSelectedId(event.id)}>
              <span className="meta">{event.scheduled_label}</span>
              <strong>{event.title_ru}</strong>
            </button>
          ))}
        </div>
      )}

      <EventDrawer eventId={selectedId} onClose={() => setSelectedId(null)} />
    </div>
  );
}
