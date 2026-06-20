import type uPlot from "uplot";

export function safeToUnixDay(value: string): number | null {
  const ts = Math.floor(new Date(`${value.slice(0, 10)}T00:00:00Z`).getTime() / 1000);
  return Number.isFinite(ts) ? ts : null;
}

export function chartSeriesCount(chart: uPlot | null): number {
  if (!chart) return 0;
  return Math.max(0, chart.series.length - 1);
}

export function needsChartRecreate(chart: uPlot | null, dataSeriesCount: number): boolean {
  if (!chart) return true;
  return chartSeriesCount(chart) !== dataSeriesCount;
}

export function deferChartUpdate(run: () => void): void {
  queueMicrotask(run);
}
