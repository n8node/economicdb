"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { adminAuthFetch } from "@/lib/auth";

type CalendarSource = {
  id: string;
  label: string;
  description: string;
  requires_api_key: boolean;
  tier: string;
};

type CalendarStats = {
  total: number;
  upcoming: number;
  past: number;
  with_actual: number;
  with_forecast: number;
  by_source: Record<string, number>;
  by_country: Record<string, number>;
};

type CalendarJob = {
  id: number;
  provider_id: string;
  trigger: string;
  status: string;
  indicator_ids: string[];
  date_from: string | null;
  date_to: string | null;
  records: number | null;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
};

type SyncResult = {
  ok: boolean;
  message?: string;
  records?: number;
  enriched?: number;
  job_id?: number;
  sources?: Record<string, number>;
  skipped?: Array<{ source?: string; reason?: string }>;
};

const SOURCE_LABELS: Record<string, string> = {
  fred: "FRED",
  cbr: "ЦБ РФ",
  ecb: "ECB",
  rosstat: "Росстат",
  fomc: "FOMC",
};

export function CalendarPanel() {
  const [sources, setSources] = useState<CalendarSource[]>([]);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [stats, setStats] = useState<CalendarStats | null>(null);
  const [jobs, setJobs] = useState<CalendarJob[]>([]);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [enrich, setEnrich] = useState(true);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const loadAll = useCallback(async () => {
    const [sourcesRes, statsRes, jobsRes, defaults] = await Promise.all([
      adminAuthFetch<{ sources: CalendarSource[]; default_sources: string[] }>("/admin/calendar/sources"),
      adminAuthFetch<CalendarStats>("/admin/calendar/stats"),
      adminAuthFetch<CalendarJob[]>("/admin/calendar/jobs?limit=20"),
      adminAuthFetch<{ date_from: string; date_to: string; sources: string[] }>("/admin/calendar/defaults"),
    ]);
    setSources(sourcesRes.sources);
    setSelectedSources(defaults.sources);
    setDateFrom(defaults.date_from);
    setDateTo(defaults.date_to);
    setStats(statsRes);
    setJobs(jobsRes);
  }, []);

  useEffect(() => {
    loadAll().catch(() => setMessage("Не удалось загрузить данные календаря"));
  }, [loadAll]);

  const toggleSource = (id: string) => {
    setSelectedSources((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id],
    );
  };

  async function runSync(dryRun: boolean) {
    if (!selectedSources.length) {
      setMessage("Выберите хотя бы один источник");
      return;
    }
    setBusy(true);
    setMessage("");
    try {
      const result = await adminAuthFetch<SyncResult>("/admin/calendar/sync", {
        method: "POST",
        body: JSON.stringify({
          date_from: dateFrom || null,
          date_to: dateTo || null,
          sources: selectedSources,
          enrich,
          dry_run: dryRun,
        }),
      });
      if (result.ok) {
        const srcSummary = result.sources
          ? Object.entries(result.sources)
              .map(([k, v]) => `${SOURCE_LABELS[k] || k}: ${v}`)
              .join(" · ")
          : "";
        setMessage(
          dryRun
            ? `Предпросмотр: ${result.records ?? 0} событий. ${srcSummary}`
            : `${result.message || "Готово"} ${srcSummary}`,
        );
        if (!dryRun) await loadAll();
      } else {
        setMessage(result.message || "Ошибка синхронизации");
      }
    } catch {
      setMessage("Ошибка запроса синхронизации");
    } finally {
      setBusy(false);
    }
  }

  async function runEnrich() {
    setBusy(true);
    setMessage("");
    try {
      const result = await adminAuthFetch<SyncResult>("/admin/calendar/enrich", {
        method: "POST",
        body: JSON.stringify({ dry_run: false }),
      });
      setMessage(result.message || "Обогащение завершено");
      await loadAll();
    } catch {
      setMessage("Ошибка обогащения");
    } finally {
      setBusy(false);
    }
  }

  const statCards = useMemo(
    () => [
      { label: "Всего событий", value: stats?.total ?? 0 },
      { label: "Предстоящие", value: stats?.upcoming ?? 0 },
      { label: "Прошедшие", value: stats?.past ?? 0 },
      { label: "С фактом", value: stats?.with_actual ?? 0 },
    ],
    [stats],
  );

  return (
    <div>
      <div className="admin-panel-head">
        <div>
          <h1>Календарь макрособытий</h1>
          <p className="muted">Загрузка расписания релизов и заседаний из официальных источников</p>
        </div>
        <Link href="/app/calendar" className="admin-btn admin-btn-secondary" target="_top">
          Открыть календарь →
        </Link>
      </div>

      {message && <div className="admin-notice">{message}</div>}

      <div className="admin-stat-grid">
        {statCards.map((card) => (
          <div key={card.label} className="admin-stat-card">
            <span className="muted">{card.label}</span>
            <strong>{card.value}</strong>
          </div>
        ))}
      </div>

      <div className="admin-card-block">
        <h2>Источники</h2>
        <p className="muted">Выберите, откуда загружать события. FRED требует API key в разделе «Провайдеры».</p>
        <div className="admin-source-grid">
          {sources.map((source) => (
            <label key={source.id} className={`admin-source-card${selectedSources.includes(source.id) ? " active" : ""}`}>
              <input
                type="checkbox"
                checked={selectedSources.includes(source.id)}
                onChange={() => toggleSource(source.id)}
              />
              <div>
                <div className="admin-source-head">
                  <strong>{source.label}</strong>
                  <span className="admin-tier">Tier {source.tier}</span>
                </div>
                <p className="muted">{source.description}</p>
                {source.requires_api_key && <span className="admin-tag">Нужен API key</span>}
              </div>
            </label>
          ))}
        </div>
      </div>

      <div className="admin-card-block">
        <h2>Период загрузки</h2>
        <div className="admin-form-row">
          <label>
            С
            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </label>
          <label>
            По
            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </label>
        </div>
        <label className="admin-check">
          <input type="checkbox" checked={enrich} onChange={(e) => setEnrich(e.target.checked)} />
          Обогатить прошедшие события фактами из рядов показателей
        </label>
        <div className="admin-actions">
          <button type="button" className="admin-btn" disabled={busy} onClick={() => runSync(false)}>
            {busy ? "Загрузка…" : "Обновить календарь"}
          </button>
          <button type="button" className="admin-btn admin-btn-secondary" disabled={busy} onClick={() => runSync(true)}>
            Предпросмотр
          </button>
          <button type="button" className="admin-btn admin-btn-secondary" disabled={busy} onClick={runEnrich}>
            Только обогащение
          </button>
        </div>
      </div>

      {stats && Object.keys(stats.by_source).length > 0 && (
        <div className="admin-card-block">
          <h2>Распределение по источникам</h2>
          <div className="admin-chip-row">
            {Object.entries(stats.by_source).map(([key, count]) => (
              <span key={key} className="admin-chip">
                {SOURCE_LABELS[key] || key}: {count}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="admin-card-block">
        <h2>Журнал синхронизаций</h2>
        {jobs.length === 0 ? (
          <p className="muted">Синхронизаций пока не было</p>
        ) : (
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Источники</th>
                  <th>Период</th>
                  <th>Записей</th>
                  <th>Статус</th>
                  <th>Время</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <tr key={job.id}>
                    <td>{job.id}</td>
                    <td>{job.indicator_ids.map((s) => SOURCE_LABELS[s] || s).join(", ") || "—"}</td>
                    <td>
                      {job.date_from || "—"} — {job.date_to || "—"}
                    </td>
                    <td>{job.records ?? "—"}</td>
                    <td>
                      <span className={`admin-status ${job.status}`}>{job.status}</span>
                    </td>
                    <td>{job.started_at ? new Date(job.started_at).toLocaleString("ru-RU") : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
