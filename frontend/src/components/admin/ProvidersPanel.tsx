"use client";

import { useEffect, useState } from "react";
import { adminAuthFetch } from "@/lib/auth";

type Provider = {
  id: string;
  name_ru: string;
  enabled: boolean;
  base_url: string | null;
  has_credentials: boolean;
  supports_credentials: boolean;
  last_test_at: string | null;
  last_test_status: string | null;
  last_sync_at: string | null;
  last_sync_status: string | null;
};

type TestDetails = {
  series_id?: string;
  title?: string;
  frequency?: string;
  latest_observation?: { date: string; value: string };
  key_rate_latest?: { date: string; value: string };
  usd_rub_latest?: { date: string; value: string };
  cpi_yoy_latest?: { date: string; value: string };
};

const PUBLIC_API_PROVIDERS = new Set(["cbr", "rosstat", "oecd"]);

function providerStatus(provider: Provider) {
  if (provider.last_test_status === "error" || provider.last_sync_status === "error") {
    return { className: "error", label: "Ошибка подключения" };
  }
  if (provider.last_test_status === "ok" || provider.last_sync_status === "ok") {
    return { className: "ok", label: provider.enabled ? "Подключён" : "Проверен, выключен" };
  }
  return { className: "idle", label: "Не проверен" };
}

export function ProvidersPanel() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [message, setMessage] = useState("");
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({});

  async function load() {
    const data = await adminAuthFetch<Provider[]>("/admin/providers");
    setProviders(data);
  }

  useEffect(() => {
    load().catch(() => setMessage("Не удалось загрузить провайдеров"));
  }, []);

  async function sync(id: string) {
    setMessage("");
    try {
      const result = await adminAuthFetch<{ ok: boolean; message?: string; error?: string; records?: number }>(
        `/admin/providers/${id}/sync`,
        { method: "POST" },
      );
      if (!result.ok) {
        setMessage(result.message || result.error || "Ошибка синхронизации");
      } else {
        setMessage(result.message || `Загружено записей: ${result.records ?? 0}`);
      }
      await load();
    } catch {
      setMessage("Ошибка синхронизации");
    }
  }

  async function saveCredentials(id: string) {
    const apiKey = apiKeys[id]?.trim();
    if (!apiKey) {
      setMessage("Введите API key");
      return;
    }
    setMessage("");
    try {
      await adminAuthFetch(`/admin/providers/${id}/credentials`, {
        method: "PUT",
        body: JSON.stringify({ api_key: apiKey }),
      });
      setApiKeys((prev) => ({ ...prev, [id]: "" }));
      setMessage("API key сохранён");
      await load();
    } catch {
      setMessage("Не удалось сохранить API key");
    }
  }

  async function testConnection(id: string) {
    setMessage("");
    const apiKey = apiKeys[id]?.trim();
    try {
      const result = await adminAuthFetch<{
        ok: boolean;
        message?: string;
        error?: string;
        details?: TestDetails;
      }>(`/admin/providers/${id}/test`, {
        method: "POST",
        body: JSON.stringify(apiKey ? { api_key: apiKey } : {}),
      });
      if (!result.ok) {
        setMessage(result.message || result.error || "Ошибка подключения");
        await load();
        return;
      }
      const latest = result.details?.latest_observation;
      const keyRate = result.details?.key_rate_latest;
      const usdRub = result.details?.usd_rub_latest;
      const cpiYoy = result.details?.cpi_yoy_latest;
      const extra = latest
        ? ` · ${latest.date}: ${latest.value}`
        : keyRate && usdRub
          ? ` · ставка ${keyRate.value}% (${keyRate.date}), USD/RUB ${usdRub.value} (${usdRub.date})`
          : cpiYoy
            ? ` · ИПЦ ${cpiYoy.value}% (${cpiYoy.date})`
            : "";
      setMessage(`${result.message || "OK"}${extra}`);
      await load();
    } catch {
      setMessage("Ошибка проверки подключения");
    }
  }

  async function toggleEnabled(id: string, enabled: boolean) {
    setMessage("");
    try {
      await adminAuthFetch(`/admin/providers/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ enabled }),
      });
      await load();
    } catch {
      setMessage(enabled ? "Сначала сохраните API key" : "Не удалось изменить статус");
    }
  }

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Провайдеры данных</h1>
      <p className="muted" style={{ maxWidth: 720 }}>
        Для проверки на реальных данных: FRED (нужен API key) или ЦБ РФ (публичный API, без ключа).
        Включённые провайдеры синхронизируются автоматически каждый день в 04:00 МСК (worker).
        После деплоя: Ctrl+Shift+R на сайте или очистка данных для {`economicdb.com`} один раз.
      </p>
      {message ? <p className="muted">{message}</p> : null}
      <table className="admin-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Название</th>
            <th>Подключение</th>
            <th>Ключ</th>
            <th>Последняя синхронизация</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {providers.map((provider) => (
            <tr key={provider.id}>
              <td>{provider.id}</td>
              <td>
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <span>{provider.name_ru}</span>
                  <span className="muted">{provider.enabled ? "Автосинхронизация включена" : "Автосинхронизация выключена"}</span>
                </div>
              </td>
              <td>
                <span className="provider-status">
                  <span className={`provider-status-dot ${providerStatus(provider).className}`} />
                  <span>{providerStatus(provider).label}</span>
                </span>
                {provider.last_test_at ? <div className="muted">{provider.last_test_at}</div> : null}
              </td>
              <td>
                {provider.supports_credentials ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: 6, minWidth: 220 }}>
                    <input
                      className="admin-input"
                      type="password"
                      placeholder={provider.has_credentials ? "Ключ сохранён · новый ключ" : "API key"}
                      value={apiKeys[provider.id] || ""}
                      onChange={(event) =>
                        setApiKeys((prev) => ({ ...prev, [provider.id]: event.target.value }))
                      }
                    />
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                      <button type="button" className="admin-btn" onClick={() => saveCredentials(provider.id)}>
                        Сохранить
                      </button>
                      <button type="button" className="admin-btn" onClick={() => testConnection(provider.id)}>
                        Проверить
                      </button>
                    </div>
                  </div>
                ) : PUBLIC_API_PROVIDERS.has(provider.id) ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    <span className="muted">Публичный API</span>
                    <button type="button" className="admin-btn" onClick={() => testConnection(provider.id)}>
                      Проверить
                    </button>
                  </div>
                ) : (
                  <span className="muted">Скоро</span>
                )}
              </td>
              <td>
                {provider.last_sync_at || "—"}
                {provider.last_sync_status ? ` (${provider.last_sync_status})` : ""}
              </td>
              <td>
                <button
                  type="button"
                  className="admin-btn primary"
                  disabled={!provider.enabled}
                  onClick={() => sync(provider.id)}
                >
                  Синхронизация
                </button>
                <button
                  type="button"
                  className="admin-btn"
                  style={{ marginLeft: 6 }}
                  onClick={() => toggleEnabled(provider.id, !provider.enabled)}
                >
                  {provider.enabled ? "Выключить" : "Включить"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
