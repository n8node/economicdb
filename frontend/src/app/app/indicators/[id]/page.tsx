import "@/styles/chart-shared.css";
import "@/styles/indicator-detail.css";
import { IndicatorDetailView } from "@/components/indicators/IndicatorDetailView";

export default async function IndicatorDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <IndicatorDetailView id={id} />;
}
