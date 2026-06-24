"use client";

import { AppLink as Link } from "@/components/AppLink";
import { FavoriteCardsGrid } from "@/components/favorites/FavoriteCardsGrid";
import { useFavoriteIndicators } from "@/hooks/useFavoriteIndicators";

export function DashboardFavoritesSection() {
  const { items, loading, reload } = useFavoriteIndicators();

  return (
    <div style={{ marginBottom: 22 }}>
      <p className="section-title">
        Мои избранные показатели
        <Link href="/app/favorites" target="_top" className="btn ghost">
          Все <i className="ti ti-arrow-right" />
        </Link>
      </p>
      {loading ? (
        <div className="card card-pad">
          <p className="meta">Загрузка избранного…</p>
        </div>
      ) : items.length === 0 ? (
        <div className="card card-pad">
          <p className="meta">
            Нет избранных показателей. Отметьте звёздочкой в{" "}
            <Link href="/app/indicators" target="_top">
              каталоге
            </Link>
            .
          </p>
        </div>
      ) : (
        <FavoriteCardsGrid items={items} onChanged={reload} />
      )}
    </div>
  );
}
