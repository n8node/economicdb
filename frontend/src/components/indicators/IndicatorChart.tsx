"use client";

import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import uPlot, { type AlignedData, type Options, type Series } from "uplot";
import "uplot/dist/uPlot.min.css";
import type { SeriesPoint } from "@/lib/indicators";
import { buildHoverPoint, type ChartHoverPoint } from "@/lib/indicatorChart";
import {
  buildBrushOptions,
  createBrushSyncKey,
  mainChartSyncCursor,
  syncBrushSelect,
} from "@/lib/uplotBrush";
import { createYAxisSize } from "@/lib/uplotAxis";
import { deferChartUpdate, safeToUnixDay } from "@/lib/uplotSafe";

function toUnixDay(isoDate: string): number {
  return safeToUnixDay(isoDate) ?? 0;
}

function formatAxisValue(value: number, unit: string | null, normalized: boolean): string {
  if (normalized) return `${value.toFixed(1)}`;
  if (unit === "%") return `${value.toFixed(1)}%`;
  return value.toLocaleString("ru-RU", { maximumFractionDigits: 2 });
}

function formatBrushYear(value: number): string {
  return new Date(value * 1000).getFullYear().toString();
}

type ChartEvent = { date: string; title: string };

export function IndicatorChart({
  points,
  unit,
  name,
  avg,
  min,
  max,
  current,
  events = [],
  normalized = false,
  onHoverIndex,
  onResetZoom,
  resetToken,
}: {
  points: SeriesPoint[];
  unit: string | null;
  name: string;
  avg: number | null;
  min: number | null;
  max: number | null;
  current: number | null;
  events?: ChartEvent[];
  normalized?: boolean;
  onHoverIndex?: (index: number | null) => void;
  onResetZoom?: () => void;
  resetToken?: number;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const brushHostRef = useRef<HTMLDivElement | null>(null);
  const [brushHostEl, setBrushHostEl] = useState<HTMLDivElement | null>(null);
  const setBrushHostRef = useCallback((node: HTMLDivElement | null) => {
    brushHostRef.current = node;
    setBrushHostEl(node);
  }, []);
  const mainRef = useRef<uPlot | null>(null);
  const brushChartRef = useRef<uPlot | null>(null);
  const initialXRef = useRef<{ min: number; max: number } | null>(null);
  const syncKeyRef = useRef(createBrushSyncKey(`indicator-${Math.random().toString(36).slice(2, 10)}`));
  const onHoverIndexRef = useRef(onHoverIndex);
  const [hover, setHover] = useState<ChartHoverPoint | null>(null);
  const [chartError, setChartError] = useState<string | null>(null);

  onHoverIndexRef.current = onHoverIndex;

  useLayoutEffect(() => {
    if (!hostRef.current || points.length === 0) {
      mainRef.current?.destroy();
      mainRef.current = null;
      brushChartRef.current?.destroy();
      brushChartRef.current = null;
      return;
    }

    const host = hostRef.current;
    const syncKey = syncKeyRef.current;
    const xs = points.map((p) => toUnixDay(p.date));
    if (!xs.length) {
      setChartError("Нет данных для графика");
      return;
    }

    setChartError(null);
    const ys = points.map((p) => p.value);
    const fullRange = { min: xs[0], max: xs[xs.length - 1] };
    initialXRef.current = fullRange;

    const series: Series[] = [
      {},
      {
        label: name,
        stroke: "#1B7561",
        width: 2,
        fill: "rgba(27, 117, 97, 0.10)",
      },
    ];

    const data: AlignedData = [xs, ys];
    const showBrush = points.length >= 8;
    const formatY = (value: number) => formatAxisValue(value, unit, normalized);
    const yAxisSize = createYAxisSize(formatY, ys);

    const destroyCharts = () => {
      mainRef.current?.destroy();
      mainRef.current = null;
      brushChartRef.current?.destroy();
      brushChartRef.current = null;
    };

    const mountCharts = () => {
      try {
        const mainWidth = host.clientWidth;
        if (mainWidth < 20) return;

        if (!mainRef.current) {
          const opts: Options = {
            width: mainWidth,
            height: 360,
            scales: { x: { time: true }, y: { auto: true } },
            series,
            legend: { show: false },
            axes: [
              { stroke: "#8b92a0", grid: { show: true, stroke: "rgba(228,231,236,0.8)" } },
              {
                stroke: "#8b92a0",
                grid: { show: true, stroke: "rgba(228,231,236,0.8)" },
                values: (_u, vals) => vals.map((v) => formatY(Number(v))),
                size: yAxisSize,
                gap: 8,
              },
            ],
            cursor: mainChartSyncCursor(syncKey),
            hooks: {
              draw: [
                (u) => {
                  const { ctx } = u;
                  const { left, top, width, height } = u.bbox;
                  const drawHLine = (value: number | null, color: string, dash: number[]) => {
                    if (value === null) return;
                    const y = u.valToPos(value, "y", true);
                    if (y < top || y > top + height) return;
                    ctx.save();
                    ctx.strokeStyle = color;
                    ctx.lineWidth = 1;
                    ctx.setLineDash(dash);
                    ctx.beginPath();
                    ctx.moveTo(left, y);
                    ctx.lineTo(left + width, y);
                    ctx.stroke();
                    ctx.restore();
                  };

                  if (min !== null && max !== null && max > min) {
                    const yMin = u.valToPos(min, "y", true);
                    const yMax = u.valToPos(max, "y", true);
                    ctx.save();
                    ctx.fillStyle = "rgba(27, 117, 97, 0.08)";
                    ctx.fillRect(left, Math.min(yMin, yMax), width, Math.abs(yMax - yMin));
                    ctx.restore();
                  }

                  drawHLine(avg, "#8B92A0", [5, 4]);
                  drawHLine(current, "#1B7561", [2, 2]);

                  for (const event of events) {
                    const x = u.valToPos(toUnixDay(event.date), "x", true);
                    if (x < left || x > left + width) continue;
                    ctx.save();
                    ctx.strokeStyle = "rgba(163, 60, 83, 0.45)";
                    ctx.lineWidth = 1;
                    ctx.setLineDash([3, 3]);
                    ctx.beginPath();
                    ctx.moveTo(x, top);
                    ctx.lineTo(x, top + height);
                    ctx.stroke();
                    ctx.restore();
                  }
                },
              ],
              setCursor: [
                (u) => {
                  const idx = u.cursor.idx ?? null;
                  deferChartUpdate(() => {
                    onHoverIndexRef.current?.(idx);
                    setHover(buildHoverPoint(points, idx));
                  });
                },
              ],
              setScale: [
                (u, scaleKey) => {
                  if (scaleKey !== "x" || !brushChartRef.current) return;
                  const { min: xMin, max: xMax } = u.scales.x;
                  if (xMin == null || xMax == null) return;
                  syncBrushSelect(brushChartRef.current, xMin, xMax);
                },
              ],
            },
          };

          mainRef.current = new uPlot(opts, data, host);
        } else {
          mainRef.current.setSize({ width: mainWidth, height: 360 });
          mainRef.current.setData(data);
        }

        const brushHost = brushHostRef.current;
        if (!showBrush || !brushHost) return;

        const brushWidth = brushHost.clientWidth || mainWidth;
        if (brushWidth < 20) return;

        const mainX = mainRef.current.scales.x;
        const selectRange =
          mainX.min != null && mainX.max != null ? { min: mainX.min, max: mainX.max } : fullRange;

        if (!brushChartRef.current) {
          brushChartRef.current = new uPlot(
            buildBrushOptions({
              width: brushWidth,
              syncKey,
              useDates: true,
              series: [{}, { stroke: "#1B7561", width: 1.5, points: { show: false } }],
              formatX: formatBrushYear,
              initialSelect: selectRange,
            }),
            data,
            brushHost,
          );
        } else {
          brushChartRef.current.setSize({ width: brushWidth, height: 72 });
          brushChartRef.current.setData(data);
          syncBrushSelect(brushChartRef.current, selectRange.min, selectRange.max);
        }
      } catch (error) {
        console.error("[indicator-chart]", error);
        mainRef.current?.destroy();
        mainRef.current = null;
        brushChartRef.current?.destroy();
        brushChartRef.current = null;
        setChartError("Не удалось построить график");
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
  }, [points, unit, name, avg, min, max, current, events, normalized, brushHostEl]);

  useEffect(() => {
    if (!initialXRef.current) return;
    mainRef.current?.setScale("x", initialXRef.current);
    if (brushChartRef.current && initialXRef.current) {
      syncBrushSelect(brushChartRef.current, initialXRef.current.min, initialXRef.current.max);
    }
  }, [resetToken]);

  if (points.length === 0) {
    return <div className="empty-chart">Нет данных за выбранный период</div>;
  }

  if (chartError) {
    return <div className="empty-chart">{chartError}</div>;
  }

  return (
    <div className="chart-stack">
      <div className="chart-tooltip-row">
        {hover ? (
          <div className="chart-tooltip">
            <strong>{new Date(hover.date).toLocaleDateString("ru-RU")}</strong>
            <span>{formatAxisValue(hover.value, unit, normalized)}</span>
            {hover.delta !== null ? (
              <span className={hover.delta >= 0 ? "up" : "down"}>
                {hover.delta >= 0 ? "+" : ""}
                {hover.delta.toFixed(2).replace(".", ",")}
              </span>
            ) : null}
          </div>
        ) : (
          <span className="meta">Наведите на график или потяните для zoom</span>
        )}
        <button
          type="button"
          className="btn chart-reset-btn"
          onClick={() => {
            if (mainRef.current && initialXRef.current) {
              mainRef.current.setScale("x", initialXRef.current);
              if (brushChartRef.current) {
                syncBrushSelect(brushChartRef.current, initialXRef.current.min, initialXRef.current.max);
              }
            }
            onResetZoom?.();
          }}
        >
          Сбросить масштаб
        </button>
      </div>
      <div className="indicator-chart-host" ref={hostRef} />
      {points.length >= 8 ? (
        <div className="chart-brush-panel">
          <div className="chart-brush-head">
            <span className="chart-brush-label">Масштаб по времени</span>
            <span className="chart-brush-hint">Выделите диапазон — основной график обновится</span>
          </div>
          <div className="chart-brush-host" ref={setBrushHostRef} />
        </div>
      ) : null}
    </div>
  );
}
