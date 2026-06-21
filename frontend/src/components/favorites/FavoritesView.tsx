"use client";

import Link from "next/link";
import { FavoriteCardsGrid } from "@/components/favorites/FavoriteCardsGrid";
import { useFavoriteIndicators } from "@/hooks/useFavoriteIndicators";

export function FavoritesView() {
  const { items, loading, reload } = useFavoriteIndicators();

  return (
    <div className="content">
      <div className="page-head">
        <div>
          <h1>Избранное</h1>
          <p className="meta">Показатели, отмеченные звёздочкой в каталоге. Сохраняются в этом браузере.</p>
        </div>
        <Link href="/app/indicators" target="_top" className="btn primary">
          К каталогу
        </Link>
      </div>
      {loading ? (
        <div className="card card-pad">
          <p className="meta">Загрузка избранного…</p>
        </div>
      ) : items.length === 0 ? (
        <div className="card card-pad">
          <p>Нет избранных показателей. Отметьте их на странице «Показатели».</p>
        </div>
      ) : (
        <FavoriteCardsGrid items={items} onChanged={reload} cardClassName="fav-card card card-pad" />
      )}
    </div>
  );
}
