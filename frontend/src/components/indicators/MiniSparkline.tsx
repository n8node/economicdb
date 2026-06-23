"use client";

import { useId } from "react";

type MiniSparklineProps = {
  values: number[];
  width?: number;
  height?: number;
  filled?: boolean;
  responsive?: boolean;
  endDot?: boolean;
  strokeWidth?: number;
};

export function MiniSparkline({
  values,
  width = 72,
  height = 28,
  filled = false,
  responsive = false,
  endDot = false,
  strokeWidth,
}: MiniSparklineProps) {
  const gradientId = useId();
  const safeValues = Array.isArray(values) ? values : [];
  const lineWidth = strokeWidth ?? (filled ? 2 : 1.5);

  if (!safeValues.length) {
    return (
      <svg
        width={responsive ? "100%" : width}
        height={height}
        viewBox={responsive ? `0 0 ${width} ${height}` : undefined}
        aria-hidden
        className={`mini-spark ${responsive ? "mini-spark-responsive" : ""}`}
      />
    );
  }

  const min = Math.min(...safeValues);
  const max = Math.max(...safeValues);
  const range = max - min || 1;
  const padX = 3;
  const padY = 4;
  const plotWidth = Math.max(1, width - padX * 2);
  const plotHeight = Math.max(1, height - padY * 2);
  const step = safeValues.length > 1 ? plotWidth / (safeValues.length - 1) : plotWidth;
  const coords = safeValues.map((v, i) => {
    const x = padX + i * step;
    const y = padY + plotHeight - ((v - min) / range) * plotHeight;
    return { x, y };
  });
  const points = coords.map(({ x, y }) => `${x},${y}`).join(" ");
  const areaPoints = filled
    ? `${coords[0].x},${height - 1} ${points} ${coords[coords.length - 1].x},${height - 1}`
    : "";
  const lastPoint = coords[coords.length - 1];

  const trend = safeValues[safeValues.length - 1] - safeValues[0];
  const stroke = trend > 0 ? "var(--positive-text)" : trend < 0 ? "var(--negative-text)" : "var(--neutral-text)";
  const gradientTop =
    trend > 0 ? "rgba(27, 117, 97, 0.28)" : trend < 0 ? "rgba(163, 60, 83, 0.24)" : "rgba(139, 146, 160, 0.18)";

  return (
    <svg
      width={responsive ? "100%" : width}
      height={height}
      viewBox={responsive ? `0 0 ${width} ${height}` : undefined}
      preserveAspectRatio={responsive ? "none" : undefined}
      aria-hidden
      className={`mini-spark ${filled ? "mini-spark-filled" : ""} ${responsive ? "mini-spark-responsive" : ""}`}
    >
      {filled ? (
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={gradientTop} />
            <stop offset="100%" stopColor="transparent" />
          </linearGradient>
        </defs>
      ) : null}
      {filled ? <polygon points={areaPoints} fill={`url(#${gradientId})`} stroke="none" /> : null}
      <polyline
        fill="none"
        stroke={stroke}
        strokeWidth={lineWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
      {endDot ? (
        <circle cx={lastPoint.x} cy={lastPoint.y} r={2.5} fill={stroke} stroke="var(--bg-surface)" strokeWidth="1.5" />
      ) : null}
    </svg>
  );
}
