import type { DashboardOverview } from "@/lib/dashboard";
import { DashboardAiSummaryCard } from "@/components/dashboard/DashboardAiSummaryCard";
import { DashboardEventsCard } from "@/components/dashboard/DashboardEventsCard";
import { DashboardFavoritesCompact } from "@/components/dashboard/DashboardFavoritesCompact";

export function DashboardDigestSection({ data }: { data: DashboardOverview }) {
  return (
    <section className="dashboard-digest-grid">
      <DashboardAiSummaryCard summary={data.ai_summary} previous={data.previous_ai_summary} />
      <div className="dashboard-digest-side">
        <DashboardEventsCard events={data.calendar_events} />
        <DashboardFavoritesCompact />
      </div>
    </section>
  );
}
