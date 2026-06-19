import { apiFetch, getApiBase } from "./api";

export type CalendarEvent = {
  id: string;
  title_ru: string;
  country: string;
  category: string;
  importance: string;
  scheduled_at_msk: string;
  scheduled_label: string;
  status: "upcoming" | "past";
  actual: string | null;
  forecast: string | null;
  previous: string | null;
  surprise: string | null;
  surprise_direction: string | null;
  source: string;
  linked_indicator_id: string | null;
};

export type CalendarEventDetail = CalendarEvent & { unit: string | null };

export type CalendarFilters = {
  country?: string[];
  importance?: string[];
  category?: string[];
  status?: "upcoming" | "past";
};

function buildQuery(filters: CalendarFilters): string {
  const params = new URLSearchParams();
  filters.country?.forEach((v) => params.append("country", v));
  filters.importance?.forEach((v) => params.append("importance", v));
  filters.category?.forEach((v) => params.append("category", v));
  if (filters.status) params.set("status", filters.status);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export async function fetchCalendarEvents(filters: CalendarFilters = {}) {
  return apiFetch<{ items: CalendarEvent[]; total: number }>(`/calendar/events${buildQuery(filters)}`);
}

export async function fetchCalendarEvent(id: string) {
  return apiFetch<CalendarEventDetail>(`/calendar/events/${id}`);
}

export function calendarIcsUrl(): string {
  return `${getApiBase().replace(/\/$/, "")}/calendar/export.ics`;
}

export const IMPORTANCE_LABELS: Record<string, string> = {
  high: "Высокая",
  med: "Средняя",
  low: "Низкая",
};

export const CATEGORY_LABELS: Record<string, string> = {
  rates: "Ставки",
  inflation: "Инфляция",
  gdp: "ВВП",
  employment: "Занятость",
  industry: "Промышленность",
  fx: "Валюты",
};
