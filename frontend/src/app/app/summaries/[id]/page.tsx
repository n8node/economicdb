import "@/styles/summaries.css";
import { SummaryDetailView } from "@/components/summaries/SummaryDetailView";

export default async function SummaryDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <SummaryDetailView id={id} />;
}
