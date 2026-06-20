import type { IndicatorEventItem, IndicatorStatsResponse, SeriesPoint } from "./indicators";

export type ChartNormalizeMode = "absolute" | "index" | "change";

export type ChartHoverPoint = {
  index: number;
  date: string;
  value: number;
  prevValue: number | null;
  delta: number | null;
};

export function normalizeValue(
  value: number,
  points: SeriesPoint[],
  mode: ChartNormalizeMode,
): number {
  if (mode === "absolute" || points.length === 0) return value;
  const base = points[0].value;
  if (base === 0) return value;
  if (mode === "index") return (value / base) * 100;
  return ((value - base) / Math.abs(base)) * 100;
}

export function normalizeSeries(points: SeriesPoint[], mode: ChartNormalizeMode): SeriesPoint[] {
  if (mode === "absolute" || points.length === 0) return points;
  const base = points[0].value;
  if (base === 0) return points;
  if (mode === "index") {
    return points.map((point) => ({ ...point, value: (point.value / base) * 100 }));
  }
  return points.map((point) => ({
    ...point,
    value: ((point.value - base) / Math.abs(base)) * 100,
  }));
}

export function buildHoverPoint(points: SeriesPoint[], index: number | null): ChartHoverPoint | null {
  if (index === null || index < 0 || index >= points.length) return null;
  const point = points[index];
  const prevValue = index > 0 ? points[index - 1].value : null;
  const delta = prevValue === null ? null : point.value - prevValue;
  return { index, date: point.date, value: point.value, prevValue, delta };
}

export function tableRowsWithDelta(points: SeriesPoint[]) {
  return [...points].reverse().map((point, reverseIdx) => {
    const idx = points.length - 1 - reverseIdx;
    const prev = idx > 0 ? points[idx - 1] : null;
    const delta = prev ? point.value - prev.value : null;
    return { ...point, delta };
  });
}

export function exportSeriesCsv(name: string, points: SeriesPoint[]) {
  const header = "date,value";
  const body = points.map((point) => `${point.date},${point.value}`).join("\n");
  const blob = new Blob([`${header}\n${body}`], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${name.replace(/\s+/g, "_")}.csv`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function formatStatValue(value: number, unit: string | null, mode: ChartNormalizeMode): string {
  if (mode === "index") return `${value.toFixed(2).replace(".", ",")}`;
  if (mode === "change") return `${value >= 0 ? "+" : ""}${value.toFixed(2).replace(".", ",")}%`;
  if (unit === "%") return `${value.toFixed(2).replace(".", ",")}%`;
  return value.toLocaleString("ru-RU", { maximumFractionDigits: 4 });
}

export function eventDates(events: IndicatorEventItem[]): Array<{ date: string; title: string }> {
  return events.map((event) => ({
    date: event.scheduled_at_msk.slice(0, 10),
    title: event.title_ru,
  }));
}

export function heroChipLabel(stats: IndicatorStatsResponse | null, frequency: string): string[] {
  if (!stats) return [];
  const chips: string[] = [];
  if (stats.mom_qoq !== null && stats.mom_qoq !== undefined) {
    chips.push(frequency === "quarterly" ? `QoQ: ${formatSigned(stats.mom_qoq)}` : `MoM: ${formatSigned(stats.mom_qoq)}`);
  }
  if (stats.yoy !== null && stats.yoy !== undefined) {
    chips.push(`YoY: ${formatSigned(stats.yoy)}`);
  }
  if (stats.streak > 0) {
    const dir = stats.streak_direction === "up" ? "рост" : stats.streak_direction === "down" ? "снижение" : "без изменений";
    chips.push(`${stats.streak} пер. ${dir}`);
  }
  return chips;
}

function formatSigned(value: number): string {
  const signed = value > 0 ? `+${value.toFixed(2)}` : value.toFixed(2);
  return signed.replace(".", ",");
}
