"use client";

import Link from "next/link";
import { MiniSparkline } from "@/components/indicators/MiniSparkline";
import { FAVORITES_KEY, SOURCE_LABELS, toggleId, type IndicatorListItem } from "@/lib/indicators";

type FavoriteCardsGridProps = {
  items: IndicatorListItem[];
  onChanged?: () => void;
  cardClassName?: string;
};

export function FavoriteCardsGrid({ items, onChanged, cardClassName = "fav-card" }: FavoriteCardsGridProps) {
  return (
    <div className="fav-grid">
      {items.map((item) => (
        <Link
          key={item.id}
          href={`/app/indicators/${item.id}`}
          target="_top"
          className={cardClassName}
        >
          <div className="fav-card-body">
            <div className="fav-main">
              <div className="fav-top">
                <p className="fav-label">{item.name_ru}</p>
                <button
                  type="button"
                  className="star-btn active"
                  aria-label="Убрать из избранного"
                  onClick={(event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    toggleId(FAVORITES_KEY, item.id);
                    onChanged?.();
                  }}
                >
                  <i className="ti ti-star-filled" />
                </button>
              </div>
              <p className="fav-value">{item.last_value ?? "—"}</p>
              <span className={`delta ${item.delta_direction}`}>{item.last_change ?? "—"}</span>
              <div>
                <span className={`source-tag ${item.source}`}>
                  {SOURCE_LABELS[item.source] || item.source}
                </span>
              </div>
            </div>
            <div className={`fav-spark fav-spark-${item.delta_direction}`}>
              <MiniSparkline
                values={item.sparkline ?? []}
                width={80}
                height={50}
                filled
                responsive
                endDot
              />
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}
