"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { MetaTags } from "@/components/ui/MetaTags";
import { MiniSparkline } from "./MiniSparkline";
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

const FILTER_UI_MODES = [
  { id: "pills", label: "A · Чипы", hint: "Все опции видны сразу, быстрый мультивыбор" },
  { id: "dropdown", label: "B · Выпадающие", hint: "Компактно, раскрываете только нужную группу" },
  { id: "panel", label: "C · Панель", hint: "Рекомендуем: одна кнопка, поиск, все группы сразу" },
] as const;

type FilterUiMode = (typeof FILTER_UI_MODES)[number]["id"];

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
  const [view, setView] = useState<"table" | "cards">("table");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<IndicatorFilters["sort"]>("name");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [draft, setDraft] = useState<DraftFilters>({ country: [], category: [], frequency: [], source: [] });
  const [applied, setApplied] = useState<DraftFilters>({ country: [], category: [], frequency: [], source: [] });
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [favoriteIds, setFavoriteIds] = useState<string[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [panelOpen, setPanelOpen] = useState(false);
  const [panelSearch, setPanelSearch] = useState("");
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setFavoriteIds(loadIds(FAVORITES_KEY));
    Promise.all([fetchIndicatorFacets(), fetchFacetLabels()]).then(([f, l]) => {
      setFacets(f);
      setLabels(l);
    });
  }, []);

  useEffect(() => {
    if (!panelOpen) return;
    const onPointerDown = (event: MouseEvent) => {
      if (!panelRef.current?.contains(event.target as Node)) setPanelOpen(false);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setPanelOpen(false);
    };
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [panelOpen]);

  const load = useCallback(async () => {
    setLoading(true);
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
      let list = res.items;
      if (favoritesOnly) {
        const fav = loadIds(FAVORITES_KEY);
        list = list.filter((i) => fav.includes(i.id));
      }
      setItems(list);
      setTotal(favoritesOnly ? list.length : res.total);
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
    saveIds(COMPARE_KEY, [...current, id]);
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
    window.location.href = "/app/compare";
  };

  const filterGroups = useMemo<FilterGroupConfig[]>(() => {
    if (!facets) return [];
    return [
      { title: "Регион", group: "country", options: facets.countries, labelMap: labels?.countries },
      { title: "Категория", group: "category", options: facets.categories, labelMap: labels?.categories },
      { title: "Частота", group: "frequency", options: facets.frequencies, labelMap: FREQ_LABELS },
      { title: "Источник", group: "source", options: facets.sources, labelMap: SOURCE_LABELS },
    ];
  }, [facets, labels]);

  const draftSelectedTotal = draft.country.length + draft.category.length + draft.frequency.length + draft.source.length;

  const optionLabel = (group: FilterGroupConfig, key: string) =>
    group.labelMap?.[key] || key.toUpperCase();

  const groupSelectedCount = (group: FilterGroupKey) => (draft[group] as string[]).length;

  const dropdownSummary = (title: string, group: FilterGroupKey) => {
    const count = groupSelectedCount(group);
    return count > 0 ? `${title} · ${count}` : title;
  };

  const filterOptionsForGroup = (group: FilterGroupConfig, withSearch = false) => {
    const needle = withSearch ? panelSearch.trim().toLowerCase() : "";
    return Object.entries(group.options).filter(([key]) => {
      if (!needle) return true;
      return optionLabel(group, key).toLowerCase().includes(needle);
    });
  };

  const clearGroup = (group: FilterGroupKey) => {
    setDraft((prev) => ({ ...prev, [group]: [] }));
  };

  const renderFilterCheckboxRow = (
    group: FilterGroupKey,
    key: string,
    label: string,
    count: number,
    variant: "list" | "pill" = "list",
  ) => {
    const checked = (draft[group] as string[]).includes(key);
    if (variant === "pill") {
      return (
        <label key={key} className={`filter-pill ${checked ? "active" : ""}`}>
          <input type="checkbox" checked={checked} onChange={() => toggleDraft(group, key)} />
          <span className="filter-pill-box" aria-hidden="true">
            <i className="ti ti-check" />
          </span>
          <span className="filter-pill-label">{label}</span>
          <span className="filter-pill-count">{count}</span>
        </label>
      );
    }
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

  const renderPillsFilters = () => (
    <div className="filters-bar-body">
      {filterGroups.map((group) => (
        <div key={group.group} className="filter-group-row">
          <span className="filter-group-label">{group.title}</span>
          <div className="filter-group-options">
            {Object.entries(group.options).map(([key, count]) =>
              renderFilterCheckboxRow(group.group, key, optionLabel(group, key), count, "pill"),
            )}
          </div>
        </div>
      ))}
    </div>
  );

  const renderDropdownFilters = () => (
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
              {Object.entries(group.options).map(([key, count]) =>
                renderFilterCheckboxRow(group.group, key, optionLabel(group, key), count),
              )}
            </div>
          </div>
        </details>
      ))}
    </div>
  );

  const renderPanelFilters = (preview = false) => (
    <div className={`filter-panel-wrap ${preview ? "is-preview" : ""}`} ref={preview ? undefined : panelRef}>
      <button
        type="button"
        className={`filter-panel-trigger ${!preview && panelOpen ? "open" : ""} ${draftSelectedTotal ? "has-value" : ""}`}
        aria-expanded={preview ? true : panelOpen}
        disabled={preview}
        onClick={() => !preview && setPanelOpen((open) => !open)}
      >
        <i className="ti ti-filter" aria-hidden="true" />
        <span>Все фильтры</span>
        {draftSelectedTotal > 0 && <span className="filter-panel-badge">{draftSelectedTotal}</span>}
        <i className="ti ti-chevron-down filter-panel-chevron" aria-hidden="true" />
      </button>
      {(preview || panelOpen) && (
        <div className="filter-panel-popover">
          <div className="filter-panel-popover-head">
            <div className="filter-panel-search">
              <i className="ti ti-search" aria-hidden="true" />
              <input
                type="text"
                placeholder="Поиск по опциям фильтра…"
                value={panelSearch}
                onChange={(e) => setPanelSearch(e.target.value)}
              />
            </div>
            {draftSelectedTotal > 0 && (
              <button type="button" className="chip-reset" onClick={resetFilters}>
                Сбросить всё
              </button>
            )}
          </div>
          <div className="filter-panel-grid">
            {filterGroups.map((group) => {
              const options = filterOptionsForGroup(group, true);
              return (
                <div key={group.group} className="filter-panel-group">
                  <div className="filter-panel-group-head">
                    <span>{group.title}</span>
                    {groupSelectedCount(group.group) > 0 && (
                      <button type="button" className="chip-reset" onClick={() => clearGroup(group.group)}>
                        Очистить
                      </button>
                    )}
                  </div>
                  <div className="filter-panel-options">
                    {options.length === 0 ? (
                      <p className="meta filter-panel-empty">Ничего не найдено</p>
                    ) : (
                      options.map(([key, count]) =>
                        renderFilterCheckboxRow(group.group, key, optionLabel(group, key), count),
                      )
                    )}
                  </div>
                </div>
              );
            })}
          </div>
          {!preview && (
            <div className="filter-panel-footer">
              <span className="meta">Выбрано {draftSelectedTotal} значений</span>
              <button
                type="button"
                className="btn primary"
                onClick={() => {
                  applyFilters();
                  setPanelOpen(false);
                }}
              >
                Применить
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );

  const renderFiltersShell = (variant: FilterUiMode, body: ReactNode) => {
    const meta = FILTER_UI_MODES.find((mode) => mode.id === variant);
    return (
      <section id={`filter-variant-${variant}`} className={`filters-bar filters-variant filters-variant-${variant}`}>
        <div className="filters-variant-label">
          <span className="filters-variant-badge">{meta?.label}</span>
          <span className="filters-variant-hint">{meta?.hint}</span>
        </div>
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
        {body}
      </section>
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

      <div className="filters-compare">
        <div className="filters-compare-head">
          <div>
            <p className="filters-compare-title">Сравнение вариантов фильтров</p>
            <p className="meta filters-compare-note">
              Все три блока используют одно состояние — меняете в любом, значения синхронизируются.
            </p>
          </div>
          <div className="filter-ui-switch" aria-label="Прокрутка к варианту">
            {FILTER_UI_MODES.map((mode) => (
              <button
                key={mode.id}
                type="button"
                title={mode.hint}
                onClick={() =>
                  document.getElementById(`filter-variant-${mode.id}`)?.scrollIntoView({ behavior: "smooth", block: "start" })
                }
              >
                {mode.label}
              </button>
            ))}
          </div>
        </div>

        <div className="filters-compare-stack">
          {facets && renderFiltersShell("pills", renderPillsFilters())}
          {facets && renderFiltersShell("dropdown", renderDropdownFilters())}
          {facets && renderFiltersShell("panel", renderPanelFilters(true))}
        </div>
      </div>

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
                Сравнить
              </button>
              <button type="button" className="btn" onClick={() => setSelected([])}>
                Отмена
              </button>
            </div>
          )}

          {loading ? (
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
                    <tr key={row.id} className={`row ${selected.includes(row.id) ? "selected" : ""}`}>
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
                        <button type="button" className="row-icon-btn" onClick={() => addToCompare(row.id)} aria-label="Сравнение">
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
                  <MiniSparkline values={row.sparkline} width={240} height={36} />
                  <div className="card-meta">
                    <MetaTags country={row.country} source={row.source} />
                  </div>
                  <button type="button" className="btn" onClick={() => addToCompare(row.id)}>
                    В сравнение
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
    </div>
  );
}
