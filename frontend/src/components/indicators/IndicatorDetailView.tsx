"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { MetaTags } from "@/components/ui/MetaTags";
import { IndicatorChart } from "./IndicatorChart";
import { MAX_COMPARE_SERIES } from "@/lib/compare";
import {
  COMPARE_KEY,
  FAVORITES_KEY,
  FREQ_LABELS,
  SOURCE_LABELS,
  fetchFacetLabels,
  fetchIndicator,
  fetchIndicatorEvents,
  fetchIndicatorRelated,
  fetchIndicatorSeries,
  fetchIndicatorStats,
  compareActionLabel,
  loadIds,
  saveIds,
  toggleId,
  type FacetLabels,
  type IndicatorDetail,
  type IndicatorEventItem,
  type IndicatorRelatedItem,
  type IndicatorSeriesResponse,
  type IndicatorStatsResponse,
} from "@/lib/indicators";
import {
  eventDates,
  exportSeriesCsv,
  formatStatValue,
  heroChipLabel,
  normalizeSeries,
  normalizeValue,
  tableRowsWithDelta,
  type ChartNormalizeMode,
} from "@/lib/indicatorChart";
import { buildIndicatorDetailExplanation } from "@/lib/indicatorPreview";

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
  const [stats, setStats] = useState<IndicatorStatsResponse | null>(null);
  const [related, setRelated] = useState<IndicatorRelatedItem[]>([]);
  const [events, setEvents] = useState<IndicatorEventItem[]>([]);
  const [labels, setLabels] = useState<FacetLabels | null>(null);
  const [period, setPeriod] = useState<PeriodKey>("5Y");
  const [normalize, setNormalize] = useState<ChartNormalizeMode>("absolute");
  const [loading, setLoading] = useState(true);
  const [seriesLoading, setSeriesLoading] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const [favoriteIds, setFavoriteIds] = useState<string[]>([]);
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const [resetToken, setResetToken] = useState(0);

  useEffect(() => {
    setFavoriteIds(loadIds(FAVORITES_KEY));
    setCompareIds(loadIds(COMPARE_KEY));
    fetchFacetLabels().then(setLabels).catch(() => undefined);
  }, []);

  useEffect(() => {
    setLoading(true);
    setNotFound(false);
    Promise.all([fetchIndicator(id), fetchIndicatorRelated(id), fetchIndicatorEvents(id)])
      .then(([row, rel, ev]) => {
        if (!row) {
          setNotFound(true);
          setIndicator(null);
          return;
        }
        setIndicator(row);
        setRelated(rel);
        setEvents(ev);
      })
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }, [id]);

  const loadSeries = useCallback(async () => {
    setSeriesLoading(true);
    try {
      const range = periodRange(period);
      const [seriesData, statsData] = await Promise.all([
        fetchIndicatorSeries(id, range),
        fetchIndicatorStats(id, range),
      ]);
      setSeries(seriesData);
      setStats(statsData);
    } catch {
      setSeries(null);
      setStats(null);
    } finally {
      setSeriesLoading(false);
    }
  }, [id, period]);

  useEffect(() => {
    if (!indicator) return;
    void loadSeries();
  }, [indicator, loadSeries]);

  const chartPoints = useMemo(
    () => normalizeSeries(series?.points || [], normalize),
    [series, normalize],
  );
  const tableRows = useMemo(() => tableRowsWithDelta(series?.points || []), [series]);
  const heroChips = useMemo(
    () => heroChipLabel(stats, indicator?.frequency || "monthly"),
    [stats, indicator?.frequency],
  );
  const chartEvents = useMemo(() => eventDates(events), [events]);
  const currentValue = series?.points.length ? series.points[series.points.length - 1].value : null;

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
    if (current.length >= MAX_COMPARE_SERIES) {
      setMessage(`В сравнении не более ${MAX_COMPARE_SERIES} показателей`);
      return;
    }
    saveIds(COMPARE_KEY, [...current, indicator.id]);
    setCompareIds([...current, indicator.id]);
    setMessage("Добавлено в сравнение");
  };

  const compareLabel = compareActionLabel(compareIds);

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
  const sourceLabel = SOURCE_LABELS[indicator.source] || indicator.source;
  const explanation = buildIndicatorDetailExplanation(indicator, {
    categoryLabel,
    countryLabel,
    sourceLabel,
  });
  const unit = series?.unit || indicator.unit;
  const chartNormalized = normalize !== "absolute";
  const rawPoints = series?.points || [];
  const normStat = (value: number | null | undefined) =>
    value == null ? null : normalizeValue(value, rawPoints, normalize);
  const displayStat = (value: number) =>
    formatStatValue(normalizeValue(value, rawPoints, normalize), unit, normalize);

  return (
    <div className="content indicator-detail-page">
      <Link href="/app/indicators" className="btn ghost detail-back">
        ← К каталогу
      </Link>

      <div className="detail-hero">
        <div className="detail-head-row">
          <div>
            <h1 style={{ margin: 0 }}>{indicator.name_ru}</h1>
            <p className="meta">
              {stats?.last_observed_at
                ? `Последняя точка: ${formatDate(stats.last_observed_at)}`
                : "Последняя точка: —"}
              {" · "}
              {SOURCE_LABELS[indicator.source] || indicator.source}
            </p>
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
              <i className="ti ti-plus" /> {compareLabel}
            </button>
            <button
              type="button"
              className="btn"
              onClick={() => series && exportSeriesCsv(indicator.name_ru, series.points)}
              disabled={!series?.points.length}
            >
              CSV
            </button>
            <Link href="/app/compare" className="btn">
              Сравнение
            </Link>
          </div>
        </div>

        <div className="detail-tags">
          <MetaTags country={indicator.country} source={indicator.source} countryLabel={countryLabel} />
          <span className="freq-tag">{FREQ_LABELS[indicator.frequency] || indicator.frequency}</span>
          <span className="meta">{categoryLabel}</span>
        </div>

        <div className="detail-kpi-row">
          <p className="detail-value">{indicator.last_value ?? "—"}</p>
          <DeltaBadge direction={indicator.delta_direction} value={indicator.last_change} />
          <span className="detail-updated">ETL: {formatDate(indicator.updated_at)}</span>
        </div>

        {heroChips.length > 0 ? (
          <div className="hero-chips">
            {heroChips.map((chip) => (
              <span key={chip} className="hero-chip">
                {chip}
              </span>
            ))}
          </div>
        ) : null}
        {message ? <p className="meta" style={{ marginTop: 12 }}>{message}</p> : null}
      </div>

      <div className="detail-layout">
        <div>
          <section className="chart-card">
            <div className="chart-toolbar">
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
              <select
                className="select-sort"
                value={normalize}
                onChange={(e) => setNormalize(e.target.value as ChartNormalizeMode)}
              >
                <option value="absolute">Абсолютные</option>
                <option value="index">Индекс (100)</option>
                <option value="change">Изменение %</option>
              </select>
            </div>
            {seriesLoading ? (
              <div className="empty-chart">Загрузка графика…</div>
            ) : (
              <IndicatorChart
                points={chartPoints}
                unit={unit}
                name={indicator.name_ru}
                avg={normStat(stats?.avg)}
                min={normStat(stats?.min)}
                max={normStat(stats?.max)}
                current={normStat(currentValue)}
                events={chartEvents}
                normalized={chartNormalized}
                onHoverIndex={setHoverIndex}
                resetToken={resetToken}
                onResetZoom={() => setResetToken((v) => v + 1)}
              />
            )}
            {stats ? (
              <div className="stats-grid">
                <div className="stat-box">
                  <p className="stat-label">Мин.</p>
                  <p className="stat-value">{displayStat(stats.min)}</p>
                </div>
                <div className="stat-box">
                  <p className="stat-label">Макс.</p>
                  <p className="stat-value">{displayStat(stats.max)}</p>
                </div>
                <div className="stat-box">
                  <p className="stat-label">Среднее</p>
                  <p className="stat-value">{displayStat(stats.avg)}</p>
                </div>
                <div className="stat-box">
                  <p className="stat-label">Медиана</p>
                  <p className="stat-value">{displayStat(stats.median)}</p>
                </div>
                <div className="stat-box">
                  <p className="stat-label">Изменение</p>
                  <p className="stat-value">{formatStatValue(stats.change, unit, "absolute")}</p>
                </div>
                <div className="stat-box">
                  <p className="stat-label">CAGR</p>
                  <p className="stat-value">
                    {stats.cagr != null ? `${stats.cagr.toFixed(2).replace(".", ",")}%` : "—"}
                  </p>
                </div>
                <div className="stat-box">
                  <p className="stat-label">Волатильность</p>
                  <p className="stat-value">{displayStat(stats.volatility)}</p>
                </div>
                <div className="stat-box">
                  <p className="stat-label">Выше текущего</p>
                  <p className="stat-value">{stats.pct_above_current}%</p>
                </div>
              </div>
            ) : null}
          </section>

          <details className="history-card" open>
            <summary>Последние значения</summary>
            {tableRows.length === 0 ? (
              <p className="meta" style={{ padding: "0 18px 14px" }}>
                Нет данных за выбранный период
              </p>
            ) : (
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Дата</th>
                    <th className="num">Значение</th>
                    <th className="num">Δ к пред.</th>
                  </tr>
                </thead>
                <tbody>
                  {tableRows.map((row, idx) => {
                    const sourceIndex = series ? series.points.length - 1 - idx : -1;
                    const active = hoverIndex !== null && sourceIndex === hoverIndex;
                    return (
                      <tr key={row.date} className={active ? "active-row" : undefined}>
                        <td>{formatDate(row.date)}</td>
                        <td className="num">{formatStatValue(row.value, unit, "absolute")}</td>
                        <td className="num">
                          {row.delta == null ? "—" : formatStatValue(row.delta, unit, "absolute")}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </details>
        </div>

        <aside className="sidebar-stack">
          <div className="meta-card meta-card-primary">
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
            {stats ? (
              <>
                {stats.best ? (
                  <div className="meta-row">
                    <span className="meta-key">Лучший</span>
                    <span className="meta-val">
                      {formatDate(stats.best.date)} · {formatStatValue(stats.best.value, unit, "absolute")}
                    </span>
                  </div>
                ) : null}
                {stats.worst ? (
                  <div className="meta-row">
                    <span className="meta-key">Худший</span>
                    <span className="meta-val">
                      {formatDate(stats.worst.date)} · {formatStatValue(stats.worst.value, unit, "absolute")}
                    </span>
                  </div>
                ) : null}
              </>
            ) : null}
            <p className="source-note">
              Источник: {SOURCE_LABELS[indicator.source] || indicator.source} · Обновлено:{" "}
              {formatDate(indicator.updated_at)}
            </p>
          </div>

          <div className="meta-card explain-card">
            <h2>Что означает показатель</h2>
            <p className="explain-lead">{explanation.lead}</p>
            {explanation.paragraphs.map((paragraph) => (
              <p key={paragraph} className="explain-text">
                {paragraph}
              </p>
            ))}
          </div>

          {related.length > 0 ? (
            <div className="meta-card">
              <h2>Похожие показатели</h2>
              <div className="related-list">
                {related.map((item) => (
                  <Link key={item.id} href={`/app/indicators/${item.id}`} className="related-item">
                    <span>{item.name_ru}</span>
                    <span className="meta">{item.last_value || "—"}</span>
                  </Link>
                ))}
              </div>
            </div>
          ) : null}

          {events.length > 0 ? (
            <div className="meta-card">
              <h2>События календаря</h2>
              <div className="events-list">
                {events.map((event) => (
                  <div key={event.id} className="event-item">
                    <p className="event-title">{event.title_ru}</p>
                    <p className="meta">
                      {formatDate(event.scheduled_at_msk)} · {event.importance}
                      {event.actual ? ` · факт: ${event.actual}` : ""}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </aside>
      </div>
    </div>
  );
}
