"use client";

import { useCallback, useEffect, useState } from "react";

const CHECK_INTERVAL_MS = 90_000;
const FETCH_TIMEOUT_MS = 8_000;
const FAILURES_BEFORE_STALE = 2;

type StaleReason = "network" | "deploy";

function currentDeployId() {
  return document.querySelector<HTMLMetaElement>('meta[name="deploy-id"]')?.content || "";
}

async function pingDeployId(timeoutMs: number): Promise<{ ok: true; id?: string } | { ok: false }> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`/deploy-id?t=${Date.now()}`, {
      cache: "no-store",
      credentials: "same-origin",
      signal: controller.signal,
    });
    if (!response.ok) return { ok: false };

    const data = (await response.json()) as { id?: string };
    return { ok: true, id: data.id };
  } catch {
    return { ok: false };
  } finally {
    window.clearTimeout(timer);
  }
}

function cleanRecoverUrl() {
  const url = new URL(window.location.href);
  if (!url.searchParams.has("_recover") && !url.searchParams.has("_fresh")) return;
  url.searchParams.delete("_recover");
  url.searchParams.delete("_fresh");
  window.history.replaceState(null, "", url.pathname + url.search + url.hash);
}

export function DeployCacheGuard() {
  const [stale, setStale] = useState<StaleReason | null>(null);

  const recover = useCallback(() => {
    window.location.href = `/app?_fresh=${Date.now()}`;
  }, []);

  useEffect(() => {
    cleanRecoverUrl();

    const initialDeployId = currentDeployId();
    if (!initialDeployId || initialDeployId === "dev") return;

    let timer: number | undefined;
    let inFlight = false;
    let consecutiveFailures = 0;

    async function checkSession() {
      if (inFlight || document.visibilityState !== "visible") return;
      inFlight = true;

      try {
        const result = await pingDeployId(FETCH_TIMEOUT_MS);
        if (!result.ok) {
          consecutiveFailures += 1;
          if (consecutiveFailures >= FAILURES_BEFORE_STALE) {
            setStale("network");
          }
          return;
        }

        consecutiveFailures = 0;
        setStale(null);

        if (result.id && result.id !== initialDeployId) {
          setStale("deploy");
        }
      } finally {
        inFlight = false;
      }
    }

    const onPageShow = (event: PageTransitionEvent) => {
      if (event.persisted) {
        setStale("network");
        return;
      }
      void checkSession();
    };

    const onVisibility = () => {
      if (document.visibilityState === "visible") void checkSession();
    };

    timer = window.setInterval(checkSession, CHECK_INTERVAL_MS);

    window.addEventListener("pageshow", onPageShow);
    document.addEventListener("visibilitychange", onVisibility);

    return () => {
      if (timer) window.clearInterval(timer);
      window.removeEventListener("pageshow", onPageShow);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, []);

  if (!stale) return null;

  const title = stale === "deploy" ? "Доступна новая версия" : "Сессия прервана";
  const hint =
    stale === "deploy"
      ? "Приложение обновилось. Нажмите кнопку, чтобы загрузить актуальную версию."
      : "Соединение с сервером устарело. Нажмите кнопку — это надёжнее автоматической перезагрузки на Windows.";

  return (
    <div className="session-stale-banner" role="alertdialog" aria-live="assertive" aria-labelledby="session-stale-title">
      <div className="session-stale-banner__card">
        <p id="session-stale-title" className="session-stale-banner__title">
          {title}
        </p>
        <p className="session-stale-banner__hint">{hint}</p>
        <button type="button" className="btn primary session-stale-banner__action" onClick={recover}>
          Обновить страницу
        </button>
      </div>
    </div>
  );
}
