import type { DeltaDirection } from "@/lib/dashboard";

export const ADVERSE_DELTA_CATEGORIES = new Set(["inflation", "fx"]);

export function usesAdverseDeltaColors(category: string): boolean {
  return ADVERSE_DELTA_CATEGORIES.has(category);
}

export function deltaClassName(direction: DeltaDirection, category: string, base = "kpi-delta"): string {
  if (direction === "flat") return `${base} flat`;
  const adverse = usesAdverseDeltaColors(category);
  return `${base} ${direction}${adverse ? " adverse" : ""}`;
}

export function sparklineDirection(direction: DeltaDirection, category: string): DeltaDirection {
  if (direction === "flat") return "flat";
  if (!usesAdverseDeltaColors(category)) return direction;
  return direction === "up" ? "down" : "up";
}
