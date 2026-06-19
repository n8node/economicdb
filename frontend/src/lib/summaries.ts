import { apiFetch } from "./api";

export type SummaryListItem = {
  id: string;
  period_label: string;
  headline: string;
  tags: string[];
  word_count: number;
  source_count: number;
  generated_at: string;
  status: string;
};

export type SummaryDetail = SummaryListItem & {
  sections: Record<string, string>;
  citations: Record<string, { label: string; value: string; source: string; indicator_id?: string }>;
  reading_minutes: number;
};

export async function fetchSummaries(region?: string) {
  const qs = region ? `?region=${region}` : "";
  return apiFetch<{ items: SummaryListItem[]; total: number }>(`/summaries${qs}`);
}

export async function fetchSummary(id: string) {
  return apiFetch<SummaryDetail>(`/summaries/${id}`);
}

export const SECTION_TITLES: Record<string, string> = {
  intro: "Введение",
  ru: "Россия",
  us: "США",
  eu: "Еврозона",
  fx: "Валюты",
  next_week: "На следующей неделе",
  risks: "Риски",
};
