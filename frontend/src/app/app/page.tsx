import { DashboardView } from "@/components/dashboard/DashboardView";
import { fetchDashboardOverview } from "@/lib/dashboard";

export default async function AppDashboardPage() {
  const data = await fetchDashboardOverview();
  return <DashboardView data={data} />;
}
