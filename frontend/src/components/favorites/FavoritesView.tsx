"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FAVORITES_KEY, SOURCE_LABELS, fetchIndicators, loadIds } from "@/lib/indicators";

export function FavoritesView() {
  const [items, setItems] = useState<Awaited<ReturnType<typeof fetchIndicators>>["items"]>([]);

  useEffect(() => {
    const ids = loadIds(FAVORITES_KEY);
    if (!ids.length) {
      setItems([]);
      return;
    }
    fetchIndicators({ page_size: 100 }).then((res) => {
      setItems(res.items.filter((i) => ids.includes(i.id)));
    });
  }, []);

  return (
    <div className="content">
      <div className="page-head">
        <div>
          <h1>Избранное</h1>
          <p className="meta">Показатели, отмеченные звёздочкой в каталоге (localStorage)</p>
        </div>
        <Link href="/app/indicators" className="btn primary">К каталогу</Link>
      </div>
      {items.length === 0 ? (
        <div className="card card-pad"><p>Нет избранных показателей. Отметьте их на странице «Показатели».</p></div>
      ) : (
        <div className="fav-grid">
          {items.map((item) => (
            <div key={item.id} className="fav-card card card-pad">
              <p className="fav-label">{item.name_ru}</p>
              <p className="fav-value">{item.last_value}</p>
              <span className={`delta ${item.delta_direction}`}>{item.last_change}</span>
              <span className={`source-tag ${item.source}`}>{SOURCE_LABELS[item.source] || item.source}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
