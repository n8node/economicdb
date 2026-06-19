"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { adminAuthFetch } from "@/lib/auth";

type Tab = "sync" | "catalog" | "jobs";

type Provider = { id: string; name_ru: string; enabled: boolean };

type Indicator = {
  id: string;
  name_ru: string;
  country: string;
  category: string;
  frequency: string;
  source: string;
  external_id: string | null;
  has_data: boolean;
};

type Template = Indicator & { wave: string; in_catalog: boolean; unit: string };

type EtlJob = {
  id: number;
  provider_id: string;
  trigger: string;
  status: string;
  country: string | null;
  indicator_ids: string[];
  date_from: string | null;
  date_to: string | null;
  dry_run: boolean;
  records: number | null;
  synced_indicators: string[];
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
};

type SyncResult = {
  ok: boolean;
  message?: string;
  error?: string;
  records?: number;
  job_id?: number;
  preview?: Array<{
    indicator_id: string;
    points: number;
    first_date?: string;
    last_date?: string;
    last_value?: string;
  }>;
};

const COUNTRIES = [
  { value: "", label: "Все страны" },
  { value: "ru", label: "Россия" },
  { value: "us", label: "США" },
  { value: "eu", label: "Еврозона" },
  { value: "cn", label: "Китай" },
  { value: "jp", label: "Япония" },
  { value: "gb", label: "Великобритания" },
  { value: "de", label: "Германия" },
  { value: "world", label: "Мир" },
];

const WAVES = [
  { value: "w1", label: "W1 — следующая волна" },
  { value: "w2", label: "W2" },
  { value: "all", label: "Все шаблоны" },
];

export function DataPanel() {
  const [tab, setTab] = useState<Tab>("sync");
  const [message, setMessage] = useState("");
  const [providers, setProviders] = useState<Provider[]>([]);
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [jobs, setJobs] = useState<EtlJob[]>([]);
  const [defaults, setDefaults] = useState({ date_from: "", date_to: "" });

  const [providerId, setProviderId] = useState("cbr");
  const [country, setCountry] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [wave, setWave] = useState("w1");
  const [busy, setBusy] = useState(false);

  const loadProviders = useCallback(async () => {
    const data = await adminAuthFetch<Provider[]>("/admin/providers");
    setProviders(data);
    if (data.length && !data.find((item) => item.id === providerId)) {
      setProviderId(data[0].id);
    }
  }, [providerId]);

  const loadIndicators = useCallback(async () => {
    const params = new URLSearchParams();
    if (providerId) params.set("provider_id", providerId);
    if (country) params.set("country", country);
    const data = await adminAuthFetch<Indicator[]>(`/admin/indicators?${params.toString()}`);
    setIndicators(data);
    setSelectedIds((prev) => prev.filter((id) => data.some((item) => item.id === id)));
  }, [providerId, country]);

  const loadTemplates = useCallback(async () => {
    const data = await adminAuthFetch<Template[]>(`/admin/indicators/templates?wave=${wave}`);
    setTemplates(data);
  }, [wave]);

  const loadJobs = useCallback(async () => {
    const params = providerId ? `?provider_id=${providerId}&limit=50` : "?limit=50";
    const data = await adminAuthFetch<EtlJob[]>(`/admin/etl/jobs${params}`);
    setJobs(data);
  }, [providerId]);

  const loadDefaults = useCallback(async () => {
    const data = await adminAuthFetch<{ date_from: string; date_to: string }>("/admin/etl/defaults");
    setDefaults(data);
    setDateFrom(data.date_from);
    setDateTo(data.date_to);
  }, []);

  useEffect(() => {
    loadProviders().catch(() => setMessage("Не удалось загрузить провайдеров"));
    loadDefaults().catch(() => undefined);
  }, [loadProviders, loadDefaults]);

  useEffect(() => {
    if (tab === "sync" || tab === "catalog") {
      loadIndicators().catch(() => setMessage("Не удалось загрузить показатели"));
    }
    if (tab === "catalog") {
      loadTemplates().catch(() => setMessage("Не удалось загрузить шаблоны"));
    }
    if (tab === "jobs") {
      loadJobs().catch(() => setMessage("Не удалось загрузить журнал ETL"));
    }
  }, [tab, loadIndicators, loadTemplates, loadJobs]);

  const payload = useMemo(
    () => ({
      provider_id: providerId,
      country: country || null,
      indicator_ids: selectedIds.length ? selectedIds : null,
      date_from: dateFrom || null,
      date_to: dateTo || null,
    }),
    [providerId, country, selectedIds, dateFrom, dateTo],
  );

  async function runPreview() {
    setBusy(true);
    setMessage("");
    try {
      const result = await adminAuthFetch<SyncResult>("/admin/etl/preview", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      if (!result.ok) {
        setMessage(result.message || result.error || "Ошибка предпросмотра");
        return;
      }
      const lines = (result.preview || [])
        .map(
          (item) =>
            `${item.indicator_id}: ${item.points} точек` +
            (item.last_date ? ` · до ${item.last_date}` : ""),
        )
        .join(" · ");
      setMessage(`${result.message || "OK"}${lines ? ` · ${lines}` : ""}`);
    } catch {
      setMessage("Ошибка предпросмотра");
    } finally {
      setBusy(false);
    }
  }

  async function runSync() {
    setBusy(true);
    setMessage("");
    try {
      const result = await adminAuthFetch<SyncResult>("/admin/etl/sync", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      if (!result.ok) {
        setMessage(result.message || result.error || "Ошибка загрузки");
        return;
      }
      setMessage(result.message || `Загружено ${result.records ?? 0} записей · job #${result.job_id ?? "—"}`);
      await loadIndicators();
      await loadJobs();
    } catch {
      setMessage("Ошибка загрузки");
    } finally {
      setBusy(false);
    }
  }

  async function importTemplates() {
    setBusy(true);
    setMessage("");
    try {
      const result = await adminAuthFetch<{ imported: string[]; skipped: string[] }>(
        `/admin/indicators/import-templates?wave=${wave}`,
        { method: "POST" },
      );
      setMessage(
        `Импортировано: ${result.imported.length}${result.skipped.length ? ` · пропущено: ${result.skipped.length}` : ""}`,
      );
      await loadIndicators();
      await loadTemplates();
    } catch {
      setMessage("Ошибка импорта шаблонов");
    } finally {
      setBusy(false);
    }
  }

  function toggleIndicator(id: string) {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]));
  }

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Данные и ETL</h1>
      <p className="muted" style={{ maxWidth: 820 }}>
        Самостоятельная загрузка макропоказателей: выберите провайдер, страну, период и показатели.
        Предпросмотр не пишет в базу. Загрузка выполняется на сервере и попадает в журнал ETL.
      </p>

      <div className="admin-tabs">
        {(
          [
            ["sync", "Загрузка"],
            ["catalog", "Каталог"],
            ["jobs", "Журнал ETL"],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            type="button"
            className={`admin-btn${tab === key ? " primary" : ""}`}
            onClick={() => setTab(key)}
          >
            {label}
          </button>
        ))}
      </div>

      {message ? <p className="muted">{message}</p> : null}

      {tab === "sync" ? (
        <div className="admin-etl-grid">
          <section className="admin-panel">
            <h2>Параметры загрузки</h2>
            <div className="admin-form-row">
              <label>
                Провайдер
                <select
                  className="admin-input"
                  value={providerId}
                  onChange={(event) => setProviderId(event.target.value)}
                >
                  {providers.map((provider) => (
                    <option key={provider.id} value={provider.id}>
                      {provider.name_ru} ({provider.id})
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Страна
                <select
                  className="admin-input"
                  value={country}
                  onChange={(event) => setCountry(event.target.value)}
                >
                  {COUNTRIES.map((item) => (
                    <option key={item.value || "all"} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="admin-form-row">
              <label>
                С даты
                <input
                  className="admin-input"
                  type="date"
                  value={dateFrom}
                  onChange={(event) => setDateFrom(event.target.value)}
                />
              </label>
              <label>
                По дату
                <input
                  className="admin-input"
                  type="date"
                  value={dateTo}
                  onChange={(event) => setDateTo(event.target.value)}
                />
              </label>
            </div>
            <p className="muted">
              По умолчанию — 5 лет ({defaults.date_from} … {defaults.date_to}). Пустой список показателей = все
              доступные для провайдера.
            </p>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button type="button" className="admin-btn" disabled={busy} onClick={runPreview}>
                Предпросмотр
              </button>
              <button type="button" className="admin-btn primary" disabled={busy} onClick={runSync}>
                Загрузить
              </button>
              <button
                type="button"
                className="admin-btn"
                onClick={() => {
                  setDateFrom(defaults.date_from);
                  setDateTo(defaults.date_to);
                }}
              >
                5 лет
              </button>
            </div>
          </section>

          <section className="admin-panel">
            <h2>Показатели ({selectedIds.length} выбрано)</h2>
            <table className="admin-table">
              <thead>
                <tr>
                  <th />
                  <th>ID</th>
                  <th>Название</th>
                  <th>Страна</th>
                  <th>Данные</th>
                </tr>
              </thead>
              <tbody>
                {indicators.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(item.id)}
                        onChange={() => toggleIndicator(item.id)}
                      />
                    </td>
                    <td>{item.id}</td>
                    <td>{item.name_ru}</td>
                    <td>{item.country}</td>
                    <td>{item.has_data ? "есть" : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </div>
      ) : null}

      {tab === "catalog" ? (
        <div>
          <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 16 }}>
            <select className="admin-input" style={{ width: 240 }} value={wave} onChange={(e) => setWave(e.target.value)}>
              {WAVES.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
            <button type="button" className="admin-btn primary" disabled={busy} onClick={importTemplates}>
              Импортировать волну в каталог
            </button>
          </div>
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Название</th>
                <th>Страна</th>
                <th>Источник</th>
                <th>external_id</th>
                <th>В каталоге</th>
              </tr>
            </thead>
            <tbody>
              {templates.map((item) => (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{item.name_ru}</td>
                  <td>{item.country}</td>
                  <td>{item.source}</td>
                  <td className="muted">{item.external_id}</td>
                  <td>{item.in_catalog ? "да" : "нет"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {tab === "jobs" ? (
        <table className="admin-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Провайдер</th>
              <th>Статус</th>
              <th>Страна</th>
              <th>Период</th>
              <th>Записей</th>
              <th>Начало</th>
              <th>Ошибка</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr key={job.id}>
                <td>{job.id}</td>
                <td>{job.provider_id}</td>
                <td>{job.status}</td>
                <td>{job.country || "—"}</td>
                <td>
                  {job.date_from || "—"} … {job.date_to || "—"}
                </td>
                <td>{job.records ?? "—"}</td>
                <td>{job.started_at || "—"}</td>
                <td className="muted">{job.error_message || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </div>
  );
}
