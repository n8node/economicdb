import { apiFetch } from "./api";

export type ComparePreset = {
  key: string;
  label: string;
  indicator_ids: string[];
};

export type CompareSeriesStats = {
  min: number;
  max: number;
  avg: number;
  change: number;
  change_direction: string;
};

export type CompareSeriesItem = {
  indicator_id: string;
  name_ru: string;
  country: string;
  source: string;
  unit: string | null;
  values: (number | null)[];
  last_value: string | null;
  last_change: string | null;
  delta_direction: string;
  stats: CompareSeriesStats;
};

export type CompareSeriesResponse = {
  labels: string[];
  dates: string[];
  series: CompareSeriesItem[];
  unit_warning: boolean;
  axis_note: string;
  normalize: string;
};

export type CompareRequest = {
  indicator_ids: string[];
  date_from?: string;
  date_to?: string;
  normalize: "absolute" | "index" | "change";
};

export async function fetchComparePresets(): Promise<ComparePreset[]> {
  return apiFetch<ComparePreset[]>("/compare/presets");
}

export async function fetchCompareSeries(body: CompareRequest): Promise<CompareSeriesResponse> {
  return apiFetch<CompareSeriesResponse>("/compare/series", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export const SERIES_COLORS = ["#1B7561", "#2B5A98", "#9A5B26", "#A33C53", "#6B4A9E", "#92701A"];

export function periodToFrom(period: string): string | undefined {
  const end = new Date("2026-06-01");
  const map: Record<string, number> = { "1M": 31, "3M": 92, "6M": 183, "1Y": 365, "3Y": 1095, "5Y": 1825 };
  if (period === "MAX") return undefined;
  const days = map[period] || 365;
  const from = new Date(end);
  from.setDate(from.getDate() - days);
  return from.toISOString().slice(0, 10);
}
