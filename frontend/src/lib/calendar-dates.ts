export type CalendarViewMode = "day" | "week" | "month" | "year" | "agenda";

const WEEKDAY_LABELS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"] as const;
const MONTH_LABELS = [
  "Январь",
  "Февраль",
  "Март",
  "Апрель",
  "Май",
  "Июнь",
  "Июль",
  "Август",
  "Сентябрь",
  "Октябрь",
  "Ноябрь",
  "Декабрь",
] as const;

export function eventDateKey(iso: string): string {
  return iso.slice(0, 10);
}

export function toDateKey(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export function parseDateKey(key: string): Date {
  const [y, m, d] = key.split("-").map(Number);
  return new Date(y, m - 1, d);
}

export function mskToday(): Date {
  const key = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Moscow",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
  return parseDateKey(key);
}

export function isPeriodOnToday(mode: CalendarViewMode, focusDate: Date): boolean {
  const today = mskToday();
  switch (mode) {
    case "day":
      return isSameDay(focusDate, today);
    case "week":
      return toDateKey(startOfWeek(focusDate)) === toDateKey(startOfWeek(today));
    case "month":
    case "agenda":
      return focusDate.getFullYear() === today.getFullYear() && focusDate.getMonth() === today.getMonth();
    case "year":
      return focusDate.getFullYear() === today.getFullYear();
    default:
      return false;
  }
}

export function isSameDay(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

export function addDays(date: Date, days: number): Date {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
}

export function addWeeks(date: Date, weeks: number): Date {
  return addDays(date, weeks * 7);
}

export function addMonths(date: Date, months: number): Date {
  const next = new Date(date.getFullYear(), date.getMonth() + months, date.getDate());
  return next;
}

export function addYears(date: Date, years: number): Date {
  return new Date(date.getFullYear() + years, date.getMonth(), date.getDate());
}

export function startOfWeek(date: Date): Date {
  const day = date.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  return addDays(date, diff);
}

export function endOfWeek(date: Date): Date {
  return addDays(startOfWeek(date), 6);
}

export function startOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

export function endOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth() + 1, 0);
}

export function weekdayLabels(): readonly string[] {
  return WEEKDAY_LABELS;
}

export function monthLabel(date: Date): string {
  return `${MONTH_LABELS[date.getMonth()]} ${date.getFullYear()}`;
}

export function shortMonthLabel(date: Date): string {
  return MONTH_LABELS[date.getMonth()];
}

export function formatDayTitle(date: Date): string {
  return `${date.getDate()} ${MONTH_LABELS[date.getMonth()]} ${date.getFullYear()}`;
}

export function formatWeekTitle(date: Date): string {
  const start = startOfWeek(date);
  const end = endOfWeek(date);
  if (start.getMonth() === end.getMonth()) {
    return `${start.getDate()}–${end.getDate()} ${MONTH_LABELS[start.getMonth()]} ${start.getFullYear()}`;
  }
  if (start.getFullYear() === end.getFullYear()) {
    return `${start.getDate()} ${MONTH_LABELS[start.getMonth()].slice(0, 3)} – ${end.getDate()} ${MONTH_LABELS[end.getMonth()].slice(0, 3)} ${start.getFullYear()}`;
  }
  return `${formatDayTitle(start)} – ${formatDayTitle(end)}`;
}

export function navigationTitle(mode: CalendarViewMode, focusDate: Date): string {
  switch (mode) {
    case "day":
      return formatDayTitle(focusDate);
    case "week":
      return formatWeekTitle(focusDate);
    case "month":
      return monthLabel(focusDate);
    case "year":
      return String(focusDate.getFullYear());
    case "agenda":
      return monthLabel(focusDate);
    default:
      return monthLabel(focusDate);
  }
}

export type CalendarCell = {
  date: Date;
  key: string;
  inMonth: boolean;
};

export function getMonthGrid(focusDate: Date): CalendarCell[] {
  const monthStart = startOfMonth(focusDate);
  const monthEnd = endOfMonth(focusDate);
  const gridStart = startOfWeek(monthStart);
  const gridEnd = addDays(startOfWeek(monthEnd), 6);
  const cells: CalendarCell[] = [];
  let cursor = gridStart;
  while (cursor <= gridEnd) {
    cells.push({
      date: new Date(cursor),
      key: toDateKey(cursor),
      inMonth: cursor.getMonth() === focusDate.getMonth(),
    });
    cursor = addDays(cursor, 1);
  }
  return cells;
}

export function getWeekDays(focusDate: Date): CalendarCell[] {
  const start = startOfWeek(focusDate);
  return Array.from({ length: 7 }, (_, i) => {
    const date = addDays(start, i);
    return {
      date,
      key: toDateKey(date),
      inMonth: true,
    };
  });
}

export function getYearMonths(focusDate: Date): Date[] {
  return Array.from({ length: 12 }, (_, i) => new Date(focusDate.getFullYear(), i, 1));
}

export function rangeForView(mode: CalendarViewMode, focusDate: Date): { from: string; to: string } {
  let start: Date;
  let end: Date;

  switch (mode) {
    case "day":
      start = focusDate;
      end = focusDate;
      break;
    case "week":
      start = startOfWeek(focusDate);
      end = endOfWeek(focusDate);
      break;
    case "month": {
      const grid = getMonthGrid(focusDate);
      start = grid[0].date;
      end = grid[grid.length - 1].date;
      break;
    }
    case "year":
      start = new Date(focusDate.getFullYear(), 0, 1);
      end = new Date(focusDate.getFullYear(), 11, 31);
      break;
    case "agenda":
      start = startOfMonth(focusDate);
      end = endOfMonth(focusDate);
      break;
    default:
      start = startOfMonth(focusDate);
      end = endOfMonth(focusDate);
  }

  return { from: toDateKey(start), to: toDateKey(end) };
}

export function shiftFocusDate(mode: CalendarViewMode, focusDate: Date, direction: -1 | 1): Date {
  switch (mode) {
    case "day":
      return addDays(focusDate, direction);
    case "week":
      return addWeeks(focusDate, direction);
    case "month":
    case "agenda":
      return addMonths(focusDate, direction);
    case "year":
      return addYears(focusDate, direction);
    default:
      return addMonths(focusDate, direction);
  }
}

export function eventTimeLabel(scheduledLabel: string): string {
  return scheduledLabel.split(", ")[1]?.replace(" МСК", "") || "—";
}
