"use client";

import { useEffect, useMemo, useState } from "react";
import {
  CATEGORY_LABELS,
  IMPORTANCE_LABELS,
  calendarIcsUrl,
  fetchCalendarEvents,
  type CalendarEvent,
  type CalendarFilters,
} from "@/lib/calendar";
import {
  eventDateKey,
  eventTimeLabel,
  formatDayTitle,
  getMonthGrid,
  getWeekDays,
  getYearMonths,
  isSameDay,
  monthLabel,
  mskToday,
  navigationTitle,
  parseDateKey,
  rangeForView,
  shiftFocusDate,
  shortMonthLabel,
  toDateKey,
  weekdayLabels,
  type CalendarViewMode,
} from "@/lib/calendar-dates";
import { SOURCE_LABELS } from "@/lib/indicators";
import { EventModal } from "@/components/calendar/EventModal";

const COUNTRY_LABELS: Record<string, string> = {
  ru: "Россия",
  us: "США",
  eu: "Еврозона",
};

const VIEW_MODES: { id: CalendarViewMode; label: string }[] = [
  { id: "day", label: "День" },
  { id: "week", label: "Неделя" },
  { id: "month", label: "Месяц" },
  { id: "year", label: "Год" },
  { id: "agenda", label: "Список" },
];

const SOURCE_TAG_CLASS: Record<string, string> = {
  cbr: "cbr",
  rosstat: "rosstat",
  fred: "fred",
  ecb: "ecb",
  eurostat: "ecb",
  oecd: "ecb",
};

function groupEventsByDay(events: CalendarEvent[]): Map<string, CalendarEvent[]> {
  const map = new Map<string, CalendarEvent[]>();
  for (const event of events) {
    const key = eventDateKey(event.scheduled_at_msk);
    const list = map.get(key) || [];
    list.push(event);
    map.set(key, list);
  }
  for (const list of map.values()) {
    list.sort((a, b) => a.scheduled_at_msk.localeCompare(b.scheduled_at_msk));
  }
  return map;
}

function EventChip({
  event,
  compact,
  onSelect,
}: {
  event: CalendarEvent;
  compact?: boolean;
  onSelect: (id: string) => void;
}) {
  return (
    <button
      type="button"
      className={`cal-event-chip importance-${event.importance}${compact ? " compact" : ""}`}
      onClick={() => onSelect(event.id)}
      title={event.title_ru}
    >
      {!compact && <span className="cal-event-chip-time">{eventTimeLabel(event.scheduled_label)}</span>}
      <span className="cal-event-chip-title">{event.title_ru}</span>
    </button>
  );
}

export function CalendarView() {
  const [viewMode, setViewMode] = useState<CalendarViewMode>("month");
  const [focusDate, setFocusDate] = useState(() => mskToday());
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [filters, setFilters] = useState<CalendarFilters>({});
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const range = useMemo(() => rangeForView(viewMode, focusDate), [viewMode, focusDate]);

  useEffect(() => {
    setLoading(true);
    fetchCalendarEvents({ ...filters, from: range.from, to: range.to })
      .then((res) => setEvents(res.items))
      .finally(() => setLoading(false));
  }, [filters, range.from, range.to]);

  const eventsByDay = useMemo(() => groupEventsByDay(events), [events]);
  const today = mskToday();

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

  const openDay = (date: Date) => {
    setFocusDate(date);
    setViewMode("day");
  };

  const renderDayView = () => {
    const key = toDateKey(focusDate);
    const dayEvents = eventsByDay.get(key) || [];

    return (
      <div className="cal-day-view card card-pad">
        <div className="cal-day-head">
          <h3>{formatDayTitle(focusDate)}</h3>
          <span className="meta">{dayEvents.length} событий</span>
        </div>
        {dayEvents.length === 0 ? (
          <p className="cal-empty-day meta">На этот день событий нет</p>
        ) : (
          <div className="cal-day-timeline">
            {dayEvents.map((event) => (
              <button key={event.id} type="button" className="cal-day-event" onClick={() => setSelectedId(event.id)}>
                <div className="cal-day-event-time">
                  <span className={`importance ${event.importance}`} />
                  {eventTimeLabel(event.scheduled_label)}
                </div>
                <div className="cal-day-event-body">
                  <strong>{event.title_ru}</strong>
                  <p className="meta">
                    {COUNTRY_LABELS[event.country] || event.country.toUpperCase()} ·{" "}
                    {IMPORTANCE_LABELS[event.importance]} · {CATEGORY_LABELS[event.category] || event.category}
                  </p>
                </div>
                <span className={`source-tag ${SOURCE_TAG_CLASS[event.source] || ""}`}>
                  {SOURCE_LABELS[event.source] || event.source}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderWeekView = () => {
    const days = getWeekDays(focusDate);
    return (
      <div className="cal-week-grid">
        {days.map((cell, idx) => {
          const dayEvents = eventsByDay.get(cell.key) || [];
          const isToday = isSameDay(cell.date, today);
          const isWeekend = idx >= 5;
          return (
            <div
              key={cell.key}
              className={`cal-week-col${isWeekend ? " weekend" : ""}${isToday ? " today" : ""}`}
            >
              <button type="button" className="cal-week-col-head" onClick={() => openDay(cell.date)}>
                <span>{weekdayLabels()[idx]}</span>
                <strong>{cell.date.getDate()}</strong>
              </button>
              <div className="cal-week-col-body">
                {dayEvents.length === 0 ? (
                  <span className="cal-week-empty meta">—</span>
                ) : (
                  dayEvents.map((event) => (
                    <EventChip key={event.id} event={event} onSelect={setSelectedId} />
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const renderMonthView = () => {
    const cells = getMonthGrid(focusDate);
    return (
      <div className="cal-month-shell card">
        <div className="cal-month-weekdays">
          {weekdayLabels().map((label) => (
            <span key={label}>{label}</span>
          ))}
        </div>
        <div className="cal-month-grid">
          {cells.map((cell) => {
            const dayEvents = eventsByDay.get(cell.key) || [];
            const isToday = isSameDay(cell.date, today);
            return (
              <div
                key={cell.key}
                className={`cal-month-cell${cell.inMonth ? "" : " outside"}${isToday ? " today" : ""}`}
              >
                <button type="button" className="cal-month-day-num" onClick={() => openDay(cell.date)}>
                  {cell.date.getDate()}
                </button>
                <div className="cal-month-events">
                  {dayEvents.slice(0, 3).map((event) => (
                    <EventChip key={event.id} event={event} compact onSelect={setSelectedId} />
                  ))}
                  {dayEvents.length > 3 && (
                    <button type="button" className="cal-month-more" onClick={() => openDay(cell.date)}>
                      +{dayEvents.length - 3} ещё
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderYearView = () => {
    const months = getYearMonths(focusDate);
    return (
      <div className="cal-year-grid">
        {months.map((monthDate) => {
          const cells = getMonthGrid(monthDate);
          const monthEvents = events.filter((event) => {
            const d = parseDateKey(eventDateKey(event.scheduled_at_msk));
            return d.getFullYear() === monthDate.getFullYear() && d.getMonth() === monthDate.getMonth();
          });
          return (
            <button
              key={monthDate.getMonth()}
              type="button"
              className="cal-year-month card card-pad"
              onClick={() => {
                setFocusDate(monthDate);
                setViewMode("month");
              }}
            >
              <div className="cal-year-month-head">
                <strong>{shortMonthLabel(monthDate)}</strong>
                <span className="meta">{monthEvents.length}</span>
              </div>
              <div className="cal-year-mini-grid">
                {weekdayLabels().map((label) => (
                  <span key={label} className="cal-year-mini-wd">
                    {label.slice(0, 1)}
                  </span>
                ))}
                {cells.map((cell) => {
                  const count = eventsByDay.get(cell.key)?.length || 0;
                  const isToday = isSameDay(cell.date, today);
                  return (
                    <span
                      key={cell.key}
                      className={`cal-year-mini-day${cell.inMonth ? "" : " outside"}${count ? " has-events" : ""}${isToday ? " today" : ""}`}
                    >
                      {cell.inMonth ? cell.date.getDate() : ""}
                    </span>
                  );
                })}
              </div>
            </button>
          );
        })}
      </div>
    );
  };

  const renderAgendaView = () => {
    const sortedKeys = [...eventsByDay.keys()].sort();
    if (sortedKeys.length === 0) {
      return <p className="meta cal-empty-day">Событий в выбранном периоде нет</p>;
    }
    return (
      <div className="cal-agenda">
        {sortedKeys.map((key) => {
          const dayEvents = eventsByDay.get(key) || [];
          const date = parseDateKey(key);
          return (
            <section key={key} className="cal-agenda-day card card-pad">
              <h3>{formatDayTitle(date)}</h3>
              {dayEvents.map((event) => (
                <button key={event.id} type="button" className="cal-agenda-row" onClick={() => setSelectedId(event.id)}>
                  <span className={`importance ${event.importance}`} />
                  <div>
                    <strong>{event.title_ru}</strong>
                    <p className="meta">
                      {eventTimeLabel(event.scheduled_label)} · {IMPORTANCE_LABELS[event.importance]}
                    </p>
                  </div>
                  <span className={`source-tag ${SOURCE_TAG_CLASS[event.source] || ""}`}>
                    {SOURCE_LABELS[event.source] || event.source}
                  </span>
                </button>
              ))}
            </section>
          );
        })}
      </div>
    );
  };

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
          <span className="meta">В периоде</span>
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

      <div className="cal-toolbar card card-pad">
        <div className="cal-nav">
          <button
            type="button"
            className="cal-nav-btn"
            onClick={() => setFocusDate((d) => shiftFocusDate(viewMode, d, -1))}
            aria-label="Предыдущий период"
          >
            <i className="ti ti-chevron-left" />
          </button>
          <button type="button" className="cal-nav-title" onClick={() => setFocusDate(mskToday())}>
            {navigationTitle(viewMode, focusDate)}
          </button>
          <button
            type="button"
            className="cal-nav-btn"
            onClick={() => setFocusDate((d) => shiftFocusDate(viewMode, d, 1))}
            aria-label="Следующий период"
          >
            <i className="ti ti-chevron-right" />
          </button>
          <button type="button" className="cal-today-btn" onClick={() => setFocusDate(mskToday())}>
            Сегодня
          </button>
        </div>

        <div className="toolbar-row cal-toolbar-row">
          <div className="seg">
            {VIEW_MODES.map((mode) => (
              <button
                key={mode.id}
                type="button"
                className={viewMode === mode.id ? "active" : ""}
                onClick={() => setViewMode(mode.id)}
              >
                {mode.label}
              </button>
            ))}
          </div>
          <div className="legend">
            <span><i className="importance high" /> Высокая</span>
            <span><i className="importance med" /> Средняя</span>
            <span><i className="importance low" /> Низкая</span>
          </div>
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
        <div className="card card-pad cal-loading">
          <i className="ti ti-loader-2 cal-spin" />
          <p className="meta">Загрузка календаря…</p>
        </div>
      ) : events.length === 0 ? (
        <div className="card card-pad empty-state calendar-empty">
          <i className="ti ti-calendar-off empty-icon" />
          <h3>Нет событий в {monthLabel(focusDate).toLowerCase()}</h3>
          <p className="meta">
            Попробуйте другой период, снимите фильтры или попросите администратора синхронизировать календарь.
          </p>
        </div>
      ) : (
        <>
          {viewMode === "day" && renderDayView()}
          {viewMode === "week" && renderWeekView()}
          {viewMode === "month" && renderMonthView()}
          {viewMode === "year" && renderYearView()}
          {viewMode === "agenda" && renderAgendaView()}
        </>
      )}

      <p className="calendar-footnote meta">
        Источники: Банк России, Росстат, FRED, ECB · Прогнозы часто недоступны (Tier C)
      </p>

      <EventModal eventId={selectedId} onClose={() => setSelectedId(null)} />
    </div>
  );
}
