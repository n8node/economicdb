"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
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

function surpriseClass(direction: string | null) {
  if (direction === "up") return "surprise-up";
  if (direction === "down") return "surprise-down";
  return "surprise-flat";
}

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
          <div>
            {detail && (
              <div className="drawer-badges">
                <span className={`importance-badge ${detail.importance}`}>
                  {IMPORTANCE_LABELS[detail.importance] || detail.importance}
                </span>
                <span className="country-flag">{COUNTRY_LABELS[detail.country] || detail.country.toUpperCase()}</span>
                <span className={`source-tag ${SOURCE_TAG_CLASS[detail.source] || ""}`}>
                  {SOURCE_LABELS[detail.source] || detail.source}
                </span>
              </div>
            )}
            <h2>{detail?.title_ru || "Загрузка…"}</h2>
          </div>
          <button type="button" className="row-icon-btn" onClick={onClose} aria-label="Закрыть">
            <i className="ti ti-x" />
          </button>
        </div>
        {detail && (
          <>
            <p className="meta drawer-time">{detail.scheduled_label}</p>
            <div className="drawer-grid">
              <div className="drawer-metric">
                <span className="meta">Факт</span>
                <p className="metric-value">{detail.actual ?? "—"}</p>
              </div>
              <div className="drawer-metric">
                <span className="meta">Прогноз</span>
                <p className="metric-value">{detail.forecast ?? "—"}</p>
              </div>
              <div className="drawer-metric">
                <span className="meta">Предыдущее</span>
                <p className="metric-value">{detail.previous ?? "—"}</p>
              </div>
              <div className="drawer-metric">
                <span className="meta">Сюрприз</span>
                <p className={`metric-value ${surpriseClass(detail.surprise_direction)}`}>
                  {detail.surprise ?? "—"}
                </p>
              </div>
            </div>
            {detail.linked_indicator_id && (
              <Link href={`/app/indicators/${detail.linked_indicator_id}`} className="drawer-link">
                <i className="ti ti-chart-line" /> Открыть показатель в каталоге
              </Link>
            )}
            <p className="ai-disclaimer">
              Прогноз/consensus часто «—» — универсального бесплатного источника нет. Факты подтягиваются из рядов
              показателей после публикации.
            </p>
          </>
        )}
      </aside>
    </div>
  );
}

function WeekView({ events, onSelect }: { events: CalendarEvent[]; onSelect: (id: string) => void }) {
  const days = useMemo(() => {
    const map = new Map<string, CalendarEvent[]>();
    for (const event of events) {
      const dayKey = event.scheduled_at_msk.slice(0, 10);
      const list = map.get(dayKey) || [];
      list.push(event);
      map.set(dayKey, list);
    }
    const sortedKeys = [...map.keys()].sort();
    const start = sortedKeys[0] ? new Date(sortedKeys[0]) : new Date();
    const weekStart = new Date(start);
    weekStart.setDate(weekStart.getDate() - ((weekStart.getDay() + 6) % 7));
    return Array.from({ length: 7 }, (_, i) => {
      const d = new Date(weekStart);
      d.setDate(d.getDate() + i);
      const key = d.toISOString().slice(0, 10);
      return { date: d, events: map.get(key) || [] };
    });
  }, [events]);

  const weekday = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

  return (
    <div className="week-grid">
      {days.map(({ date, events: dayEvents }, idx) => {
        const isWeekend = idx >= 5;
        const isToday = date.toDateString() === new Date().toDateString();
        return (
          <div key={date.toISOString()} className={`week-day-col${isWeekend ? " weekend" : ""}${isToday ? " today" : ""}`}>
            <div className="week-day-head">
              {weekday[idx]}
              <span className="num">{date.getDate()}</span>
            </div>
            {dayEvents.length === 0 ? (
              <div className="week-empty-note">{isWeekend ? "Выходной" : "Событий нет"}</div>
            ) : (
              dayEvents.map((event) => (
                <button key={event.id} type="button" className="week-mini-event" onClick={() => onSelect(event.id)}>
                  <span className="week-mini-time">{event.scheduled_label.split(", ")[1]?.replace(" МСК", "") || "—"}</span>
                  <span className="country-flag">{event.country.toUpperCase()}</span>
                  <span className="week-mini-title">{event.title_ru}</span>
                  {event.status === "past" && event.actual && <span className="week-mini-actual">{event.actual}</span>}
                </button>
              ))
            )}
          </div>
        );
      })}
    </div>
  );
}

function MonthView({ events, onSelect }: { events: CalendarEvent[]; onSelect: (id: string) => void }) {
  const grouped = useMemo(() => {
    const map = new Map<string, CalendarEvent[]>();
    for (const event of events) {
      const day = event.scheduled_label.split(",")[0];
      const list = map.get(day) || [];
      list.push(event);
      map.set(day, list);
    }
    return [...map.entries()].sort(([a], [b]) => {
      const [da, ma, ya] = a.split(".").map(Number);
      const [db, mb, yb] = b.split(".").map(Number);
      return new Date(ya, ma - 1, da).getTime() - new Date(yb, mb - 1, db).getTime();
    });
  }, [events]);

  return (
    <div className="month-grid">
      {grouped.map(([day, dayEvents]) => (
        <section key={day} className="month-day card card-pad">
          <h3>{day}</h3>
          {dayEvents.map((event) => (
            <button key={event.id} type="button" className="month-event" onClick={() => onSelect(event.id)}>
              <span className={`importance ${event.importance}`} />
              <div>
                <strong>{event.title_ru}</strong>
                <p className="meta">{event.scheduled_label.split(", ")[1]}</p>
              </div>
            </button>
          ))}
        </section>
      ))}
    </div>
  );
}

export function CalendarView() {
  const [view, setView] = useState<"list" | "week" | "month">("list");
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [filters, setFilters] = useState<CalendarFilters>({ status: "upcoming" });
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

  const summary = useMemo(() => {
    const upcoming = events.filter((e) => e.status === "upcoming").length;
    const past = events.filter((e) => e.status === "past").length;
    const high = events.filter((e) => e.importance === "high").length;
    return { upcoming, past, high, total: events.length };
  }, [events]);

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
          <p className="meta">Макроэкономические релизы и решения по ставкам · время по Москве (МСК)</p>
        </div>
        <div className="head-actions">
          <a className="btn" href={calendarIcsUrl()} download="macro-calendar.ics">
            <i className="ti ti-calendar-down" /> Экспорт ICS
          </a>
        </div>
      </div>

      <div className="calendar-summary">
        <div className="summary-card">
          <span className="meta">Показано</span>
          <strong>{summary.total}</strong>
        </div>
        <div className="summary-card">
          <span className="meta">Предстоящие</span>
          <strong>{summary.upcoming}</strong>
        </div>
        <div className="summary-card">
          <span className="meta">Прошедшие</span>
          <strong>{summary.past}</strong>
        </div>
        <div className="summary-card accent">
          <span className="meta">Высокая важность</span>
          <strong>{summary.high}</strong>
        </div>
      </div>

      <div className="toolbar-row">
        <div className="seg">
          {(["list", "week", "month"] as const).map((mode) => (
            <button key={mode} type="button" className={view === mode ? "active" : ""} onClick={() => setView(mode)}>
              {mode === "list" ? "Список" : mode === "week" ? "Неделя" : "Месяц"}
            </button>
          ))}
        </div>
        <div className="legend">
          <span><i className="importance high" /> Высокая</span>
          <span><i className="importance med" /> Средняя</span>
          <span><i className="importance low" /> Низкая</span>
        </div>
      </div>

      <div className="filter-bar">
        <span className="filter-label">Страна</span>
        {(["ru", "us", "eu"] as const).map((c) => (
          <button
            key={c}
            type="button"
            className={`pill ${filters.country?.includes(c) ? "active" : ""}`}
            onClick={() => toggleFilter("country", c)}
          >
            {COUNTRY_LABELS[c]}
          </button>
        ))}
        <span className="filter-divider" />
        <span className="filter-label">Статус</span>
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
        <span className="filter-divider" />
        <span className="filter-label">Важность</span>
        {(["high", "med", "low"] as const).map((imp) => (
          <button
            key={imp}
            type="button"
            className={`pill ${filters.importance?.includes(imp) ? "active" : ""}`}
            onClick={() => toggleFilter("importance", imp)}
          >
            {IMPORTANCE_LABELS[imp]}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="card card-pad"><p className="meta">Загрузка календаря…</p></div>
      ) : events.length === 0 ? (
        <div className="card card-pad empty-state calendar-empty">
          <i className="ti ti-calendar-off empty-icon" />
          <h3>Нет событий по выбранным фильтрам</h3>
          <p className="meta">
            {filters.status === "upcoming"
              ? "Предстоящих событий нет — возможно, синхронизация загрузила только прошлые даты. Переключитесь на «Прошедшие» или попросите администратора пересинхронизировать календарь с датами в будущем."
              : "Если календарь пуст — администратор может загрузить события в разделе «Календарь» админ-панели."}
          </p>
        </div>
      ) : view === "list" ? (
        <div className="event-list">
          {Object.entries(grouped).map(([day, dayEvents]) => (
            <section key={day} className="day-group card card-pad">
              <h3>{day}</h3>
              {dayEvents.map((event) => (
                <button key={event.id} type="button" className="event-row" onClick={() => setSelectedId(event.id)}>
                  <span className={`importance ${event.importance}`} />
                  <div className="event-main">
                    <strong>{event.title_ru}</strong>
                    <p className="meta">
                      {event.scheduled_label.split(", ")[1]} · {IMPORTANCE_LABELS[event.importance]} ·{" "}
                      {CATEGORY_LABELS[event.category] || event.category}
                    </p>
                  </div>
                  <span className={`source-tag ${SOURCE_TAG_CLASS[event.source] || ""}`}>
                    {SOURCE_LABELS[event.source] || event.source}
                  </span>
                  <span className="country-flag">{event.country.toUpperCase()}</span>
                  {event.status === "past" ? (
                    <span className="event-values">
                      <span>{event.actual ?? "—"}</span>
                      <span className="meta"> / {event.forecast ?? "—"}</span>
                      {event.surprise && (
                        <span className={`surprise-badge ${surpriseClass(event.surprise_direction)}`}>
                          {event.surprise}
                        </span>
                      )}
                    </span>
                  ) : (
                    <span className="event-status upcoming">Скоро</span>
                  )}
                </button>
              ))}
            </section>
          ))}
        </div>
      ) : view === "week" ? (
        <div className="card card-pad week-wrap">
          <WeekView events={events} onSelect={setSelectedId} />
        </div>
      ) : (
        <MonthView events={events} onSelect={setSelectedId} />
      )}

      <p className="calendar-footnote meta">
        Источники: Банк России, Росстат, FRED, ECB · Прогнозы часто недоступны (Tier C)
      </p>

      <EventDrawer eventId={selectedId} onClose={() => setSelectedId(null)} />
    </div>
  );
}
