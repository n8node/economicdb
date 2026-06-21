import { DashboardView } from "@/components/dashboard/DashboardView";
import { fetchDashboardOverview, type DashboardOverview } from "@/lib/dashboard";

const FALLBACK: DashboardOverview = {
  updated_at: "—",
  kpis: [],
  ai_summary: { period: "—", headline: "Данные временно недоступны", bullets: [], summary_id: null },
  calendar_events: [],
  changes: [],
};

export default async function AppDashboardPage() {
  let data: DashboardOverview;
  try {
    data = await fetchDashboardOverview();
  } catch {
    data = FALLBACK;
  }
  return <DashboardView data={data} />;
}
