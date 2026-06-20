"use client";

import { useEffect } from "react";

const RELOAD_FLAG = "macro_chunk_reload";
const RELOAD_COUNT_KEY = "macro_reload_count";
const DEPLOY_ID_KEY = "macro_deploy_id";
const CHECK_COOLDOWN_MS = 60_000;
const MAX_RELOADS = 3;

const CHUNK_ERROR =
  /Loading chunk|ChunkLoadError|Failed to fetch dynamically imported module|Importing a module script failed|error loading dynamically imported module/i;

function reloadOnce(reason: string) {
  const count = Number(sessionStorage.getItem(RELOAD_COUNT_KEY) || "0");
  if (count >= MAX_RELOADS) return;
  sessionStorage.setItem(RELOAD_COUNT_KEY, String(count + 1));
  sessionStorage.setItem(RELOAD_FLAG, reason);
  const url = new URL(window.location.href);
  url.searchParams.set("_", Date.now().toString());
  window.location.replace(url.toString());
}

function isNextStaticScript(target: EventTarget | null): target is HTMLScriptElement {
  return (
    target instanceof HTMLScriptElement &&
    typeof target.src === "string" &&
    target.src.includes("/_next/static/")
  );
}

async function fetchDeployId(signal: AbortSignal): Promise<string | null> {
  const response = await fetch("/deploy-id", { cache: "no-store", signal });
  if (!response.ok) return null;
  const payload = (await response.json()) as { id?: string };
  return payload.id ?? null;
}

function markDeploySynced(deployId: string) {
  sessionStorage.setItem(DEPLOY_ID_KEY, deployId);
  sessionStorage.removeItem(RELOAD_COUNT_KEY);
  sessionStorage.removeItem(RELOAD_FLAG);
}

export function DeployCacheGuard() {
  useEffect(() => {
    let lastCheckAt = 0;
    let checking = false;

    const onError = (event: ErrorEvent) => {
      if (isNextStaticScript(event.target)) {
        reloadOnce("chunk");
        return;
      }
      if (CHUNK_ERROR.test(event.message || "")) {
        reloadOnce("chunk");
      }
    };

    const onRejection = (event: PromiseRejectionEvent) => {
      const reason = event.reason;
      const message = reason instanceof Error ? reason.message : String(reason ?? "");
      if (CHUNK_ERROR.test(message)) {
        event.preventDefault();
        reloadOnce("import");
      }
    };

    const syncDeployId = async () => {
      const now = Date.now();
      if (checking || now - lastCheckAt < CHECK_COOLDOWN_MS) return;
      checking = true;
      lastCheckAt = now;

      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), 5000);

      try {
        const remoteId = await fetchDeployId(controller.signal);
        if (!remoteId) return;

        const stored = sessionStorage.getItem(DEPLOY_ID_KEY);
        if (stored && stored !== remoteId) {
          sessionStorage.setItem(DEPLOY_ID_KEY, remoteId);
          reloadOnce("deploy");
          return;
        }

        markDeploySynced(remoteId);
      } catch {
        // ignore transient network errors
      } finally {
        window.clearTimeout(timeout);
        checking = false;
      }
    };

    const onVisibility = () => {
      if (document.visibilityState === "visible") {
        void syncDeployId();
      }
    };

    void syncDeployId();

    window.addEventListener("error", onError, true);
    window.addEventListener("unhandledrejection", onRejection);
    document.addEventListener("visibilitychange", onVisibility);

    return () => {
      window.removeEventListener("error", onError, true);
      window.removeEventListener("unhandledrejection", onRejection);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, []);

  return null;
}
