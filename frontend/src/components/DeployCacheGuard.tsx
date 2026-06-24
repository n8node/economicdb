"use client";

import { useEffect } from "react";

const CHECK_INTERVAL_MS = 30_000;
const FETCH_TIMEOUT_MS = 8_000;
const BACKGROUND_STALE_MS = 90_000;

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

function hardReload() {
  window.location.assign(window.location.href);
}

export function DeployCacheGuard() {
  useEffect(() => {
    const initialDeployId = currentDeployId();
    let lastSuccessfulCheck = Date.now();
    let timer: number | undefined;
    let inFlight = false;

    async function checkDeployId({ reloadOnFailure = false, immediateOnFailure = false } = {}) {
      if (!initialDeployId || initialDeployId === "dev" || inFlight) return;
      inFlight = true;

      try {
        const result = await pingDeployId(FETCH_TIMEOUT_MS);
        if (!result.ok) {
          const staleFor = Date.now() - lastSuccessfulCheck;
          if (
            navigator.onLine &&
            (immediateOnFailure || (reloadOnFailure && staleFor > BACKGROUND_STALE_MS))
          ) {
            hardReload();
          }
          return;
        }

        lastSuccessfulCheck = Date.now();

        if (result.id && result.id !== initialDeployId) {
          window.location.reload();
        }
      } finally {
        inFlight = false;
      }
    }

    const checkAfterIdle = () => void checkDeployId({ reloadOnFailure: true, immediateOnFailure: true });
    const checkOnVisibility = () => {
      if (document.visibilityState === "visible") checkAfterIdle();
    };

    timer = window.setInterval(() => {
      if (document.visibilityState === "visible") void checkDeployId({ reloadOnFailure: true });
    }, CHECK_INTERVAL_MS);

    window.addEventListener("focus", checkAfterIdle);
    window.addEventListener("pageshow", checkAfterIdle);
    document.addEventListener("visibilitychange", checkOnVisibility);

    return () => {
      if (timer) window.clearInterval(timer);
      window.removeEventListener("focus", checkAfterIdle);
      window.removeEventListener("pageshow", checkAfterIdle);
      document.removeEventListener("visibilitychange", checkOnVisibility);
    };
  }, []);

  return null;
}
