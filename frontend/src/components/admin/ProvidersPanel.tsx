"use client";

import { useEffect, useState } from "react";
import { adminAuthFetch } from "@/lib/auth";

type Provider = {
  id: string;
  name_ru: string;
  enabled: boolean;
  last_sync_at: string | null;
  last_sync_status: string | null;
};

export function ProvidersPanel() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [message, setMessage] = useState("");

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
      const result = await adminAuthFetch<{ ok: boolean; message?: string; error?: string }>(
        `/admin/providers/${id}/sync`,
        { method: "POST" },
      );
      setMessage(result.message || result.error || "Готово");
      await load();
    } catch {
      setMessage("Ошибка синхронизации");
    }
  }

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Провайдеры данных</h1>
      {message ? <p className="muted">{message}</p> : null}
      <table className="admin-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Название</th>
            <th>Статус</th>
            <th>Последняя синхронизация</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {providers.map((provider) => (
            <tr key={provider.id}>
              <td>{provider.id}</td>
              <td>{provider.name_ru}</td>
              <td>{provider.enabled ? "Включён" : "Выключен"}</td>
              <td>{provider.last_sync_at || "—"}</td>
              <td>
                <button type="button" className="admin-btn primary" onClick={() => sync(provider.id)}>
                  Sync
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
