export type DeltaDirection = "up" | "down" | "flat";

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
    updated_at: string;
    sparkline?: number[];
  }>;
  ai_summary: {
    period: string;
    headline: string;
    bullets: string[];
    summary_id: string | null;
  };
  calendar_events: Array<{
    title: string;
    time: string;
    country: string;
  }>;
  changes: Array<{
    direction: DeltaDirection;
    text: string;
    meta: string;
  }>;
};

export async function fetchDashboardOverview(): Promise<DashboardOverview> {
  const { apiFetch } = await import("./api");
  return apiFetch<DashboardOverview>("/dashboard/overview");
}
