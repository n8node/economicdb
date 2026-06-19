export type DeltaDirection = "up" | "down" | "flat";

export type DashboardOverview = {
  updated_at: string;
  kpis: Array<{
    label: string;
    value: string;
    delta: string;
    delta_direction: DeltaDirection;
  }>;
  ai_summary: {
    period: string;
    headline: string;
    bullets: string[];
  };
  calendar_events: Array<{
    title: string;
    time: string;
    country: string;
  }>;
  favorites: Array<{
    label: string;
    value: string;
    delta: string;
    delta_direction: DeltaDirection;
    source: string;
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
