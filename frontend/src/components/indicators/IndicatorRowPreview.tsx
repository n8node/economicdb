"use client";

import { useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { MetaTags } from "@/components/ui/MetaTags";
import { MiniSparkline } from "./MiniSparkline";
import { buildIndicatorDescription } from "@/lib/indicatorPreview";
import { FREQ_LABELS, type IndicatorListItem } from "@/lib/indicators";

const DELTA_ICON = { up: "ti-arrow-up-right", down: "ti-arrow-down-right", flat: "ti-minus" } as const;

type PreviewState = {
  item: IndicatorListItem;
  x: number;
  y: number;
};

function DeltaBadge({ direction, value }: { direction: string; value: string | null }) {
  if (!value) return <span className="preview-delta flat">—</span>;
  return (
    <span className={`preview-delta ${direction}`}>
      <i className={`ti ${DELTA_ICON[direction as keyof typeof DELTA_ICON] || "ti-minus"}`} />
      {value}
    </span>
  );
}

function clampPosition(x: number, y: number, width: number, height: number) {
  const offsetX = 18;
  const offsetY = 14;
  const pad = 12;
  const left = Math.min(Math.max(pad, x + offsetX), Math.max(pad, window.innerWidth - width - pad));
  const top = Math.min(Math.max(pad, y + offsetY), Math.max(pad, window.innerHeight - height - pad));
  return { left, top };
}

export function isRowPreviewBlockedTarget(target: EventTarget | null): boolean {
  if (!(target instanceof Element)) return false;
  return !!target.closest("a, button, input, label, summary, .filter-dropdown");
}

export function IndicatorRowPreview({
  preview,
  visible,
  categoryLabel,
}: {
  preview: PreviewState | null;
  visible: boolean;
  categoryLabel?: string;
}) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState({ left: 0, top: 0 });

  useLayoutEffect(() => {
    if (!preview || !cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    setPosition(clampPosition(preview.x, preview.y, rect.width, rect.height));
  }, [preview?.item.id, preview?.x, preview?.y, visible]);

  if (!preview || typeof document === "undefined") return null;

  const { item } = preview;
  const description = buildIndicatorDescription(item, categoryLabel);

  return createPortal(
    <div
      ref={cardRef}
      className={`indicator-row-preview ${visible ? "is-visible" : "is-hiding"}`}
      style={{ left: position.left, top: position.top }}
      role="tooltip"
      aria-hidden={!visible}
    >
      <div className="indicator-row-preview-glow" aria-hidden="true" />
      <div className="indicator-row-preview-inner" key={item.id}>
        <p className="preview-title">{item.name_ru}</p>
        <p className="preview-desc">{description}</p>
        <div className="preview-chart">
          <MiniSparkline values={item.sparkline ?? []} width={300} height={52} filled />
        </div>
        <div className="preview-kpi">
          <span className="preview-value">{item.last_value ?? "—"}</span>
          <DeltaBadge direction={item.delta_direction} value={item.last_change} />
        </div>
        <div className="preview-meta">
          <MetaTags country={item.country} source={item.source} />
          <span className="preview-freq">{FREQ_LABELS[item.frequency] || item.frequency}</span>
        </div>
      </div>
    </div>,
    document.body,
  );
}
