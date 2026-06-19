"use client";

type MiniSparklineProps = {
  values: number[];
  width?: number;
  height?: number;
};

export function MiniSparkline({ values, width = 72, height = 28 }: MiniSparklineProps) {
  if (!values.length) return <svg width={width} height={height} aria-hidden />;

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = values.length > 1 ? width / (values.length - 1) : width;
  const points = values
    .map((v, i) => {
      const x = i * step;
      const y = height - ((v - min) / range) * (height - 4) - 2;
      return `${x},${y}`;
    })
    .join(" ");

  const trend = values[values.length - 1] - values[0];
  const stroke = trend > 0 ? "var(--positive-text)" : trend < 0 ? "var(--negative-text)" : "var(--neutral-text)";

  return (
    <svg width={width} height={height} aria-hidden className="mini-spark">
      <polyline fill="none" stroke={stroke} strokeWidth="1.5" points={points} />
    </svg>
  );
}
