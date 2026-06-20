"use client";

import { useEffect, useRef } from "react";
import uPlot from "uplot";
import "uplot/dist/uPlot.min.css";
import type { SeriesPoint } from "@/lib/indicators";

function toUnixDay(isoDate: string): number {
  return Math.floor(new Date(`${isoDate.slice(0, 10)}T00:00:00Z`).getTime() / 1000);
}

function formatAxisValue(value: number, unit: string | null): string {
  if (unit === "%") return `${value.toFixed(2)}%`;
  if (unit === "index") return value.toFixed(2);
  return value.toLocaleString("ru-RU", { maximumFractionDigits: 2 });
}

export function IndicatorChart({
  points,
  unit,
  name,
}: {
  points: SeriesPoint[];
  unit: string | null;
  name: string;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<uPlot | null>(null);

  useEffect(() => {
    if (!hostRef.current || points.length === 0) return;

    const xs = points.map((p) => toUnixDay(p.date));
    const ys = points.map((p) => p.value);
    chartRef.current?.destroy();
    chartRef.current = new uPlot(
      {
        width: hostRef.current.clientWidth,
        height: 320,
        scales: { x: { time: true } },
        series: [
          {},
          {
            label: name,
            stroke: "#1B7561",
            width: 2,
          },
        ],
        axes: [
          { stroke: "#8b92a0", grid: { show: false } },
          {
            values: (_u, vals) => vals.map((v) => formatAxisValue(Number(v), unit)),
          },
        ],
        legend: { show: false },
      },
      [xs, ys],
      hostRef.current,
    );

    const onResize = () => {
      if (chartRef.current && hostRef.current) {
        chartRef.current.setSize({ width: hostRef.current.clientWidth, height: 320 });
      }
    };
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      chartRef.current?.destroy();
      chartRef.current = null;
    };
  }, [points, unit, name]);

  if (points.length === 0) {
    return <div className="empty-chart">Нет данных за выбранный период</div>;
  }

  return <div className="indicator-chart-host" ref={hostRef} />;
}
