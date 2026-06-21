"use client";

import { useCallback, useEffect, useState } from "react";
import { adminAuthFetch } from "@/lib/auth";

type OpenRouterSettings = {
  base_url: string;
  has_api_key: boolean;
  model_digest: string | null;
  model_fallback: string | null;
  last_test_at: string | null;
  last_test_status: string | null;
};

type OpenRouterModel = {
  id: string;
  name: string;
  label: string;
};

const DEFAULT_BASE_URL = "https://openrouter.ai/api/v1";

function connectionStatus(settings: OpenRouterSettings | null) {
  if (!settings) return { className: "idle", label: "Не проверен" };
  if (settings.last_test_status === "ok") return { className: "ok", label: "Подключение успешно" };
  if (settings.last_test_status === "error") return { className: "error", label: "Ошибка подключения" };
  return { className: "idle", label: "Не проверен" };
}

export function SettingsPanel() {
  const [settings, setSettings] = useState<OpenRouterSettings | null>(null);
  const [models, setModels] = useState<OpenRouterModel[]>([]);
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState(DEFAULT_BASE_URL);
  const [modelDigest, setModelDigest] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loadingModels, setLoadingModels] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);

  const loadSettings = useCallback(async () => {
    const data = await adminAuthFetch<OpenRouterSettings>("/admin/settings/openrouter");
    setSettings(data);
    setBaseUrl(data.base_url || DEFAULT_BASE_URL);
    setModelDigest(data.model_digest || "");
    return data;
  }, []);

  const loadModels = useCallback(
    async (inlineKey?: string) => {
      setLoadingModels(true);
      setError("");
      try {
        const payload =
          inlineKey?.trim() || apiKey.trim()
            ? await adminAuthFetch<{ items: OpenRouterModel[] }>("/admin/settings/openrouter/models", {
                method: "POST",
                body: JSON.stringify({
                  api_key: inlineKey?.trim() || apiKey.trim() || undefined,
                  base_url: baseUrl.trim() || undefined,
                }),
              })
            : await adminAuthFetch<{ items: OpenRouterModel[] }>("/admin/settings/openrouter/models");
        setModels(payload.items);
      } catch {
        setModels([]);
        setError("Не удалось загрузить список моделей OpenRouter");
      } finally {
        setLoadingModels(false);
      }
    },
    [apiKey, baseUrl],
  );

  useEffect(() => {
    loadSettings()
      .then((data) => {
        if (data.has_api_key && data.last_test_status === "ok") {
          return loadModels();
        }
        return undefined;
      })
      .catch(() => setError("Не удалось загрузить настройки OpenRouter"));
  }, [loadSettings, loadModels]);

  async function saveSettings() {
    setSaving(true);
    setMessage("");
    setError("");
    try {
      const body: Record<string, string> = {
        base_url: baseUrl.trim() || DEFAULT_BASE_URL,
      };
      if (apiKey.trim()) body.api_key = apiKey.trim();
      if (modelDigest.trim()) body.model_digest = modelDigest.trim();

      const data = await adminAuthFetch<OpenRouterSettings>("/admin/settings/openrouter", {
        method: "PUT",
        body: JSON.stringify(body),
      });
      setSettings(data);
      setApiKey("");
      setMessage("Настройки OpenRouter сохранены");
    } catch {
      setError("Не удалось сохранить настройки");
    } finally {
      setSaving(false);
    }
  }

  async function testConnection() {
    setTesting(true);
    setMessage("");
    setError("");
    try {
      const result = await adminAuthFetch<{
        ok: boolean;
        message?: string;
        error?: string;
        models_count?: number;
      }>("/admin/settings/openrouter/test", {
        method: "POST",
        body: JSON.stringify({
          api_key: apiKey.trim() || undefined,
          base_url: baseUrl.trim() || undefined,
        }),
      });
      await loadSettings();
      if (!result.ok) {
        setError(result.message || result.error || "Ошибка подключения");
        return;
      }
      setMessage(result.message || "Подключение успешно");
      await loadModels(apiKey.trim() || undefined);
    } catch {
      setError("Ошибка проверки подключения");
    } finally {
      setTesting(false);
    }
  }

  const status = connectionStatus(settings);

  return (
    <div className="admin-settings-page">
      <h1 style={{ marginTop: 0 }}>LLM подключение</h1>
      <p className="muted" style={{ maxWidth: 760 }}>
        Все LLM-запросы продукта идут через OpenRouter. Ключ хранится в PostgreSQL в зашифрованном виде.
      </p>

      {error ? <p className="admin-error">{error}</p> : null}
      {message ? <p className="muted">{message}</p> : null}

      <section className="admin-settings-card">
        <div className="admin-settings-card-head">
          <div>
            <h2>OpenRouter</h2>
            <p className="muted">Все LLM-запросы идут через OpenRouter</p>
          </div>
          <span className="provider-status">
            <span className={`provider-status-dot ${status.className}`} />
            <span>{status.label}</span>
          </span>
        </div>

        <label className="admin-settings-label" htmlFor="openrouter-base-url">
          API Base URL
        </label>
        <input
          id="openrouter-base-url"
          className="admin-input"
          value={baseUrl}
          onChange={(event) => setBaseUrl(event.target.value)}
        />

        <label className="admin-settings-label" htmlFor="openrouter-api-key">
          API Key
        </label>
        <input
          id="openrouter-api-key"
          className="admin-input"
          type="password"
          placeholder={settings?.has_api_key ? "Ключ сохранён · введите новый, чтобы заменить" : "sk-or-..."}
          value={apiKey}
          onChange={(event) => setApiKey(event.target.value)}
        />
        <p className="muted admin-settings-help">
          Тест использует значение из поля, если оно заполнено. Иначе — сохранённый ключ.
        </p>

        <div className="admin-settings-actions">
          <button type="button" className="admin-btn" onClick={() => void testConnection()} disabled={testing}>
            <i className="ti ti-wand" /> {testing ? "Проверка…" : "Тестировать соединение"}
          </button>
          <button type="button" className="admin-btn primary" onClick={() => void saveSettings()} disabled={saving}>
            {saving ? "Сохранение…" : "Сохранить ключ и URL"}
          </button>
        </div>
        {settings?.last_test_at ? <p className="muted">Последняя проверка: {settings.last_test_at}</p> : null}
      </section>

      <section className="admin-settings-card">
        <div className="admin-settings-card-head">
          <div>
            <h2>Модели OpenRouter</h2>
            <p className="muted">
              После успешного теста выберите модели из списка, доступного в вашем регионе
            </p>
          </div>
        </div>

        <label className="admin-settings-label" htmlFor="openrouter-model-digest">
          Сводка
        </label>
        {loadingModels ? (
          <p className="muted">Загрузка моделей…</p>
        ) : models.length === 0 ? (
          <p className="muted">Сначала проверьте подключение — список моделей появится после успешного теста.</p>
        ) : (
          <select
            id="openrouter-model-digest"
            className="admin-input"
            value={modelDigest}
            onChange={(event) => setModelDigest(event.target.value)}
          >
            <option value="">Выберите модель</option>
            {models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.label}
              </option>
            ))}
          </select>
        )}
        <p className="muted admin-settings-help">Используется для AI-сводки (weekly digest)</p>

        <div className="admin-settings-actions">
          <button
            type="button"
            className="admin-btn primary"
            onClick={() => void saveSettings()}
            disabled={saving || !modelDigest.trim()}
          >
            {saving ? "Сохранение…" : "Сохранить модель для сводки"}
          </button>
          <button type="button" className="admin-btn" onClick={() => void loadModels()} disabled={loadingModels}>
            Обновить список моделей
          </button>
        </div>
      </section>
    </div>
  );
}
