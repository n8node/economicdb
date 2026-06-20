"use client";

import { useEffect, useRef, useState } from "react";
import uPlot, { type AlignedData, type Options, type Series } from "uplot";
import "uplot/dist/uPlot.min.css";
import type { SeriesPoint } from "@/lib/indicators";
import { buildHoverPoint, type ChartHoverPoint } from "@/lib/indicatorChart";

function toUnixDay(isoDate: string): number {
  return Math.floor(new Date(`${isoDate.slice(0, 10)}T00:00:00Z`).getTime() / 1000);
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
  const brushRef = useRef<HTMLDivElement>(null);
  const mainRef = useRef<uPlot | null>(null);
  const brushChartRef = useRef<uPlot | null>(null);
  const initialXRef = useRef<{ min: number; max: number } | null>(null);
  const zoomXRef = useRef<{ min: number; max: number } | null>(null);
  const [hover, setHover] = useState<ChartHoverPoint | null>(null);

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

  useEffect(() => {
    if (!hostRef.current || points.length === 0) return;

    const xs = points.map((p) => toUnixDay(p.date));
    const ys = points.map((p) => p.value);
    initialXRef.current = { min: xs[0], max: xs[xs.length - 1] };
    zoomXRef.current = { ...initialXRef.current };

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
    const opts: Options = {
      width: hostRef.current.clientWidth,
      height: 360,
      scales: { x: { time: true } },
      series,
      legend: { show: false },
      axes: [
        { stroke: "#8b92a0", grid: { show: true, stroke: "rgba(228,231,236,0.8)" } },
        {
          stroke: "#8b92a0",
          grid: { show: true, stroke: "rgba(228,231,236,0.8)" },
          values: (_u, vals) => vals.map((v) => formatAxisValue(Number(v), unit, normalized)),
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
            onHoverIndex?.(idx);
            setHover(buildHoverPoint(points, idx));
          },
        ],
        setScale: [
          (u, scaleKey) => {
            if (scaleKey !== "x") return;
            const { min: xMin, max: xMax } = u.scales.x;
            if (xMin == null || xMax == null) return;
            zoomXRef.current = { min: xMin, max: xMax };
            brushChartRef.current?.redraw();
          },
        ],
      },
    };

    mainRef.current?.destroy();
    mainRef.current = new uPlot(opts, data, hostRef.current);

    const onResize = () => {
      if (mainRef.current && hostRef.current) {
        mainRef.current.setSize({ width: hostRef.current.clientWidth, height: 360 });
      }
    };
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      mainRef.current?.destroy();
      mainRef.current = null;
    };
  }, [points, unit, name, avg, min, max, current, events, normalized, onHoverIndex]);

  useEffect(() => {
    if (!brushRef.current || points.length < 8) return;
    const brushHost = brushRef.current;
    const xs = points.map((p) => toUnixDay(p.date));
    const ys = points.map((p) => p.value);

    const ensureBrush = () => {
      const width = brushHost.clientWidth;
      if (width < 20) return;
      if (brushChartRef.current) {
        brushChartRef.current.setSize({ width, height: 64 });
        brushChartRef.current.redraw();
        return;
      }
      brushChartRef.current = new uPlot(
        {
          width,
          height: 64,
          padding: [4, 8, 0, 8],
          scales: { x: { time: true } },
          legend: { show: false },
          series: [{}, { stroke: "#1B7561", width: 1.5, points: { show: false } }],
          axes: [
            {
              stroke: "#8b92a0",
              grid: { show: false },
              ticks: { show: false },
              size: 18,
              values: (_u, vals) => vals.map((v) => formatBrushYear(Number(v))),
            },
            { show: false },
          ],
          cursor: { show: true, x: true, y: false, points: { show: false }, drag: { setScale: true, x: true, y: false } },
          hooks: {
            draw: [drawBrushSelection],
            setScale: [
              (u, scaleKey) => {
                if (scaleKey !== "x" || !mainRef.current) return;
                const { min, max } = u.scales.x;
                if (min == null || max == null) return;
                zoomXRef.current = { min, max };
                mainRef.current.setScale("x", { min, max });
                u.redraw();
              },
            ],
          },
        },
        [xs, ys],
        brushHost,
      );
    };

    ensureBrush();
    const observer = new ResizeObserver(ensureBrush);
    observer.observe(brushHost);
    return () => {
      observer.disconnect();
      brushChartRef.current?.destroy();
      brushChartRef.current = null;
    };
  }, [points]);

  useEffect(() => {
    if (!initialXRef.current) return;
    zoomXRef.current = { ...initialXRef.current };
    mainRef.current?.setScale("x", initialXRef.current);
    brushChartRef.current?.setScale("x", initialXRef.current);
    brushChartRef.current?.redraw();
  }, [resetToken]);

  if (points.length === 0) {
    return <div className="empty-chart">Нет данных за выбранный период</div>;
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
      {points.length >= 8 ? (
        <div className="chart-brush-panel">
          <div className="chart-brush-head">
            <span className="chart-brush-label">Масштаб по времени</span>
            <span className="chart-brush-hint">Выделите диапазон — основной график обновится</span>
          </div>
          <div className="chart-brush-host" ref={brushRef} />
        </div>
      ) : null}
    </div>
  );
}
