"use client";

type MiniSparklineProps = {
  values: number[];
  width?: number;
  height?: number;
  filled?: boolean;
  responsive?: boolean;
};

export function MiniSparkline({
  values,
  width = 72,
  height = 28,
  filled = false,
  responsive = false,
}: MiniSparklineProps) {
  const safeValues = Array.isArray(values) ? values : [];
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
  const padX = 2;
  const plotWidth = Math.max(1, width - padX * 2);
  const step = safeValues.length > 1 ? plotWidth / (safeValues.length - 1) : plotWidth;
  const coords = safeValues.map((v, i) => {
    const x = padX + i * step;
    const y = height - ((v - min) / range) * (height - 4) - 2;
    return { x, y };
  });
  const points = coords.map(({ x, y }) => `${x},${y}`).join(" ");
  const areaPoints = filled
    ? `${coords[0].x},${height} ${points} ${coords[coords.length - 1].x},${height}`
    : "";

  const trend = safeValues[safeValues.length - 1] - safeValues[0];
  const stroke = trend > 0 ? "var(--positive-text)" : trend < 0 ? "var(--negative-text)" : "var(--neutral-text)";
  const fill = trend > 0 ? "rgba(27, 117, 97, 0.12)" : trend < 0 ? "rgba(163, 60, 83, 0.10)" : "rgba(139, 146, 160, 0.10)";

  return (
    <svg
      width={responsive ? "100%" : width}
      height={height}
      viewBox={responsive ? `0 0 ${width} ${height}` : undefined}
      preserveAspectRatio={responsive ? "none" : undefined}
      aria-hidden
      className={`mini-spark ${filled ? "mini-spark-filled" : ""} ${responsive ? "mini-spark-responsive" : ""}`}
    >
      {filled ? <polygon points={areaPoints} fill={fill} stroke="none" /> : null}
      <polyline fill="none" stroke={stroke} strokeWidth="1.5" points={points} />
    </svg>
  );
}
