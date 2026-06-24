"use client";

import { useEffect } from "react";

const CHECK_INTERVAL_MS = 60_000;
const STALE_FAILURE_GRACE_MS = 10 * 60_000;

function currentDeployId() {
  return document.querySelector<HTMLMetaElement>('meta[name="deploy-id"]')?.content || "";
}

export function DeployCacheGuard() {
  useEffect(() => {
    const initialDeployId = currentDeployId();
    let lastSuccessfulCheck = Date.now();
    let timer: number | undefined;
    let inFlight = false;

    async function checkDeployId({ reloadOnFailure = false } = {}) {
      if (!initialDeployId || initialDeployId === "dev" || inFlight) return;
      inFlight = true;

      try {
        const response = await fetch(`/deploy-id?t=${Date.now()}`, {
          cache: "no-store",
          credentials: "same-origin",
        });
        if (!response.ok) return;

        const data = (await response.json()) as { id?: string };
        lastSuccessfulCheck = Date.now();

        if (data.id && data.id !== initialDeployId) {
          window.location.reload();
        }
      } catch {
        const staleFor = Date.now() - lastSuccessfulCheck;
        if (reloadOnFailure && staleFor > STALE_FAILURE_GRACE_MS && navigator.onLine) {
          window.location.reload();
        }
      } finally {
        inFlight = false;
      }
    }

    const checkOnFocus = () => void checkDeployId({ reloadOnFailure: true });
    const checkOnVisibility = () => {
      if (document.visibilityState === "visible") checkOnFocus();
    };

    timer = window.setInterval(() => {
      if (document.visibilityState === "visible") void checkDeployId();
    }, CHECK_INTERVAL_MS);

    window.addEventListener("focus", checkOnFocus);
    window.addEventListener("pageshow", checkOnFocus);
    document.addEventListener("visibilitychange", checkOnVisibility);

    return () => {
      if (timer) window.clearInterval(timer);
      window.removeEventListener("focus", checkOnFocus);
      window.removeEventListener("pageshow", checkOnFocus);
      document.removeEventListener("visibilitychange", checkOnVisibility);
    };
  }, []);

  return null;
}
