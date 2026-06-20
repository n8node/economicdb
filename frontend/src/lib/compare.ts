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

export const MAX_COMPARE_SERIES = 12;

export const SERIES_COLORS = [
  "#1B7561",
  "#2B5A98",
  "#9A5B26",
  "#A33C53",
  "#6B4A9E",
  "#92701A",
  "#0E6655",
  "#154360",
  "#784212",
  "#7B241C",
  "#4A235A",
  "#566573",
];

export function periodToFrom(period: string): string | undefined {
  const end = new Date();
  const map: Record<string, number> = { "1M": 31, "3M": 92, "6M": 183, "1Y": 365, "3Y": 1095, "5Y": 1825 };
  if (period === "MAX") return undefined;
  const days = map[period] || 365;
  const from = new Date(end);
  from.setDate(from.getDate() - days);
  return from.toISOString().slice(0, 10);
}

export function exportCompareCsv(data: CompareSeriesResponse) {
  const headers = ["date", ...data.series.map((s) => s.name_ru.replace(/,/g, " "))];
  const length = data.dates.length || data.labels.length;
  const rows: string[] = [headers.join(",")];
  for (let i = 0; i < length; i += 1) {
    const date = data.dates[i] || data.labels[i] || String(i);
    const values = data.series.map((s) => (s.values[i] == null ? "" : String(s.values[i])));
    rows.push([date, ...values].join(","));
  }
  const blob = new Blob([rows.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "compare.csv";
  anchor.click();
  URL.revokeObjectURL(url);
}
