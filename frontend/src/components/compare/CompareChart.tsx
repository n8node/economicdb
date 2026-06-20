"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import uPlot, { type AlignedData, type Options, type Series } from "uplot";
import "uplot/dist/uPlot.min.css";
import { SERIES_COLORS, type CompareSeriesItem, type CompareSeriesResponse } from "@/lib/compare";

function toUnixDay(isoDate: string): number {
  return Math.floor(new Date(`${isoDate.slice(0, 10)}T00:00:00Z`).getTime() / 1000);
}

function formatAxisValue(value: number, normalized: boolean): string {
  if (normalized) return `${value.toFixed(1).replace(".", ",")}`;
  return value.toLocaleString("ru-RU", { maximumFractionDigits: 2 });
}

function formatTooltipValue(value: number | null, unit: string | null, normalized: boolean): string {
  if (value === null) return "—";
  if (normalized) return formatAxisValue(value, true);
  if (unit === "%") return `${value.toFixed(2).replace(".", ",")}%`;
  return value.toLocaleString("ru-RU", { maximumFractionDigits: 4 });
}

type HoverRow = { name: string; color: string; value: string };

export function CompareChart({
  data,
  hiddenIds,
  normalize,
}: {
  data: CompareSeriesResponse | null;
  hiddenIds: Set<string>;
  normalize: "absolute" | "index" | "change";
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const brushRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<uPlot | null>(null);
  const brushChartRef = useRef<uPlot | null>(null);
  const initialXRef = useRef<{ min: number; max: number } | null>(null);
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  const visibleSeries = useMemo(
    () => data?.series.filter((s) => !hiddenIds.has(s.indicator_id)) ?? [],
    [data, hiddenIds],
  );
  const normalized = normalize !== "absolute";

  const hoverRows = useMemo((): HoverRow[] => {
    if (hoverIdx === null || !data || visibleSeries.length === 0) return [];
    return visibleSeries.map((series, idx) => ({
      name: series.name_ru,
      color: SERIES_COLORS[data.series.indexOf(series) % SERIES_COLORS.length],
      value: formatTooltipValue(series.values[hoverIdx], series.unit, normalized),
    }));
  }, [data, hoverIdx, normalized, visibleSeries]);

  const hoverDate = useMemo(() => {
    if (hoverIdx === null || !data) return null;
    if (data.dates.length > hoverIdx) return new Date(data.dates[hoverIdx]).toLocaleDateString("ru-RU");
    return data.labels[hoverIdx] || null;
  }, [data, hoverIdx]);

  useEffect(() => {
    if (!hostRef.current || !data || visibleSeries.length === 0) return;

    const useDates = data.dates.length > 0;
    const xs = useDates ? data.dates.map(toUnixDay) : data.labels.map((_, i) => i);
    initialXRef.current = { min: xs[0], max: xs[xs.length - 1] };

    const seriesList: Series[] = [
      {},
      ...visibleSeries.map((s) => ({
        label: s.name_ru,
        stroke: SERIES_COLORS[data.series.indexOf(s) % SERIES_COLORS.length],
        width: 2,
        spanGaps: true,
      })),
    ];

    const seriesData: AlignedData = [
      xs,
      ...visibleSeries.map((s) => s.values.map((v) => (v === null ? null : v))),
    ];

    const opts: Options = {
      width: hostRef.current.clientWidth,
      height: 380,
      scales: { x: { time: useDates } },
      series: seriesList,
      axes: [
        useDates
          ? { stroke: "#8b92a0", grid: { show: true, stroke: "rgba(228,231,236,0.8)" } }
          : {
              stroke: "#8b92a0",
              grid: { show: true, stroke: "rgba(228,231,236,0.8)" },
              values: (_u, vals) => vals.map((v) => data.labels[Number(v)] || ""),
            },
        {
          stroke: "#8b92a0",
          grid: { show: true, stroke: "rgba(228,231,236,0.8)" },
          values: (_u, vals) => vals.map((v) => formatAxisValue(Number(v), normalized)),
        },
      ],
      cursor: {
        show: true,
        x: true,
        y: false,
        drag: { setScale: true, x: true, y: false },
      },
      hooks: {
        setCursor: [
          (u) => {
            setHoverIdx(u.cursor.idx ?? null);
          },
        ],
      },
    };

    chartRef.current?.destroy();
    chartRef.current = new uPlot(opts, seriesData, hostRef.current);

    const onResize = () => {
      if (chartRef.current && hostRef.current) {
        chartRef.current.setSize({ width: hostRef.current.clientWidth, height: 380 });
      }
    };
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      chartRef.current?.destroy();
      chartRef.current = null;
    };
  }, [data, normalized, visibleSeries]);

  useEffect(() => {
    if (!brushRef.current || !data || visibleSeries.length === 0 || xsLength(data) < 8) return;

    const useDates = data.dates.length > 0;
    const xs = useDates ? data.dates.map(toUnixDay) : data.labels.map((_, i) => i);
    const first = visibleSeries[0];
    const ys = first.values.map((v) => (v === null ? null : v));

    brushChartRef.current?.destroy();
    brushChartRef.current = new uPlot(
      {
        width: brushRef.current.clientWidth,
        height: 56,
        scales: { x: { time: useDates } },
        series: [{}, { stroke: SERIES_COLORS[data.series.indexOf(first) % SERIES_COLORS.length], width: 1, points: { show: false } }],
        axes: [{ show: false }, { show: false }],
        cursor: { show: true, x: true, y: false, drag: { setScale: true, x: true, y: false } },
        hooks: {
          setScale: [
            (u, scaleKey) => {
              if (scaleKey !== "x" || !chartRef.current) return;
              const { min, max } = u.scales.x;
              if (min == null || max == null) return;
              chartRef.current.setScale("x", { min, max });
            },
          ],
        },
      },
      [xs, ys],
      brushRef.current,
    );

    const onResize = () => {
      if (brushChartRef.current && brushRef.current) {
        brushChartRef.current.setSize({ width: brushRef.current.clientWidth, height: 56 });
      }
    };
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      brushChartRef.current?.destroy();
      brushChartRef.current = null;
    };
  }, [data, visibleSeries]);

  if (!data || data.series.length === 0) {
    return <div className="empty-chart">Нет данных для сравнения</div>;
  }

  if (visibleSeries.length === 0) {
    return <div className="empty-chart">Все серии скрыты — включите хотя бы одну</div>;
  }

  return (
    <div className="chart-stack">
      <div className="chart-tooltip-row">
        {hoverRows.length > 0 && hoverDate ? (
          <div className="compare-tooltip">
            <strong>{hoverDate}</strong>
            {hoverRows.map((row) => (
              <span key={row.name} className="compare-tooltip-item">
                <span className="compare-tooltip-dot" style={{ background: row.color }} />
                {row.name}: {row.value}
              </span>
            ))}
          </div>
        ) : (
          <span className="meta">Наведите на график или потяните для zoom</span>
        )}
        <button
          type="button"
          className="btn chart-reset-btn"
          onClick={() => {
            if (chartRef.current && initialXRef.current) {
              chartRef.current.setScale("x", initialXRef.current);
            }
          }}
        >
          Сбросить масштаб
        </button>
      </div>
      <div className="compare-chart-host" ref={hostRef} />
      {xsLength(data) >= 8 ? <div className="compare-brush-host" ref={brushRef} /> : null}
      {data.axis_note ? <p className="axis-note">{data.axis_note}</p> : null}
    </div>
  );
}

function xsLength(data: CompareSeriesResponse): number {
  return data.dates.length || data.labels.length;
}
