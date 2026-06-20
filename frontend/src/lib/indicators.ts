import { apiFetch, getApiBase } from "./api";

export type IndicatorListItem = {
  id: string;
  name_ru: string;
  country: string;
  category: string;
  frequency: string;
  source: string;
  unit: string | null;
  last_value: string | null;
  last_change: string | null;
  delta_direction: "up" | "down" | "flat";
  updated_at: string;
  sparkline: number[];
};

export type IndicatorDetail = IndicatorListItem & {
  external_id: string | null;
};

export type SeriesPoint = {
  date: string;
  value: number;
};

export type IndicatorSeriesResponse = {
  indicator_id: string;
  unit: string | null;
  points: SeriesPoint[];
};

export type IndicatorListResponse = {
  items: IndicatorListItem[];
  total: number;
  page: number;
  page_size: number;
};

export type IndicatorFacets = {
  countries: Record<string, number>;
  categories: Record<string, number>;
  frequencies: Record<string, number>;
  sources: Record<string, number>;
};

export type FacetLabels = {
  countries: Record<string, string>;
  categories: Record<string, string>;
};

export type IndicatorFilters = {
  q?: string;
  country?: string[];
  category?: string[];
  frequency?: string[];
  source?: string[];
  updated_within?: number;
  sort?: "name" | "updated" | "country";
  page?: number;
  page_size?: number;
};

function buildQuery(filters: IndicatorFilters): string {
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  filters.country?.forEach((v) => params.append("country", v));
  filters.category?.forEach((v) => params.append("category", v));
  filters.frequency?.forEach((v) => params.append("frequency", v));
  filters.source?.forEach((v) => params.append("source", v));
  if (filters.updated_within) params.set("updated_within", String(filters.updated_within));
  if (filters.sort) params.set("sort", filters.sort);
  if (filters.page) params.set("page", String(filters.page));
  if (filters.page_size) params.set("page_size", String(filters.page_size));
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export async function fetchIndicators(filters: IndicatorFilters = {}): Promise<IndicatorListResponse> {
  return apiFetch<IndicatorListResponse>(`/indicators${buildQuery(filters)}`);
}

export async function fetchIndicatorFacets(): Promise<IndicatorFacets> {
  return apiFetch<IndicatorFacets>("/indicators/facets");
}

export async function fetchFacetLabels(): Promise<FacetLabels> {
  return apiFetch<FacetLabels>("/indicators/facets/labels");
}

export async function fetchIndicator(id: string): Promise<IndicatorDetail | null> {
  const base = getApiBase();
  const url = `${base.replace(/\/$/, "")}/indicators/${encodeURIComponent(id)}`;
  const response = await fetch(url, { cache: "no-store" });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`API ${response.status}`);
  return response.json() as Promise<IndicatorDetail>;
}

export async function fetchIndicatorSeries(
  id: string,
  params: { from?: string; to?: string } = {},
): Promise<IndicatorSeriesResponse | null> {
  const search = new URLSearchParams();
  if (params.from) search.set("from", params.from);
  if (params.to) search.set("to", params.to);
  const qs = search.toString();
  const base = getApiBase();
  const url = `${base.replace(/\/$/, "")}/indicators/${encodeURIComponent(id)}/series${qs ? `?${qs}` : ""}`;
  const response = await fetch(url, { cache: "no-store" });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`API ${response.status}`);
  return response.json() as Promise<IndicatorSeriesResponse>;
}

export const SOURCE_LABELS: Record<string, string> = {
  cbr: "Банк России",
  rosstat: "Росстат",
  fred: "FRED",
  oecd: "OECD",
  ecb: "ECB",
  eurostat: "Eurostat",
  moex: "MOEX",
  imf: "IMF",
  world_bank: "World Bank",
};

export const FREQ_LABELS: Record<string, string> = {
  daily: "D",
  weekly: "W",
  monthly: "M",
  quarterly: "Q",
  yearly: "Y",
};

export const FAVORITES_KEY = "macro_favorites";
export const COMPARE_KEY = "macro_compare_ids";

export function loadIds(key: string): string[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(key) || "[]") as string[];
  } catch {
    return [];
  }
}

export function saveIds(key: string, ids: string[]) {
  localStorage.setItem(key, JSON.stringify(ids));
}

export function toggleId(key: string, id: string): string[] {
  const ids = loadIds(key);
  const next = ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id];
  saveIds(key, next);
  return next;
}
