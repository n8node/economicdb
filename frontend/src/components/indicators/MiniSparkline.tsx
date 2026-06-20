"use client";

type MiniSparklineProps = {
  values: number[];
  width?: number;
  height?: number;
  filled?: boolean;
};

export function MiniSparkline({ values, width = 72, height = 28, filled = false }: MiniSparklineProps) {
  if (!values.length) return <svg width={width} height={height} aria-hidden />;

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = values.length > 1 ? width / (values.length - 1) : width;
  const coords = values.map((v, i) => {
    const x = i * step;
    const y = height - ((v - min) / range) * (height - 4) - 2;
    return { x, y };
  });
  const points = coords.map(({ x, y }) => `${x},${y}`).join(" ");
  const areaPoints = filled
    ? `${coords[0].x},${height} ${points} ${coords[coords.length - 1].x},${height}`
    : "";

  const trend = values[values.length - 1] - values[0];
  const stroke = trend > 0 ? "var(--positive-text)" : trend < 0 ? "var(--negative-text)" : "var(--neutral-text)";
  const fill = trend > 0 ? "rgba(27, 117, 97, 0.12)" : trend < 0 ? "rgba(163, 60, 83, 0.10)" : "rgba(139, 146, 160, 0.10)";

  return (
    <svg width={width} height={height} aria-hidden className={`mini-spark ${filled ? "mini-spark-filled" : ""}`}>
      {filled ? <polygon points={areaPoints} fill={fill} stroke="none" /> : null}
      <polyline fill="none" stroke={stroke} strokeWidth="1.5" points={points} />
    </svg>
  );
}
