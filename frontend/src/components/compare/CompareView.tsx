"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { MetaTags } from "@/components/ui/MetaTags";
import { CompareChart } from "./CompareChart";
import { COMPARE_KEY, loadIds, saveIds } from "@/lib/indicators";
import {
  SERIES_COLORS,
  exportCompareCsv,
  fetchComparePresets,
  fetchCompareSeries,
  periodToFrom,
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

  const loadSeries = useCallback(
    async (ids: string[]) => {
      if (!ids.length) {
        setData(null);
        setLoading(false);
        return;
      }
      setLoading(true);
      try {
        const res = await fetchCompareSeries({
          indicator_ids: ids,
          date_from: periodToFrom(period),
          date_to: new Date().toISOString().slice(0, 10),
          normalize,
        });
        setData(res);
        setHiddenIds(new Set());
      } finally {
        setLoading(false);
      }
    },
    [normalize, period],
  );

  useEffect(() => {
    fetchComparePresets().then((p) => {
      setPresets(p);
      const stored = loadIds(COMPARE_KEY);
      if (stored.length) {
        setIndicatorIds(stored.slice(0, 6));
      } else {
        const rates = p.find((x) => x.key === "rates") || p[0];
        if (rates) setIndicatorIds(rates.indicator_ids);
      }
    });
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

  const summaryText = useMemo(() => {
    const periodLabel = period === "MAX" ? "макс." : period;
    return `${indicatorIds.length} серий · период: ${periodLabel} · режим: ${NORMALIZE_LABELS[normalize]}`;
  }, [indicatorIds.length, normalize, period]);

  return (
    <div className="content compare-page">
      <div className="page-head">
        <div>
          <h1>Сравнение</h1>
          <p className="meta">До 6 серий · presets · absolute / index(100) / change%</p>
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
        <aside className="series-panel card">
          <div className="series-panel-head card-pad">
            <p className="panel-title">Серии ({indicatorIds.length}/6)</p>
          </div>
          <div className="series-list">
            {data?.series.map((s, idx) => {
              const hidden = hiddenIds.has(s.indicator_id);
              return (
                <div key={s.indicator_id} className={`series-row ${hidden ? "hidden-series" : ""}`}>
                  <span
                    className="series-dot"
                    style={{ background: SERIES_COLORS[idx % SERIES_COLORS.length] }}
                  />
                  <div className="series-info">
                    <span className="series-name" title={s.name_ru}>
                      {s.name_ru}
                    </span>
                    <MetaTags country={s.country} source={s.source} />
                  </div>
                  <span className="series-value">{s.last_value ?? "—"}</span>
                  <div className="series-icons">
                    <button
                      type="button"
                      className={`series-icon-btn ${hidden ? "off" : ""}`}
                      onClick={() => toggleVisibility(s.indicator_id)}
                      title={hidden ? "Показать на графике" : "Скрыть на графике"}
                      aria-label={hidden ? "Показать на графике" : "Скрыть на графике"}
                    >
                      <i className={`ti ${hidden ? "ti-eye-off" : "ti-eye"}`} />
                    </button>
                    <button
                      type="button"
                      className="series-icon-btn danger"
                      onClick={() => removeSeries(s.indicator_id)}
                      title="Удалить из сравнения"
                      aria-label="Удалить из сравнения"
                    >
                      <i className="ti ti-x" />
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
              Перетаскивание на графике — zoom по оси X. Скрытые серии остаются в таблице.
            </p>
            <Link href="/app/indicators" className="catalog-link">
              <i className="ti ti-plus" /> Добавить из каталога
            </Link>
          </div>
        </aside>

        <div className="chart-panel">
          <div className="chart-toolbar card card-pad">
            <div className="toolbar-group">
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
          </div>

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

          <div className="card card-pad chart-card">
            {loading ? (
              <p className="meta">Загрузка графика…</p>
            ) : (
              <CompareChart data={data} hiddenIds={hiddenIds} normalize={normalize} />
            )}
          </div>

          {data && data.series.length > 0 && (
            <>
              <div className="custom-legend card card-pad">
                {data.series.map((s, idx) => {
                  const hidden = hiddenIds.has(s.indicator_id);
                  return (
                    <button
                      key={s.indicator_id}
                      type="button"
                      className={`legend-item ${hidden ? "muted" : ""}`}
                      onClick={() => toggleVisibility(s.indicator_id)}
                    >
                      <span
                        className="legend-swatch"
                        style={{ background: SERIES_COLORS[idx % SERIES_COLORS.length] }}
                      />
                      {s.name_ru} ({s.country.toUpperCase()})
                    </button>
                  );
                })}
              </div>

              <div className="table-card">
                <p className="table-section-title">Сводка за период</p>
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
                        <td className="num">{s.stats.min}</td>
                        <td className="num">{s.stats.max}</td>
                        <td className="num">{s.stats.avg}</td>
                        <td className="num">
                          <span className={`delta-badge ${s.stats.change_direction}`}>
                            <i
                              className={`ti ${DELTA_ICON[s.stats.change_direction as keyof typeof DELTA_ICON] || "ti-minus"}`}
                            />
                            {s.stats.change}
                          </span>
                        </td>
                        <td>
                          <MetaTags country={s.country} source={s.source} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
