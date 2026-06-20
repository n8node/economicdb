import type uPlot from "uplot";

const AXIS_FONT = '12px system-ui, -apple-system, "Segoe UI", sans-serif';
const MIN_Y_AXIS_SIZE = 52;
const Y_AXIS_GAP = 10;

let measureCtx: CanvasRenderingContext2D | null = null;

function getMeasureCtx(): CanvasRenderingContext2D | null {
  if (typeof document === "undefined") return null;
  if (!measureCtx) {
    const canvas = document.createElement("canvas");
    measureCtx = canvas.getContext("2d");
  }
  return measureCtx;
}

export function measureAxisLabelWidth(text: string, font = AXIS_FONT): number {
  const ctx = getMeasureCtx();
  if (!ctx) return text.length * 7;
  ctx.font = font;
  return ctx.measureText(text).width;
}

export function yAxisSizeForLabels(labels: string[]): number {
  let maxWidth = 0;
  for (const label of labels) {
    maxWidth = Math.max(maxWidth, measureAxisLabelWidth(label));
  }
  return Math.max(MIN_Y_AXIS_SIZE, Math.ceil(maxWidth) + Y_AXIS_GAP);
}

export function yAxisSizeFromValues(values: number[], format: (value: number) => string): number {
  if (values.length === 0) return MIN_Y_AXIS_SIZE;
  return yAxisSizeForLabels(values.map((value) => format(value)));
}

export function yAxisSizeFromSeries(values: number[], format: (value: number) => string): number {
  const finite = values.filter((value) => Number.isFinite(value));
  if (finite.length === 0) return MIN_Y_AXIS_SIZE;

  const min = Math.min(...finite);
  const max = Math.max(...finite);
  const samples = new Set<number>([min, max, 0]);
  if (max > min) {
    const step = (max - min) / 4;
    for (let i = 0; i <= 4; i += 1) {
      samples.add(min + step * i);
    }
  }

  return yAxisSizeFromValues([...samples], format);
}

export function createYAxisSize(
  format: (value: number) => string,
  seriesValues: number[],
): (self: uPlot, values: string[], axisIdx: number, cycleNum: number) => number {
  const baseline = yAxisSizeFromSeries(seriesValues, format);
  return (_u, values) => {
    const numeric = values.map((value) => Number(value));
    return Math.max(baseline, yAxisSizeFromValues(numeric, format));
  };
}
