"use client";

import { useEffect } from "react";

const CHECK_INTERVAL_MS = 15_000;
const FETCH_TIMEOUT_MS = 5_000;

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
  const url = new URL(window.location.href);
  url.searchParams.set("_recover", String(Date.now()));
  window.location.replace(url.toString());
}

export function DeployCacheGuard() {
  useEffect(() => {
    const initialDeployId = currentDeployId();
    let timer: number | undefined;
    let inFlight = false;

    async function checkDeployId() {
      if (!initialDeployId || initialDeployId === "dev" || inFlight) return;
      if (document.visibilityState !== "visible") return;
      inFlight = true;

      try {
        const result = await pingDeployId(FETCH_TIMEOUT_MS);
        if (!result.ok) {
          if (navigator.onLine) hardReload();
          return;
        }

        if (result.id && result.id !== initialDeployId) {
          window.location.reload();
        }
      } finally {
        inFlight = false;
      }
    }

    const checkAfterIdle = () => void checkDeployId();
    const checkOnVisibility = () => {
      if (document.visibilityState === "visible") checkAfterIdle();
    };

    timer = window.setInterval(checkAfterIdle, CHECK_INTERVAL_MS);

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
