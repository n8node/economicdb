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
  const [hover, setHover] = useState<ChartHoverPoint | null>(null);

  useEffect(() => {
    if (!hostRef.current || points.length === 0) return;

    const xs = points.map((p) => toUnixDay(p.date));
    const ys = points.map((p) => p.value);
    initialXRef.current = { min: xs[0], max: xs[xs.length - 1] };

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
    const xs = points.map((p) => toUnixDay(p.date));
    const ys = points.map((p) => p.value);
    brushChartRef.current?.destroy();
    brushChartRef.current = new uPlot(
      {
        width: brushRef.current.clientWidth,
        height: 56,
        scales: { x: { time: true } },
        series: [{}, { stroke: "#1B7561", width: 1, points: { show: false } }],
        axes: [{ show: false }, { show: false }],
        cursor: { show: true, x: true, y: false, drag: { setScale: true, x: true, y: false } },
        hooks: {
          setScale: [
            (u, scaleKey) => {
              if (scaleKey !== "x" || !mainRef.current) return;
              const { min, max } = u.scales.x;
              if (min == null || max == null) return;
              mainRef.current.setScale("x", { min, max });
            },
          ],
        },
      },
      [xs, ys],
      brushRef.current,
    );
    return () => {
      brushChartRef.current?.destroy();
      brushChartRef.current = null;
    };
  }, [points]);

  useEffect(() => {
    if (!mainRef.current || !initialXRef.current) return;
    mainRef.current.setScale("x", initialXRef.current);
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
            }
            onResetZoom?.();
          }}
        >
          Сбросить масштаб
        </button>
      </div>
      <div className="indicator-chart-host" ref={hostRef} />
      {points.length >= 8 ? <div className="indicator-brush-host" ref={brushRef} /> : null}
    </div>
  );
}
