"use client";

import { useCallback, useLayoutEffect, useMemo, useRef, useState } from "react";
import uPlot, { type AlignedData, type Series } from "uplot";
import "uplot/dist/uPlot.min.css";
import { SERIES_COLORS, type CompareSeriesResponse } from "@/lib/compare";

function toUnixDay(value: string): number {
  const text = value.slice(0, 10);
  return Math.floor(new Date(`${text}T00:00:00Z`).getTime() / 1000);
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

function formatBrushYear(value: number, useDates: boolean): string {
  if (!useDates) return String(value);
  return new Date(value * 1000).getFullYear().toString();
}

function seriesColor(data: CompareSeriesResponse, indicatorId: string): string {
  const idx = data.series.findIndex((s) => s.indicator_id === indicatorId);
  return SERIES_COLORS[(idx >= 0 ? idx : 0) % SERIES_COLORS.length];
}

function resolveHostWidth(primary: HTMLElement | null, fallback: HTMLElement | null): number {
  const width = primary?.clientWidth ?? 0;
  if (width >= 20) return width;
  return fallback?.clientWidth ?? 0;
}

type HoverRow = { name: string; color: string; value: string };

export function CompareChart({
  data,
  hiddenIds,
  normalize,
  resetToken,
  onResetZoom,
}: {
  data: CompareSeriesResponse | null;
  hiddenIds: Set<string>;
  normalize: "absolute" | "index" | "change";
  resetToken?: number;
  onResetZoom?: () => void;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const brushHostRef = useRef<HTMLDivElement | null>(null);
  const [brushHostEl, setBrushHostEl] = useState<HTMLDivElement | null>(null);
  const setBrushHostRef = useCallback((node: HTMLDivElement | null) => {
    brushHostRef.current = node;
    setBrushHostEl(node);
  }, []);
  const chartRef = useRef<uPlot | null>(null);
  const brushChartRef = useRef<uPlot | null>(null);
  const initialXRef = useRef<{ min: number; max: number } | null>(null);
  const zoomXRef = useRef<{ min: number; max: number } | null>(null);
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  const visibleSeries = useMemo(
    () => data?.series.filter((s) => !hiddenIds.has(s.indicator_id)) ?? [],
    [data, hiddenIds],
  );
  const normalized = normalize !== "absolute";
  const pointCount = data ? data.dates.length || data.labels.length : 0;
  const showBrush = pointCount >= 8;

  const hoverRows = useMemo((): HoverRow[] => {
    if (hoverIdx === null || !data || visibleSeries.length === 0) return [];
    return visibleSeries.map((series) => ({
      name: series.name_ru,
      color: seriesColor(data, series.indicator_id),
      value: formatTooltipValue(series.values[hoverIdx], series.unit, normalized),
    }));
  }, [data, hoverIdx, normalized, visibleSeries]);

  const hoverDate = useMemo(() => {
    if (hoverIdx === null || !data) return null;
    if (data.dates.length > hoverIdx) return new Date(data.dates[hoverIdx]).toLocaleDateString("ru-RU");
    return data.labels[hoverIdx] || null;
  }, [data, hoverIdx]);

  const drawBrushSelection = (u: uPlot) => {
    const full = initialXRef.current;
    const zoom = zoomXRef.current;
    if (!full || !zoom) return;

    const { ctx } = u;
    const { left, top, width, height } = u.bbox;
    const selMin = u.valToPos(zoom.min, "x", true);
    const selMax = u.valToPos(zoom.max, "x", true);
    const x1 = Math.max(left, Math.min(selMin, selMax));
    const x2 = Math.min(left + width, Math.max(selMin, selMax));

    ctx.save();
    ctx.fillStyle = "rgba(20, 24, 31, 0.07)";
    if (x1 > left) ctx.fillRect(left, top, x1 - left, height);
    if (x2 < left + width) ctx.fillRect(x2, top, left + width - x2, height);
    ctx.fillStyle = "rgba(27, 117, 97, 0.10)";
    ctx.fillRect(x1, top, Math.max(x2 - x1, 1), height);
    ctx.strokeStyle = "rgba(27, 117, 97, 0.55)";
    ctx.lineWidth = 1;
    ctx.strokeRect(x1, top, Math.max(x2 - x1, 1), height);
    ctx.restore();
  };

  const syncZoomFromMain = (u: uPlot) => {
    const { min, max } = u.scales.x;
    if (min == null || max == null) return;
    zoomXRef.current = { min, max };
    brushChartRef.current?.redraw();
  };

  useLayoutEffect(() => {
    if (!hostRef.current || !data || visibleSeries.length === 0) return;

    const host = hostRef.current;
    const useDates = data.dates.length > 0;
    const xs = useDates ? data.dates.map(toUnixDay) : data.labels.map((_, i) => i);
    initialXRef.current = { min: xs[0], max: xs[xs.length - 1] };
    zoomXRef.current = { ...initialXRef.current };

    const seriesList: Series[] = [
      {},
      ...visibleSeries.map((s) => ({
        label: s.name_ru,
        stroke: seriesColor(data, s.indicator_id),
        width: 2,
        spanGaps: true,
      })),
    ];

    const seriesData: AlignedData = [
      xs,
      ...visibleSeries.map((s) => s.values.map((v) => (v === null ? null : v))),
    ];

    const brushSeries: Series[] = [
      {},
      ...visibleSeries.map((s) => ({
        stroke: seriesColor(data, s.indicator_id),
        width: 1.5,
        spanGaps: true,
        points: { show: false },
      })),
    ];

    const destroyCharts = () => {
      chartRef.current?.destroy();
      chartRef.current = null;
      brushChartRef.current?.destroy();
      brushChartRef.current = null;
    };

    const mountCharts = () => {
      const mainWidth = resolveHostWidth(host, null);
      if (mainWidth < 20) return;

      if (!chartRef.current) {
        chartRef.current = new uPlot(
          {
            width: mainWidth,
            height: 360,
            scales: { x: { time: useDates } },
            series: seriesList,
            legend: { show: false },
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
              points: { show: false },
              drag: { setScale: true, x: true, y: false },
            },
            hooks: {
              setCursor: [
                (u) => {
                  setHoverIdx(u.cursor.idx ?? null);
                },
              ],
              setScale: [
                (u, scaleKey) => {
                  if (scaleKey === "x") syncZoomFromMain(u);
                },
              ],
            },
          },
          seriesData,
          host,
        );
      } else {
        chartRef.current.setSize({ width: mainWidth, height: 360 });
        chartRef.current.setData(seriesData);
      }

      const brushHost = brushHostRef.current;
      if (!showBrush || !brushHost) return;

      const brushWidth = resolveHostWidth(brushHost, host);
      if (brushWidth < 20) return;

      if (!brushChartRef.current) {
        brushChartRef.current = new uPlot(
          {
            width: brushWidth,
            height: 64,
            padding: [4, 8, 0, 8],
            scales: { x: { time: useDates } },
            legend: { show: false },
            series: brushSeries,
            axes: [
              {
                stroke: "#8b92a0",
                grid: { show: false },
                ticks: { show: false },
                size: 18,
                values: (_u, vals) => vals.map((v) => formatBrushYear(Number(v), useDates)),
              },
              { show: false },
            ],
            cursor: {
              show: true,
              x: true,
              y: false,
              points: { show: false },
              drag: { setScale: true, x: true, y: false },
            },
            hooks: {
              draw: [drawBrushSelection],
              setScale: [
                (u, scaleKey) => {
                  if (scaleKey !== "x" || !chartRef.current) return;
                  const { min, max } = u.scales.x;
                  if (min == null || max == null) return;
                  zoomXRef.current = { min, max };
                  chartRef.current.setScale("x", { min, max });
                  u.redraw();
                },
              ],
            },
          },
          seriesData,
          brushHost,
        );
      } else {
        brushChartRef.current.setSize({ width: brushWidth, height: 64 });
        brushChartRef.current.setData(seriesData);
        brushChartRef.current.redraw();
      }
    };

    destroyCharts();
    mountCharts();

    const observer = new ResizeObserver(() => {
      mountCharts();
    });
    observer.observe(host);
    if (brushHostRef.current) observer.observe(brushHostRef.current);

    return () => {
      observer.disconnect();
      destroyCharts();
    };
  }, [brushHostEl, data, normalized, showBrush, visibleSeries]);

  useLayoutEffect(() => {
    if (!initialXRef.current) return;
    zoomXRef.current = { ...initialXRef.current };
    chartRef.current?.setScale("x", initialXRef.current);
    brushChartRef.current?.setScale("x", initialXRef.current);
    brushChartRef.current?.redraw();
  }, [resetToken]);

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
          <div className="chart-tooltip">
            <strong>{hoverDate}</strong>
            {hoverRows.map((row) => (
              <span key={row.name} className="chart-tooltip-item">
                <span className="chart-tooltip-dot" style={{ background: row.color }} />
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
              zoomXRef.current = { ...initialXRef.current };
              brushChartRef.current?.setScale("x", initialXRef.current);
              brushChartRef.current?.redraw();
            }
            onResetZoom?.();
          }}
        >
          Сбросить масштаб
        </button>
      </div>
      <div className="indicator-chart-host" ref={hostRef} />
      {showBrush ? (
        <div className="chart-brush-panel">
          <div className="chart-brush-head">
            <span className="chart-brush-label">Масштаб по времени</span>
            <span className="chart-brush-hint">Выделите диапазон — основной график обновится</span>
          </div>
          <div className="chart-brush-host" ref={setBrushHostRef} />
        </div>
      ) : null}
      {data.axis_note ? <p className="chart-footnote">{data.axis_note}</p> : null}
    </div>
  );
}
