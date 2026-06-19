"use client";

import { useEffect, useRef } from "react";
import uPlot from "uplot";
import "uplot/dist/uPlot.min.css";
import { SERIES_COLORS, type CompareSeriesResponse } from "@/lib/compare";

export function CompareChart({ data }: { data: CompareSeriesResponse | null }) {
  const hostRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<uPlot | null>(null);

  useEffect(() => {
    if (!hostRef.current || !data || data.series.length === 0) return;

    const xs = data.labels.map((_, i) => i);
    const seriesData: uPlot.AlignedData = [
      xs,
      ...data.series.map((s) => s.values.map((v) => (v === null ? null : v))),
    ];

    chartRef.current?.destroy();
    chartRef.current = new uPlot(
      {
        width: hostRef.current.clientWidth,
        height: 320,
        series: [
          {},
          ...data.series.map((s, idx) => ({
            label: s.name_ru,
            stroke: SERIES_COLORS[idx % SERIES_COLORS.length],
            width: 2,
          })),
        ],
        axes: [
          {
            values: (_u, vals) => vals.map((v) => data.labels[Number(v)] || ""),
          },
          { values: (_u, vals) => vals.map((v) => String(v)) },
        ],
        legend: { show: true },
      },
      seriesData,
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
  }, [data]);

  return <div className="compare-chart-host" ref={hostRef} />;
}
