"use client";

import Link from "next/link";
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

      <div className="card card-pad">
        <p className="section-title">Что изменилось</p>
        {data.changes.map((change) => (
          <div key={change.text} className="change-row">
            <div className={`change-icon ${change.direction}`}>
              <i className={`ti ${CHANGE_ICON[change.direction]}`} />
            </div>
            <div>
              <p className="change-text">{change.text}</p>
              <p className="change-meta">{change.meta}</p>
            </div>
          </div>
        ))}
      </div>

      <footer className="app-footer">
        Данные предоставлены Банком России, Росстатом, FRED, IMF, OECD, ECB/Eurostat.
      </footer>
    </div>
  );
}

const CHANGE_ICON: Record<string, string> = {
  up: "ti-arrow-up-right",
  down: "ti-arrow-down-right",
  flat: "ti-minus",
};
