"use client";

import { AppLink as Link } from "@/components/AppLink";
import { MiniSparkline } from "@/components/indicators/MiniSparkline";
import { useFavoriteIndicators } from "@/hooks/useFavoriteIndicators";
import { SOURCE_LABELS } from "@/lib/indicators";

export function DashboardFavoritesCompact() {
  const { items, loading } = useFavoriteIndicators();
  const preview = items.slice(0, 4);

  return (
    <div className="card card-pad dashboard-side-card">
      <div className="dashboard-card-head">
        <div className="dashboard-card-title-wrap">
          <i className="ti ti-star dashboard-card-icon" />
          <h3 className="card-title">Избранные показатели</h3>
        </div>
        <Link href="/app/favorites" target="_top" className="dashboard-card-link">
          Все
        </Link>
      </div>

      {loading ? (
        <p className="meta">Загрузка…</p>
      ) : preview.length === 0 ? (
        <p className="meta">
          Нет избранных. Отметьте звёздочкой в{" "}
          <Link href="/app/indicators" target="_top">
            каталоге
          </Link>
          .
        </p>
      ) : (
        <div className="dashboard-fav-list">
          {preview.map((item) => (
              <Link key={item.id} href={`/app/indicators/${item.id}`} target="_top" className="dashboard-fav-row">
                <div className="dashboard-fav-copy">
                  <p className="dashboard-fav-name">{item.name_ru}</p>
                  <p className="dashboard-fav-source">{SOURCE_LABELS[item.source] || item.source}</p>
                </div>
                <div className="dashboard-fav-metrics">
                  <p className="dashboard-fav-value">{item.last_value ?? "—"}</p>
                  <span className={`dashboard-fav-delta ${item.delta_direction}`}>{item.last_change ?? "—"}</span>
                </div>
                <div className="dashboard-fav-spark">
                  <MiniSparkline values={item.sparkline ?? []} width={88} height={34} filled responsive />
                </div>
              </Link>
            ))}
        </div>
      )}
    </div>
  );
}
