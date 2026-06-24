export type DeltaDirection = "up" | "down" | "flat";

export type AiSummaryBlock = {
  period: string;
  headline: string;
  bullets: string[];
  summary_id: string | null;
};

export type DashboardOverview = {
  updated_at: string;
  kpis: Array<{
    id: string;
    label: string;
    value: string;
    delta: string;
    delta_direction: DeltaDirection;
    source: string;
    unit: string | null;
    frequency: string;
    category: string;
    updated_at: string;
    sparkline?: number[];
  }>;
  ai_summary: AiSummaryBlock;
  previous_ai_summary: AiSummaryBlock | null;
  calendar_events: Array<{
    title: string;
    date_label: string;
    time_label: string;
    country: string;
    subtext: string | null;
    importance: string;
  }>;
};

export async function fetchDashboardOverview(): Promise<DashboardOverview> {
  const { apiFetch } = await import("./api");
  return apiFetch<DashboardOverview>("/dashboard/overview");
}
