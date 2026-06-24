"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { MiniSparkline } from "@/components/indicators/MiniSparkline";
import type { DashboardOverview, DeltaDirection } from "@/lib/dashboard";
import { FAVORITES_KEY, SOURCE_LABELS, toggleId, loadIds } from "@/lib/indicators";

type SparkPeriod = "day" | "week" | "month";

const PERIOD_OPTIONS: { id: SparkPeriod; label: string; points: number }[] = [
  { id: "day", label: "День", points: 5 },
  { id: "week", label: "Неделя", points: 7 },
  { id: "month", label: "Месяц", points: 12 },
];

function formatWeekLabel(date = new Date()): string {
  const day = date.getDay();
  const mondayOffset = day === 0 ? -6 : 1 - day;
  const monday = new Date(date);
  monday.setDate(date.getDate() + mondayOffset);
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);

  const sameMonth = monday.getMonth() === sunday.getMonth();
  const monthFmt = new Intl.DateTimeFormat("ru-RU", { month: "long" });
  const mondayDay = monday.getDate();
  const sundayDay = sunday.getDate();
  const month = monthFmt.format(sunday);
  const year = sunday.getFullYear();

  if (sameMonth) {
    return `Неделя ${mondayDay}–${sundayDay} ${month} ${year}`;
  }
  const mondayMonth = monthFmt.format(monday);
  return `Неделя ${mondayDay} ${mondayMonth} – ${sundayDay} ${month} ${year}`;
}

function formatUpdatedHighlight(updatedAt: string): string {
  const match = updatedAt.match(/(\d{2}\.\d{2})(?:\.\d{4})?,?\s*(\d{2}:\d{2})\s*МСК/);
  if (match) {
    return `${match[1]}, ${match[2]} МСК`;
  }
  return updatedAt;
}

function sliceSparkline(values: number[], period: SparkPeriod): number[] {
  const count = PERIOD_OPTIONS.find((item) => item.id === period)?.points ?? values.length;
  if (!values.length) return values;
  return values.slice(-count);
}

function KpiDelta({
  direction,
  delta,
  unit,
}: {
  direction: DeltaDirection;
  delta: string;
  unit: string | null;
}) {
  if (direction === "flat") {
    const suffix = unit === "п.п." ? " п.п." : unit === "%" ? "%" : "";
    return <span className="kpi-delta flat">- 0{suffix}</span>;
  }

  const icon = direction === "up" ? "ti-arrow-up" : "ti-arrow-down";
  return (
    <span className={`kpi-delta ${direction}`}>
      <i className={`ti ${icon}`} />
      {delta}
    </span>
  );
}

export function MarketKpiSection({ data }: { data: DashboardOverview }) {
  const [period, setPeriod] = useState<SparkPeriod>("week");
  const [favoriteIds, setFavoriteIds] = useState<string[]>([]);

  useEffect(() => {
    setFavoriteIds(loadIds(FAVORITES_KEY));
    const onChanged = () => setFavoriteIds(loadIds(FAVORITES_KEY));
    window.addEventListener("macro_favorites_changed", onChanged);
    window.addEventListener("storage", onChanged);
    return () => {
      window.removeEventListener("macro_favorites_changed", onChanged);
      window.removeEventListener("storage", onChanged);
    };
  }, []);

  const weekLabel = useMemo(() => formatWeekLabel(), []);
  const updatedHighlight = useMemo(() => formatUpdatedHighlight(data.updated_at), [data.updated_at]);

  return (
    <section className="market-overview">
      <div className="market-overview-head">
        <div>
          <h2 className="market-overview-title">Обзор рынка</h2>
          <p className="market-overview-meta">
            {weekLabel} · данные обновлены <span className="market-overview-updated">{updatedHighlight}</span>
          </p>
        </div>
        <div className="seg market-period-seg" role="tablist" aria-label="Период графика">
          {PERIOD_OPTIONS.map((option) => (
            <button
              key={option.id}
              type="button"
              role="tab"
              aria-selected={period === option.id}
              className={period === option.id ? "active" : undefined}
              onClick={() => setPeriod(option.id)}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      <div className="kpi-grid">
        {data.kpis.map((kpi) => {
          const isFavorite = favoriteIds.includes(kpi.id);
          const sparkValues = sliceSparkline(kpi.sparkline || [], period);

          return (
            <Link key={kpi.id} href={`/app/indicators/${kpi.id}`} target="_top" className="kpi-card">
              <div className="kpi-card-top">
                <span className="kpi-source">
                  <span className="kpi-source-dot" aria-hidden />
                  {SOURCE_LABELS[kpi.source] || kpi.source}
                </span>
                <button
                  type="button"
                  className={`kpi-star ${isFavorite ? "active" : ""}`}
                  aria-label={isFavorite ? "Убрать из избранного" : "Добавить в избранное"}
                  onClick={(event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    toggleId(FAVORITES_KEY, kpi.id);
                    setFavoriteIds(loadIds(FAVORITES_KEY));
                  }}
                >
                  <i className={`ti ${isFavorite ? "ti-star-filled" : "ti-star"}`} />
                </button>
              </div>

              <p className="kpi-label">{kpi.label}</p>
              <p className="kpi-value">{kpi.value}</p>
              <KpiDelta direction={kpi.delta_direction} delta={kpi.delta} unit={kpi.unit} />

              <div className={`kpi-spark kpi-spark-${kpi.delta_direction}`}>
                <MiniSparkline
                  values={sparkValues}
                  width={320}
                  height={44}
                  filled
                  responsive
                  direction={kpi.delta_direction}
                />
              </div>

              <p className="kpi-foot">обн. {kpi.updated_at}</p>
            </Link>
          );
        })}
      </div>
    </section>
  );
}
