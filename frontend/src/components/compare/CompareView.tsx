"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { MetaTags, SourceTag } from "@/components/ui/MetaTags";
import { CompareChart } from "./CompareChart";
import { COMPARE_KEY, loadIds, saveIds } from "@/lib/indicators";
import {
  exportCompareCsv,
  fetchComparePresets,
  fetchCompareSeries,
  MAX_COMPARE_SERIES,
  periodToFrom,
  SERIES_COLORS,
  type ComparePreset,
  type CompareSeriesResponse,
} from "@/lib/compare";

const DELTA_ICON = { up: "ti-arrow-up-right", down: "ti-arrow-down-right", flat: "ti-minus" } as const;
const PERIODS = ["1M", "3M", "6M", "1Y", "3Y", "5Y", "MAX"] as const;
const NORMALIZE_LABELS = { absolute: "Абсолютные", index: "Индекс (100)", change: "Изменение %" } as const;

export function CompareView() {
  const [presets, setPresets] = useState<ComparePreset[]>([]);
  const [activePreset, setActivePreset] = useState("rates");
  const [indicatorIds, setIndicatorIds] = useState<string[]>([]);
  const [period, setPeriod] = useState("1Y");
  const [normalize, setNormalize] = useState<"absolute" | "index" | "change">("absolute");
  const [hiddenIds, setHiddenIds] = useState<Set<string>>(new Set());
  const [data, setData] = useState<CompareSeriesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [resetToken, setResetToken] = useState(0);

  const loadSeries = useCallback(
    async (ids: string[]) => {
      if (!ids.length) {
        setData(null);
        setLoading(false);
        return;
      }
      setLoading(true);
      setLoadError(null);
      try {
        const res = await fetchCompareSeries({
          indicator_ids: ids,
          date_from: periodToFrom(period),
          date_to: new Date().toISOString().slice(0, 10),
          normalize,
        });
        setData(res);
        setHiddenIds(new Set());
      } catch {
        setData(null);
        setLoadError("Не удалось загрузить данные сравнения. Проверьте backend и нажмите «Повторить».");
      } finally {
        setLoading(false);
      }
    },
    [normalize, period],
  );

  useEffect(() => {
    fetchComparePresets()
      .then((p) => {
        setPresets(p);
        const stored = loadIds(COMPARE_KEY);
        if (stored.length) {
          setIndicatorIds(stored.slice(0, MAX_COMPARE_SERIES));
        } else {
          const rates = p.find((x) => x.key === "rates") || p[0];
          if (rates) setIndicatorIds(rates.indicator_ids);
        }
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    if (indicatorIds.length) void loadSeries(indicatorIds);
    else setLoading(false);
  }, [indicatorIds, loadSeries]);

  const applyPreset = (key: string) => {
    const preset = presets.find((p) => p.key === key);
    if (!preset) return;
    setActivePreset(key);
    setIndicatorIds(preset.indicator_ids);
    saveIds(COMPARE_KEY, preset.indicator_ids);
  };

  const removeSeries = (id: string) => {
    const next = indicatorIds.filter((x) => x !== id);
    setIndicatorIds(next);
    saveIds(COMPARE_KEY, next);
    setHiddenIds((prev) => {
      const copy = new Set(prev);
      copy.delete(id);
      return copy;
    });
  };

  const toggleVisibility = (id: string) => {
    setHiddenIds((prev) => {
      const copy = new Set(prev);
      if (copy.has(id)) copy.delete(id);
      else copy.add(id);
      return copy;
    });
  };

  const compareFull = indicatorIds.length >= MAX_COMPARE_SERIES;

  const summaryText = useMemo(() => {
    const periodLabel = period === "MAX" ? "макс." : period;
    return `${indicatorIds.length} серий · период: ${periodLabel} · режим: ${NORMALIZE_LABELS[normalize]}`;
  }, [indicatorIds.length, normalize, period]);

  return (
    <div className="content compare-page">
      <div className="page-head">
        <div>
          <h1>Сравнение</h1>
          <p className="meta">До {MAX_COMPARE_SERIES} серий · presets · absolute / index(100) / change%</p>
        </div>
        <div className="page-head-actions">
          <button
            type="button"
            className="btn"
            disabled={!data?.series.length}
            onClick={() => data && exportCompareCsv(data)}
          >
            CSV
          </button>
          <Link href="/app/indicators" className="btn primary">
            К каталогу
          </Link>
        </div>
      </div>

      <div className="preset-bar">
        {presets.map((preset) => (
          <button
            key={preset.key}
            type="button"
            className={`preset-chip ${activePreset === preset.key ? "active" : ""}`}
            onClick={() => applyPreset(preset.key)}
          >
            {preset.label}
          </button>
        ))}
      </div>

      <p className="compare-summary">{summaryText}</p>

      <div className="compare-layout">
        <div className="compare-main">
          {data?.unit_warning && (
            <div className="warning-banner">
              <div className="wb-left">
                <i className="ti ti-alert-triangle" />
                На одной оси смешаны разные единицы. Рекомендуем режим «Индекс (100)».
              </div>
              <button type="button" className="btn warning-action" onClick={() => setNormalize("index")}>
                Переключить
              </button>
            </div>
          )}

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
                onChange={(e) => setNormalize(e.target.value as typeof normalize)}
              >
                <option value="absolute">Абсолютные</option>
                <option value="index">Индекс (100)</option>
                <option value="change">Изменение %</option>
              </select>
            </div>

            {loadError ? (
              <div className="empty-chart">
                <p>{loadError}</p>
                <button type="button" className="btn primary" onClick={() => void loadSeries(indicatorIds)}>
                  Повторить
                </button>
              </div>
            ) : loading ? (
              <p className="meta">Загрузка графика…</p>
            ) : (
              <CompareChart
                data={data}
                hiddenIds={hiddenIds}
                normalize={normalize}
                resetToken={resetToken}
                onResetZoom={() => setResetToken((v) => v + 1)}
              />
            )}
          </section>

          {data && data.series.length > 0 && (
            <section className="table-card">
              <p className="table-section-title">Сводка за период</p>
              <div className="table-scroll">
                <table className="data-table compare-table">
                  <thead>
                    <tr>
                      <th>Показатель</th>
                      <th>Страна</th>
                      <th className="num">Текущее</th>
                      <th className="num">Min</th>
                      <th className="num">Max</th>
                      <th className="num">Avg</th>
                      <th className="num">Δ периода</th>
                      <th>Источник</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.series.map((s, idx) => (
                      <tr key={s.indicator_id} className={hiddenIds.has(s.indicator_id) ? "muted-row" : undefined}>
                        <td>
                          <div className="series-cell">
                            <span
                              className="series-cell-dot"
                              style={{ background: SERIES_COLORS[idx % SERIES_COLORS.length] }}
                            />
                            {s.name_ru}
                          </div>
                        </td>
                        <td>
                          <span className="country-flag">{s.country.toUpperCase()}</span>
                        </td>
                        <td className="num">{s.last_value ?? "—"}</td>
                        <td className="num">{s.stats?.min ?? "—"}</td>
                        <td className="num">{s.stats?.max ?? "—"}</td>
                        <td className="num">{s.stats?.avg ?? "—"}</td>
                        <td className="num">
                          <span className={`delta-badge ${s.stats?.change_direction || "flat"}`}>
                            <i
                              className={`ti ${DELTA_ICON[(s.stats?.change_direction as keyof typeof DELTA_ICON) || "flat"] || "ti-minus"}`}
                            />
                            {s.stats?.change ?? "—"}
                          </span>
                        </td>
                        <td className="source-cell">
                          <SourceTag source={s.source} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </div>

        <aside className="series-panel card">
          <div className="series-panel-head card-pad">
            <p className="panel-title">
              Серии ({indicatorIds.length}/{MAX_COMPARE_SERIES})
            </p>
          </div>
          <div className="series-list">
            {data?.series.map((s, idx) => {
              const hidden = hiddenIds.has(s.indicator_id);
              const color = SERIES_COLORS[idx % SERIES_COLORS.length];
              return (
                <div
                  key={s.indicator_id}
                  className={`series-row ${hidden ? "hidden-series" : ""}`}
                  style={{ ["--series-color" as string]: color }}
                >
                  <span className="series-dot" style={{ background: color }} />
                  <div className="series-body">
                    <div className="series-title-row">
                      <span className="series-name" title={s.name_ru}>
                        {s.name_ru}
                      </span>
                      <span className="series-value">{s.last_value ?? "—"}</span>
                    </div>
                    <MetaTags country={s.country} source={s.source} compact />
                  </div>
                  <div className="series-actions">
                    <button
                      type="button"
                      className={`series-action ${hidden ? "is-off" : ""}`}
                      onClick={() => toggleVisibility(s.indicator_id)}
                      title={hidden ? "Показать на графике" : "Скрыть на графике"}
                      aria-label={hidden ? "Показать на графике" : "Скрыть на графике"}
                    >
                      <i className={`ti ${hidden ? "ti-eye-off" : "ti-eye"}`} />
                      <span>{hidden ? "Показать" : "Скрыть"}</span>
                    </button>
                    <button
                      type="button"
                      className="series-action danger"
                      onClick={() => removeSeries(s.indicator_id)}
                      title="Удалить из сравнения"
                      aria-label="Удалить из сравнения"
                    >
                      <i className="ti ti-trash" />
                      <span>Удалить</span>
                    </button>
                  </div>
                </div>
              );
            })}
            {!indicatorIds.length && (
              <p className="meta series-empty">Добавьте показатели из каталога или выберите preset.</p>
            )}
          </div>
          <div className="series-footer card-pad">
            <p className="series-hint">
              <i className="ti ti-info-circle" />
              На графике потяните мышью для zoom. Скрытые серии остаются в таблице.
            </p>
            {compareFull ? (
              <span className="catalog-link is-disabled" aria-disabled="true">
                <i className="ti ti-plus" /> Добавить из каталога
              </span>
            ) : (
              <Link href="/app/indicators" className="catalog-link">
                <i className="ti ti-plus" /> Добавить из каталога
              </Link>
            )}
            {compareFull ? (
              <p className="catalog-limit-note">
                Достигнут лимит — не более {MAX_COMPARE_SERIES} серий. Удалите серию, чтобы добавить новую.
              </p>
            ) : null}
          </div>
        </aside>
      </div>
    </div>
  );
}
