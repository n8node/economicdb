"use client";

import { useRouter } from "next/navigation";
import { DashboardDigestSection } from "@/components/dashboard/DashboardDigestSection";
import { MarketKpiSection } from "@/components/dashboard/MarketKpiSection";
import type { DashboardOverview } from "@/lib/dashboard";

export function DashboardView({ data }: { data: DashboardOverview }) {
  const router = useRouter();

  return (
    <div className="content">
      <div className="page-head">
        <div>
          <h1>Обзор</h1>
          <p className="meta">Данные обновлены {data.updated_at}</p>
        </div>
        <button type="button" className="btn" onClick={() => router.refresh()}>
          <i className="ti ti-refresh" />
          Обновить
        </button>
      </div>

      <MarketKpiSection data={data} />
      <DashboardDigestSection data={data} />

      <footer className="app-footer">
        Данные предоставлены Банком России, Росстатом, FRED, IMF, OECD, ECB/Eurostat.
      </footer>
    </div>
  );
}
