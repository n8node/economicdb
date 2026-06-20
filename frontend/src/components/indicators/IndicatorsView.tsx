"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { MetaTags } from "@/components/ui/MetaTags";
import { MiniSparkline } from "./MiniSparkline";
import { IndicatorRowPreview, isRowPreviewBlockedTarget } from "./IndicatorRowPreview";
import { MAX_COMPARE_SERIES } from "@/lib/compare";
import {
  COMPARE_KEY,
  FAVORITES_KEY,
  FREQ_LABELS,
  SOURCE_LABELS,
  fetchFacetLabels,
  fetchIndicatorFacets,
  fetchIndicators,
  loadIds,
  saveIds,
  compareActionLabel,
  toggleId,
  type FacetLabels,
  type IndicatorFacets,
  type IndicatorFilters,
  type IndicatorListItem,
} from "@/lib/indicators";

const DELTA_ICON = { up: "ti-arrow-up-right", down: "ti-arrow-down-right", flat: "ti-minus" } as const;

type DraftFilters = {
  country: string[];
  category: string[];
  frequency: string[];
  source: string[];
  updated_within?: number;
};

type FilterGroupKey = "country" | "category" | "frequency" | "source";

type FilterGroupConfig = {
  title: string;
  group: FilterGroupKey;
  options: Record<string, number>;
  labelMap?: Record<string, string>;
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("ru-RU");
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

function SourceTag({ source }: { source: string }) {
  return <span className={`source-tag ${source}`}>{SOURCE_LABELS[source] || source}</span>;
}

export function IndicatorsView() {
  const [facets, setFacets] = useState<IndicatorFacets | null>(null);
  const [labels, setLabels] = useState<FacetLabels | null>(null);
  const [items, setItems] = useState<IndicatorListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [view, setView] = useState<"table" | "cards">("table");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<IndicatorFilters["sort"]>("name");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [draft, setDraft] = useState<DraftFilters>({ country: [], category: [], frequency: [], source: [] });
  const [applied, setApplied] = useState<DraftFilters>({ country: [], category: [], frequency: [], source: [] });
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [favoriteIds, setFavoriteIds] = useState<string[]>([]);
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [rowPreview, setRowPreview] = useState<{ item: IndicatorListItem; x: number; y: number } | null>(null);
  const [rowPreviewVisible, setRowPreviewVisible] = useState(false);
  const rowPreviewHideTimer = useRef<number | null>(null);

  useEffect(() => {
    setFavoriteIds(loadIds(FAVORITES_KEY));
    setCompareIds(loadIds(COMPARE_KEY));
    Promise.all([fetchIndicatorFacets(), fetchFacetLabels()])
      .then(([f, l]) => {
        setFacets(f);
        setLabels(l);
      })
      .catch(() => undefined);
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const res = await fetchIndicators({
        q: search || undefined,
        country: applied.country.length ? applied.country : undefined,
        category: applied.category.length ? applied.category : undefined,
        frequency: applied.frequency.length ? applied.frequency : undefined,
        source: applied.source.length ? applied.source : undefined,
        updated_within: applied.updated_within,
        sort,
        page,
        page_size: pageSize,
      });
      let list = res.items ?? [];
      if (favoritesOnly) {
        const fav = loadIds(FAVORITES_KEY);
        list = list.filter((i) => fav.includes(i.id));
      }
      setItems(list);
      setTotal(favoritesOnly ? list.length : (res.total ?? list.length));
    } catch {
      setItems([]);
      setTotal(0);
      setLoadError("Не удалось загрузить каталог. Проверьте, что backend доступен, и нажмите «Повторить».");
    } finally {
      setLoading(false);
    }
  }, [applied, favoritesOnly, page, pageSize, search, sort]);

  useEffect(() => {
    void load();
  }, [load]);

  const chips = useMemo(() => {
    const result: { key: string; value: string; label: string; group: keyof DraftFilters }[] = [];
    applied.country.forEach((c) =>
      result.push({ key: `country-${c}`, value: c, label: labels?.countries[c] || c.toUpperCase(), group: "country" }),
    );
    applied.category.forEach((c) =>
      result.push({ key: `cat-${c}`, value: c, label: labels?.categories[c] || c, group: "category" }),
    );
    applied.frequency.forEach((f) =>
      result.push({ key: `freq-${f}`, value: f, label: FREQ_LABELS[f] || f, group: "frequency" }),
    );
    applied.source.forEach((s) =>
      result.push({ key: `src-${s}`, value: s, label: SOURCE_LABELS[s] || s, group: "source" }),
    );
    return result;
  }, [applied, labels]);

  const removeChip = (chip: { group: keyof DraftFilters; value: string }) => {
    const next = {
      ...applied,
      [chip.group]: (applied[chip.group] as string[]).filter((v) => v !== chip.value),
    };
    setApplied(next);
    setDraft(next);
    setPage(1);
  };

  const toggleDraft = (group: keyof DraftFilters, value: string) => {
    setDraft((prev) => {
      const list = prev[group] as string[];
      const next = list.includes(value) ? list.filter((x) => x !== value) : [...list, value];
      return { ...prev, [group]: next };
    });
  };

  const applyFilters = () => {
    setApplied({ ...draft });
    setPage(1);
  };

  const resetFilters = () => {
    const empty = { country: [], category: [], frequency: [], source: [] } as DraftFilters;
    setDraft(empty);
    setApplied(empty);
    setPage(1);
  };

  const toggleFavorite = (id: string) => {
    const next = toggleId(FAVORITES_KEY, id);
    setFavoriteIds(next);
  };

  const addToCompare = (id: string) => {
    const current = loadIds(COMPARE_KEY);
    if (current.includes(id) || current.length >= MAX_COMPARE_SERIES) return;
    const next = [...current, id];
    saveIds(COMPARE_KEY, next);
    setCompareIds(next);
  };

  const toggleSelect = (id: string) => {
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const toggleSelectAll = () => {
    setSelected(selected.length === items.length ? [] : items.map((i) => i.id));
  };

  const bulkCompare = () => {
    const current = loadIds(COMPARE_KEY);
    const merged = [...new Set([...current, ...selected])].slice(0, MAX_COMPARE_SERIES);
    saveIds(COMPARE_KEY, merged);
    setCompareIds(merged);
    window.location.href = "/app/compare";
  };

  const compareLabel = compareActionLabel(compareIds);

  const clearRowPreviewHideTimer = () => {
    if (rowPreviewHideTimer.current !== null) {
      window.clearTimeout(rowPreviewHideTimer.current);
      rowPreviewHideTimer.current = null;
    }
  };

  const hideRowPreview = () => {
    setRowPreviewVisible(false);
    clearRowPreviewHideTimer();
    rowPreviewHideTimer.current = window.setTimeout(() => {
      setRowPreview(null);
      rowPreviewHideTimer.current = null;
    }, 180);
  };

  const showRowPreview = (item: IndicatorListItem, x: number, y: number) => {
    clearRowPreviewHideTimer();
    setRowPreview({ item, x, y });
    setRowPreviewVisible(true);
  };

  const handleRowPointerMove = (item: IndicatorListItem, event: React.MouseEvent<HTMLTableRowElement>) => {
    if (isRowPreviewBlockedTarget(event.target)) {
      if (rowPreviewVisible) hideRowPreview();
      return;
    }
    showRowPreview(item, event.clientX, event.clientY);
  };

  useEffect(() => () => clearRowPreviewHideTimer(), []);

  const filterGroups = useMemo<FilterGroupConfig[]>(() => {
    if (!facets) return [];
    return [
      { title: "Регион", group: "country", options: facets.countries, labelMap: labels?.countries },
      { title: "Категория", group: "category", options: facets.categories, labelMap: labels?.categories },
      { title: "Частота", group: "frequency", options: facets.frequencies, labelMap: FREQ_LABELS },
      { title: "Источник", group: "source", options: facets.sources, labelMap: SOURCE_LABELS },
    ];
  }, [facets, labels]);

  const optionLabel = (group: FilterGroupConfig, key: string) =>
    group.labelMap?.[key] || key.toUpperCase();

  const groupSelectedCount = (group: FilterGroupKey) => (draft[group] as string[]).length;

  const dropdownSummary = (title: string, group: FilterGroupKey) => {
    const count = groupSelectedCount(group);
    return count > 0 ? `${title} · ${count}` : title;
  };

  const clearGroup = (group: FilterGroupKey) => {
    setDraft((prev) => ({ ...prev, [group]: [] }));
  };

  const renderFilterCheckboxRow = (
    group: FilterGroupKey,
    key: string,
    label: string,
    count: number,
  ) => {
    const checked = (draft[group] as string[]).includes(key);
    return (
      <label key={key} className={`filter-check-row ${checked ? "active" : ""}`}>
        <input type="checkbox" checked={checked} onChange={() => toggleDraft(group, key)} />
        <span className="filter-pill-box" aria-hidden="true">
          <i className="ti ti-check" />
        </span>
        <span className="filter-check-label">{label}</span>
        <span className="filter-pill-count">{count}</span>
      </label>
    );
  };

  return (
    <div className="content indicators-page">
      <div className="page-head">
        <div>
          <h1>Показатели</h1>
          <p className="meta">Каталог макроэкономических показателей</p>
        </div>
        <div className="view-toggle">
          <button type="button" className={view === "table" ? "active" : ""} onClick={() => setView("table")}>
            <i className="ti ti-table" /> Таблица
          </button>
          <button type="button" className={view === "cards" ? "active" : ""} onClick={() => setView("cards")}>
            <i className="ti ti-layout-grid" /> Карточки
          </button>
        </div>
      </div>

      {chips.length > 0 && (
        <div className="chips-row">
          {chips.map((chip) => (
            <span key={chip.key} className="chip">
              {chip.label}
              <button type="button" aria-label="Убрать фильтр" onClick={() => removeChip(chip)}>
                <i className="ti ti-x" />
              </button>
            </span>
          ))}
          <button type="button" className="chip-reset" onClick={resetFilters}>
            Сбросить все
          </button>
        </div>
      )}

      <section className="filters-bar">
        <div className="filters-bar-head">
          <div className="filters-bar-title">
            <i className="ti ti-adjustments-horizontal" aria-hidden="true" />
            <span>Фильтры</span>
          </div>
          <div className="filters-bar-actions">
            <span className="filters-bar-meta">
              Показано {items.length} из {total.toLocaleString("ru-RU")}
            </span>
            <button type="button" className="chip-reset" onClick={resetFilters}>
              Сбросить
            </button>
            <button type="button" className="btn primary" onClick={applyFilters}>
              Применить
            </button>
          </div>
        </div>
        {facets && (
          <div className="filters-dropdown-row">
            {filterGroups.map((group) => (
              <details key={group.group} className="filter-dropdown">
                <summary>
                  <span>{dropdownSummary(group.title, group.group)}</span>
                  <i className="ti ti-chevron-down" aria-hidden="true" />
                </summary>
                <div className="filter-dropdown-menu">
                  <div className="filter-dropdown-menu-head">
                    <span>{group.title}</span>
                    {groupSelectedCount(group.group) > 0 && (
                      <button type="button" className="chip-reset" onClick={() => clearGroup(group.group)}>
                        Очистить
                      </button>
                    )}
                  </div>
                  <div className="filter-dropdown-options">
                    {Object.entries(group.options ?? {}).map(([key, count]) =>
                      renderFilterCheckboxRow(group.group, key, optionLabel(group, key), count),
                    )}
                  </div>
                </div>
              </details>
            ))}
          </div>
        )}
      </section>

      <div className="results-col">
          <div className="results-toolbar">
            <div className="toolbar-left">
              <div className="inline-search">
                <i className="ti ti-search" />
                <input
                  type="text"
                  placeholder="Инфляция, ставка, ВВП…"
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(1);
                  }}
                />
              </div>
              <select
                className="select-sort"
                value={sort}
                onChange={(e) => setSort(e.target.value as IndicatorFilters["sort"])}
              >
                <option value="name">По названию</option>
                <option value="updated">По дате обновления</option>
                <option value="country">По стране</option>
              </select>
              <label className={`filter-pill filter-pill-compact ${favoritesOnly ? "active" : ""}`}>
                <input
                  type="checkbox"
                  checked={favoritesOnly}
                  onChange={(e) => setFavoritesOnly(e.target.checked)}
                />
                <span className="filter-pill-box" aria-hidden="true">
                  <i className="ti ti-check" />
                </span>
                <span className="filter-pill-label">Только избранное</span>
              </label>
            </div>
          </div>

          {selected.length > 0 && (
            <div className="bulk-bar">
              <span>Выбрано: {selected.length}</span>
              <button type="button" className="btn primary" onClick={bulkCompare}>
                {compareLabel}
              </button>
              <button type="button" className="btn" onClick={() => setSelected([])}>
                Отмена
              </button>
            </div>
          )}

          {loadError ? (
            <div className="card card-pad empty-state">
              <p>{loadError}</p>
              <button type="button" className="btn primary" onClick={() => void load()}>
                Повторить
              </button>
            </div>
          ) : loading ? (
            <div className="card card-pad">
              <p className="meta">Загрузка…</p>
            </div>
          ) : items.length === 0 ? (
            <div className="card card-pad empty-state">
              <p>Ничего не найдено. Измените фильтры или поисковый запрос.</p>
              <button type="button" className="btn" onClick={resetFilters}>
                Сбросить фильтры
              </button>
            </div>
          ) : view === "table" ? (
            <div className="table-card">
              <table className="data-table">
                <thead>
                  <tr>
                    <th className="checkbox-cell">
                      <input type="checkbox" checked={selected.length === items.length} onChange={toggleSelectAll} />
                    </th>
                    <th>Показатель</th>
                    <th>Страна</th>
                    <th className="num">Последнее</th>
                    <th className="num">Изменение</th>
                    <th>Частота</th>
                    <th>Источник</th>
                    <th>Обновлено</th>
                    <th />
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {items.map((row) => (
                    <tr
                      key={row.id}
                      className={`row ${selected.includes(row.id) ? "selected" : ""} ${rowPreview?.item.id === row.id && rowPreviewVisible ? "preview-active" : ""}`}
                      onMouseMove={(event) => handleRowPointerMove(row, event)}
                      onMouseLeave={(event) => {
                        const tbody = event.currentTarget.closest("tbody");
                        if (event.relatedTarget instanceof Node && tbody?.contains(event.relatedTarget)) return;
                        hideRowPreview();
                      }}
                    >
                      <td className="checkbox-cell">
                        <input type="checkbox" checked={selected.includes(row.id)} onChange={() => toggleSelect(row.id)} />
                      </td>
                      <td>
                        <Link href={`/app/indicators/${row.id}`} className="indicator-name" title={row.name_ru}>
                          {row.name_ru}
                        </Link>
                      </td>
                      <td>
                        <span className="country-flag">{row.country.toUpperCase()}</span>
                      </td>
                      <td className="num value-cell">{row.last_value ?? "—"}</td>
                      <td className="num">
                        <DeltaBadge direction={row.delta_direction} value={row.last_change} />
                      </td>
                      <td>
                        <span className="freq-tag">{FREQ_LABELS[row.frequency] || row.frequency}</span>
                      </td>
                      <td>
                        <SourceTag source={row.source} />
                      </td>
                      <td className="updated-cell">{formatDate(row.updated_at)}</td>
                      <td>
                        <button
                          type="button"
                          className={`row-icon-btn star ${favoriteIds.includes(row.id) ? "active" : ""}`}
                          onClick={() => toggleFavorite(row.id)}
                          aria-label="Избранное"
                        >
                          <i className={`ti ${favoriteIds.includes(row.id) ? "ti-star-filled" : "ti-star"}`} />
                        </button>
                      </td>
                      <td>
                        <button
                          type="button"
                          className="row-icon-btn"
                          onClick={() => addToCompare(row.id)}
                          aria-label={compareLabel}
                          title={compareLabel}
                        >
                          <i className="ti ti-plus" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="cards-grid">
              {items.map((row) => (
                <div key={row.id} className="indicator-card card card-pad">
                  <div className="indicator-card-head">
                    <Link href={`/app/indicators/${row.id}`} className="indicator-name">
                      {row.name_ru}
                    </Link>
                    <button
                      type="button"
                      className={`row-icon-btn star ${favoriteIds.includes(row.id) ? "active" : ""}`}
                      onClick={() => toggleFavorite(row.id)}
                    >
                      <i className={`ti ${favoriteIds.includes(row.id) ? "ti-star-filled" : "ti-star"}`} />
                    </button>
                  </div>
                  <p className="value-cell card-value">{row.last_value ?? "—"}</p>
                  <DeltaBadge direction={row.delta_direction} value={row.last_change} />
                  <MiniSparkline values={row.sparkline ?? []} width={240} height={36} />
                  <div className="card-meta">
                    <MetaTags country={row.country} source={row.source} />
                  </div>
                  <button type="button" className="btn" onClick={() => addToCompare(row.id)}>
                    {compareLabel}
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="pagination-bar">
            <select value={pageSize} onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
            <div className="pagination-controls">
              <button type="button" className="btn" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                Назад
              </button>
              <span className="meta">
                Стр. {page} · {total.toLocaleString("ru-RU")} всего
              </span>
              <button
                type="button"
                className="btn"
                disabled={page * pageSize >= total}
                onClick={() => setPage((p) => p + 1)}
              >
                Вперёд
              </button>
            </div>
            <Link href="/app/compare" className="btn">
              Открыть сравнение
            </Link>
          </div>
      </div>

      <IndicatorRowPreview
        preview={rowPreview}
        visible={rowPreviewVisible}
        categoryLabel={rowPreview ? labels?.categories[rowPreview.item.category] : undefined}
      />
    </div>
  );
}
