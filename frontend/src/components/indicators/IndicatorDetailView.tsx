"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { IndicatorChart } from "./IndicatorChart";
import {
  COMPARE_KEY,
  FAVORITES_KEY,
  FREQ_LABELS,
  SOURCE_LABELS,
  fetchFacetLabels,
  fetchIndicator,
  fetchIndicatorSeries,
  loadIds,
  saveIds,
  toggleId,
  type FacetLabels,
  type IndicatorDetail,
  type IndicatorSeriesResponse,
  type SeriesPoint,
} from "@/lib/indicators";

type PeriodKey = "1Y" | "3Y" | "5Y" | "MAX";

const PERIODS: PeriodKey[] = ["1Y", "3Y", "5Y", "MAX"];
const DELTA_ICON = { up: "ti-arrow-up-right", down: "ti-arrow-down-right", flat: "ti-minus" } as const;

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("ru-RU");
}

function formatDateInput(date: Date) {
  return date.toISOString().slice(0, 10);
}

function periodRange(key: PeriodKey): { from?: string; to: string } {
  const to = formatDateInput(new Date());
  if (key === "MAX") return { to };
  const days = key === "1Y" ? 365 : key === "3Y" ? 365 * 3 : 365 * 5;
  const fromDate = new Date();
  fromDate.setDate(fromDate.getDate() - days);
  return { from: formatDateInput(fromDate), to };
}

function formatPointValue(value: number, unit: string | null): string {
  if (unit === "%") return `${value.toFixed(2).replace(".", ",")}%`;
  return value.toLocaleString("ru-RU", { maximumFractionDigits: 4 });
}

function computeStats(points: SeriesPoint[]) {
  if (!points.length) return null;
  const values = points.map((p) => p.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const avg = values.reduce((sum, v) => sum + v, 0) / values.length;
  const change = values[values.length - 1] - values[0];
  return { min, max, avg, change };
}

function DeltaBadge({ direction, value }: { direction: string; value: string | null }) {
  if (!value) return <span className="delta-badge flat">—</span>;
  return (
    <span className={`delta-badge ${direction}`}>
      <i className={`ti ${DELTA_ICON[direction as keyof typeof DELTA_ICON] || "ti-minus"}`} />
      {value}
    </span>
  );
}

export function IndicatorDetailView({ id }: { id: string }) {
  const [indicator, setIndicator] = useState<IndicatorDetail | null>(null);
  const [series, setSeries] = useState<IndicatorSeriesResponse | null>(null);
  const [labels, setLabels] = useState<FacetLabels | null>(null);
  const [period, setPeriod] = useState<PeriodKey>("5Y");
  const [loading, setLoading] = useState(true);
  const [seriesLoading, setSeriesLoading] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const [favoriteIds, setFavoriteIds] = useState<string[]>([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    setFavoriteIds(loadIds(FAVORITES_KEY));
    fetchFacetLabels().then(setLabels).catch(() => undefined);
  }, []);

  useEffect(() => {
    setLoading(true);
    setNotFound(false);
    fetchIndicator(id)
      .then((row) => {
        if (!row) {
          setNotFound(true);
          setIndicator(null);
          return;
        }
        setIndicator(row);
      })
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }, [id]);

  const loadSeries = useCallback(async () => {
    setSeriesLoading(true);
    try {
      const range = periodRange(period);
      const data = await fetchIndicatorSeries(id, range);
      setSeries(data);
    } catch {
      setSeries(null);
    } finally {
      setSeriesLoading(false);
    }
  }, [id, period]);

  useEffect(() => {
    if (!indicator) return;
    void loadSeries();
  }, [indicator, loadSeries]);

  const stats = useMemo(() => computeStats(series?.points || []), [series]);
  const historyPoints = useMemo(() => [...(series?.points || [])].reverse().slice(0, 24), [series]);

  const toggleFavorite = () => {
    if (!indicator) return;
    setFavoriteIds(toggleId(FAVORITES_KEY, indicator.id));
  };

  const addToCompare = () => {
    if (!indicator) return;
    const current = loadIds(COMPARE_KEY);
    if (current.includes(indicator.id)) {
      setMessage("Показатель уже в сравнении");
      return;
    }
    if (current.length >= 6) {
      setMessage("В сравнении не более 6 показателей");
      return;
    }
    saveIds(COMPARE_KEY, [...current, indicator.id]);
    setMessage("Добавлено в сравнение");
  };

  if (loading) {
    return (
      <div className="content indicator-detail-page">
        <div className="card card-pad">
          <p className="meta">Загрузка…</p>
        </div>
      </div>
    );
  }

  if (notFound || !indicator) {
    return (
      <div className="content indicator-detail-page">
        <Link href="/app/indicators" className="btn ghost detail-back">
          ← К каталогу
        </Link>
        <div className="card card-pad">
          <h1>Показатель недоступен</h1>
          <p className="meta">Показатель не найден или скрыт из продукта.</p>
          <Link href="/app/indicators" className="btn primary">
            Перейти в каталог
          </Link>
        </div>
      </div>
    );
  }

  const countryLabel = labels?.countries[indicator.country] || indicator.country.toUpperCase();
  const categoryLabel = labels?.categories[indicator.category] || indicator.category;

  return (
    <div className="content indicator-detail-page">
      <Link href="/app/indicators" className="btn ghost detail-back">
        ← К каталогу
      </Link>

      <div className="detail-hero">
        <div className="detail-head-row">
          <div>
            <h1 style={{ margin: 0 }}>{indicator.name_ru}</h1>
            <p className="meta">{indicator.id}</p>
          </div>
          <div className="detail-actions">
            <button
              type="button"
              className={`btn ${favoriteIds.includes(indicator.id) ? "primary" : ""}`}
              onClick={toggleFavorite}
            >
              <i className={`ti ${favoriteIds.includes(indicator.id) ? "ti-star-filled" : "ti-star"}`} /> Избранное
            </button>
            <button type="button" className="btn" onClick={addToCompare}>
              <i className="ti ti-plus" /> В сравнение
            </button>
            <Link href="/app/compare" className="btn">
              Открыть сравнение
            </Link>
          </div>
        </div>

        <div className="detail-tags">
          <span className="country-flag">{countryLabel}</span>
          <span className="freq-tag">{FREQ_LABELS[indicator.frequency] || indicator.frequency}</span>
          <span className={`source-tag ${indicator.source}`}>
            {SOURCE_LABELS[indicator.source] || indicator.source}
          </span>
          <span className="meta">{categoryLabel}</span>
        </div>

        <div className="detail-kpi-row">
          <p className="detail-value">{indicator.last_value ?? "—"}</p>
          <DeltaBadge direction={indicator.delta_direction} value={indicator.last_change} />
          <span className="detail-updated">Обновлено {formatDate(indicator.updated_at)}</span>
        </div>
        {message ? <p className="meta" style={{ marginTop: 12 }}>{message}</p> : null}
      </div>

      <div className="detail-layout">
        <div>
          <section className="chart-card">
            <div className="period-bar">
              {PERIODS.map((key) => (
                <button
                  key={key}
                  type="button"
                  className={`period-btn ${period === key ? "active" : ""}`}
                  onClick={() => setPeriod(key)}
                >
                  {key === "MAX" ? "Макс." : key}
                </button>
              ))}
            </div>
            {seriesLoading ? (
              <div className="empty-chart">Загрузка графика…</div>
            ) : (
              <IndicatorChart points={series?.points || []} unit={series?.unit || indicator.unit} name={indicator.name_ru} />
            )}
            {stats ? (
              <div className="stats-row">
                <div className="stat-box">
                  <p className="stat-label">Мин.</p>
                  <p className="stat-value">{formatPointValue(stats.min, indicator.unit)}</p>
                </div>
                <div className="stat-box">
                  <p className="stat-label">Макс.</p>
                  <p className="stat-value">{formatPointValue(stats.max, indicator.unit)}</p>
                </div>
                <div className="stat-box">
                  <p className="stat-label">Среднее</p>
                  <p className="stat-value">{formatPointValue(stats.avg, indicator.unit)}</p>
                </div>
                <div className="stat-box">
                  <p className="stat-label">Изменение</p>
                  <p className="stat-value">{formatPointValue(stats.change, indicator.unit)}</p>
                </div>
              </div>
            ) : null}
          </section>

          <details className="history-card">
            <summary>Последние значения</summary>
            {historyPoints.length === 0 ? (
              <p className="meta" style={{ padding: "0 18px 14px" }}>
                Нет данных за выбранный период
              </p>
            ) : (
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Дата</th>
                    <th className="num">Значение</th>
                  </tr>
                </thead>
                <tbody>
                  {historyPoints.map((point) => (
                    <tr key={point.date}>
                      <td>{formatDate(point.date)}</td>
                      <td className="num">{formatPointValue(point.value, indicator.unit)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </details>
        </div>

        <aside className="meta-card">
          <h2>О показателе</h2>
          <div className="meta-row">
            <span className="meta-key">Источник</span>
            <span className="meta-val">{SOURCE_LABELS[indicator.source] || indicator.source}</span>
          </div>
          <div className="meta-row">
            <span className="meta-key">Единица</span>
            <span className="meta-val">{indicator.unit || "—"}</span>
          </div>
          <div className="meta-row">
            <span className="meta-key">Частота</span>
            <span className="meta-val">{FREQ_LABELS[indicator.frequency] || indicator.frequency}</span>
          </div>
          <div className="meta-row">
            <span className="meta-key">Страна</span>
            <span className="meta-val">{countryLabel}</span>
          </div>
          <div className="meta-row">
            <span className="meta-key">external_id</span>
            <span className="meta-val">{indicator.external_id || "—"}</span>
          </div>
          <p className="source-note">
            Источник: {SOURCE_LABELS[indicator.source] || indicator.source} · Обновлено:{" "}
            {formatDate(indicator.updated_at)}
          </p>
        </aside>
      </div>
    </div>
  );
}
