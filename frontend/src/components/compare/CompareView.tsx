"use client";

import { useCallback, useEffect, useState } from "react";
import { CompareChart } from "./CompareChart";
import { COMPARE_KEY, SOURCE_LABELS, loadIds, saveIds } from "@/lib/indicators";
import {
  SERIES_COLORS,
  fetchComparePresets,
  fetchCompareSeries,
  periodToFrom,
  type ComparePreset,
  type CompareSeriesResponse,
} from "@/lib/compare";

const DELTA_ICON = { up: "ti-arrow-up-right", down: "ti-arrow-down-right", flat: "ti-minus" } as const;

export function CompareView() {
  const [presets, setPresets] = useState<ComparePreset[]>([]);
  const [activePreset, setActivePreset] = useState("rates");
  const [indicatorIds, setIndicatorIds] = useState<string[]>([]);
  const [period, setPeriod] = useState("1Y");
  const [normalize, setNormalize] = useState<"absolute" | "index" | "change">("absolute");
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
          date_to: "2026-06-01",
          normalize,
        });
        setData(res);
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
  };

  return (
    <div className="content compare-page">
      <div className="page-head">
        <div>
          <h1>Сравнение</h1>
          <p className="meta">До 6 серий · presets · absolute / index(100) / change%</p>
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

      <div className="compare-layout">
        <aside className="series-panel card card-pad">
          <p className="panel-title">Серии ({indicatorIds.length}/6)</p>
          {data?.series.map((s, idx) => (
            <div key={s.indicator_id} className="series-row">
              <span className="series-dot" style={{ background: SERIES_COLORS[idx % SERIES_COLORS.length] }} />
              <div className="series-info">
                <span className="series-name">{s.name_ru}</span>
                <div className="series-meta-row">
                  <span className="country-flag">{s.country.toUpperCase()}</span>
                  <span className={`source-tag ${s.source}`}>{SOURCE_LABELS[s.source] || s.source}</span>
                </div>
              </div>
              <span className="series-value">{s.last_value ?? "—"}</span>
              <button type="button" className="row-icon-btn" onClick={() => removeSeries(s.indicator_id)} aria-label="Удалить">
                <i className="ti ti-x" />
              </button>
            </div>
          ))}
          {!indicatorIds.length && <p className="meta">Добавьте показатели из каталога или выберите preset.</p>}
        </aside>

        <div className="chart-panel">
          <div className="chart-toolbar card card-pad">
            <select value={period} onChange={(e) => setPeriod(e.target.value)}>
              <option value="1M">1M</option>
              <option value="3M">3M</option>
              <option value="6M">6M</option>
              <option value="1Y">1Y</option>
              <option value="3Y">3Y</option>
              <option value="5Y">5Y</option>
              <option value="MAX">MAX</option>
            </select>
            <select value={normalize} onChange={(e) => setNormalize(e.target.value as typeof normalize)}>
              <option value="absolute">Абсолютные</option>
              <option value="index">Индекс (100)</option>
              <option value="change">Изменение %</option>
            </select>
            <span className="meta">{data?.axis_note}</span>
          </div>

          {data?.unit_warning && (
            <div className="warning-banner">
              <i className="ti ti-alert-triangle" />
              На одной оси смешаны разные единицы измерения. Рекомендуем режим «Индекс (100)».
            </div>
          )}

          <div className="card card-pad chart-card">
            {loading ? <p className="meta">Загрузка графика…</p> : <CompareChart data={data} />}
          </div>

          {data && data.series.length > 0 && (
            <div className="table-card">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Показатель</th>
                    <th className="num">Min</th>
                    <th className="num">Max</th>
                    <th className="num">Avg</th>
                    <th className="num">Δ периода</th>
                  </tr>
                </thead>
                <tbody>
                  {data.series.map((s) => (
                    <tr key={s.indicator_id}>
                      <td>{s.name_ru}</td>
                      <td className="num">{s.stats.min}</td>
                      <td className="num">{s.stats.max}</td>
                      <td className="num">{s.stats.avg}</td>
                      <td className="num">
                        <span className={`delta-badge ${s.stats.change_direction}`}>
                          <i className={`ti ${DELTA_ICON[s.stats.change_direction as keyof typeof DELTA_ICON] || "ti-minus"}`} />
                          {s.stats.change}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
