"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { MiniSparkline } from "@/components/indicators/MiniSparkline";
import type { DashboardOverview, DeltaDirection } from "@/lib/dashboard";
import { FAVORITES_KEY, SOURCE_LABELS, toggleId, loadIds } from "@/lib/indicators";

type SparkPeriod = "day" | "week" | "month";

const PERIOD_OPTIONS: { id: SparkPeriod; label: string; caption: string; points: number }[] = [
  { id: "day", label: "День", caption: "за день", points: 5 },
  { id: "week", label: "Неделя", caption: "за неделю", points: 7 },
  { id: "month", label: "Месяц", caption: "за месяц", points: 12 },
];

const CHANGE_CAPTION: Record<string, string> = {
  daily: "к пред. дню",
  weekly: "к пред. неделе",
  monthly: "к пред. месяцу",
  quarterly: "к пред. кварталу",
  yearly: "к пред. году",
};

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

function formatSignedNumber(value: number, decimals: number): string {
  const fixed = value.toFixed(decimals).replace(".", ",");
  return value > 0 ? `+${fixed}` : fixed;
}

function formatDeltaValue(raw: number, unit: string | null): string {
  if (Math.abs(raw) < 0.005) {
    if (unit === "п.п.") return "0 п.п.";
    if (unit === "%") return "0%";
    return "0";
  }

  if (unit === "п.п.") {
    return `${formatSignedNumber(raw, 2)} п.п.`;
  }
  if (unit === "%") {
    return `${formatSignedNumber(raw, 2)}%`;
  }
  if (unit === "RUB" || unit === "USD" || unit === "EUR" || unit === "index") {
    return formatSignedNumber(raw, 2);
  }

  const pct = raw !== 0 && Math.abs(raw) < 1000 ? raw : raw;
  return `${formatSignedNumber(pct, 2)}%`;
}

function deltaDirectionFromValue(raw: number): DeltaDirection {
  if (Math.abs(raw) < 0.005) return "flat";
  return raw > 0 ? "up" : "down";
}

function computePeriodChange(values: number[], unit: string | null): { direction: DeltaDirection; text: string } {
  if (values.length < 2) {
    return { direction: "flat", text: "—" };
  }

  const raw = values[values.length - 1] - values[0];
  return {
    direction: deltaDirectionFromValue(raw),
    text: formatDeltaValue(raw, unit),
  };
}

import { deltaClassName, usesAdverseDeltaColors } from "@/lib/deltaSemantics";

function changeCaptionForFrequency(frequency: string): string {
  return CHANGE_CAPTION[frequency] || "к пред. значению";
}

function KpiDelta({
  direction,
  delta,
  unit,
  category,
}: {
  direction: DeltaDirection;
  delta: string;
  unit: string | null;
  category: string;
}) {
  if (direction === "flat") {
    const suffix = unit === "п.п." ? " п.п." : unit === "%" ? "%" : "";
    return <span className="kpi-delta flat">- 0{suffix}</span>;
  }

  const adverse = usesAdverseDeltaColors(category);
  const icon = direction === "up" ? "ti-arrow-up" : "ti-arrow-down";
  return (
    <span className={deltaClassName(direction, category)}>
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
  const periodCaption = PERIOD_OPTIONS.find((item) => item.id === period)?.caption ?? "за период";

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
          const periodChange = computePeriodChange(sparkValues, kpi.unit);

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

              <div className="kpi-change-row">
                <KpiDelta
                  direction={kpi.delta_direction}
                  delta={kpi.delta}
                  unit={kpi.unit}
                  category={kpi.category}
                />
                <span className="kpi-change-caption">{changeCaptionForFrequency(kpi.frequency)}</span>
              </div>

              <div className="kpi-spark">
                <MiniSparkline
                  values={sparkValues}
                  width={320}
                  height={44}
                  filled
                  responsive
                  tone="neutral"
                />
              </div>

              <p className="kpi-period-change">
                {periodCaption}:{" "}
                <span className={`kpi-period-change-value ${periodChange.direction}`}>{periodChange.text}</span>
              </p>

              <p className="kpi-foot">обн. {kpi.updated_at}</p>
            </Link>
          );
        })}
      </div>
    </section>
  );
}
