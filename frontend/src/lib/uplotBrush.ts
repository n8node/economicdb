import uPlot, { type Options, type Series } from "uplot";

export function createBrushSyncKey(scope: string): string {
  return `edb-brush-${scope}`;
}

export function syncBrushSelect(brush: uPlot, xMin: number, xMax: number): void {
  const left = brush.valToPos(xMin, "x");
  const width = brush.valToPos(xMax, "x") - left;
  const top = brush.bbox.top / devicePixelRatio;
  const height = brush.bbox.height / devicePixelRatio;
  brush.setSelect({ left, top, width, height }, false);
}

export type BrushBuildParams = {
  width: number;
  height?: number;
  syncKey: string;
  useDates: boolean;
  series: Series[];
  formatX?: (value: number) => string;
  initialSelect?: { min: number; max: number };
};

export function buildBrushOptions(params: BrushBuildParams): Options {
  const { width, height = 72, syncKey, useDates, series, formatX, initialSelect } = params;

  return {
    width,
    height,
    padding: [4, 8, 0, 8],
    legend: { show: false },
    scales: {
      x: { time: useDates },
      y: { auto: true },
    },
    series,
    axes: [
      {
        stroke: "#8b92a0",
        grid: { show: false },
        ticks: { show: false },
        size: 18,
        values: (_u, vals) => vals.map((v) => (formatX ? formatX(Number(v)) : String(v))),
      },
      { show: false, scale: "y" },
    ],
    cursor: {
      show: true,
      x: true,
      y: false,
      points: { show: false },
      drag: { setScale: false, x: true, y: false },
      sync: { key: syncKey },
    },
    select: { show: true, over: true, left: 0, top: 0, width: 0, height: 0 },
    hooks: {
      ready: initialSelect
        ? [
            (u) => {
              syncBrushSelect(u, initialSelect.min, initialSelect.max);
            },
          ]
        : undefined,
    },
  };
}

export function mainChartSyncCursor(syncKey: string): NonNullable<Options["cursor"]> {
  return {
    show: true,
    x: true,
    y: false,
    points: { show: false },
    drag: { setScale: true, x: true, y: false },
    sync: { key: syncKey },
  };
}
