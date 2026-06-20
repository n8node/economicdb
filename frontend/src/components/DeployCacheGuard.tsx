"use client";

import { useEffect } from "react";

const RELOAD_FLAG = "macro_chunk_reload";
const DEPLOY_ID_KEY = "macro_deploy_id";
const CHECK_COOLDOWN_MS = 60_000;

const CHUNK_ERROR =
  /Loading chunk|ChunkLoadError|Failed to fetch dynamically imported module|Importing a module script failed|error loading dynamically imported module/i;

function reloadOnce(reason: string) {
  if (sessionStorage.getItem(RELOAD_FLAG)) return;
  sessionStorage.setItem(RELOAD_FLAG, reason);
  const url = new URL(window.location.href);
  url.searchParams.set("_", Date.now().toString());
  window.location.replace(url.toString());
}

function readDeployIdFromDom(): string | null {
  return document.querySelector('meta[name="deploy-id"]')?.getAttribute("content") ?? null;
}

export function DeployCacheGuard() {
  useEffect(() => {
    let lastCheckAt = 0;
    let checking = false;

    const onError = (event: ErrorEvent) => {
      const target = event.target;
      if (target instanceof HTMLScriptElement || target instanceof HTMLLinkElement) {
        reloadOnce("asset");
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

    const deployId = readDeployIdFromDom();
    if (deployId) {
      const stored = sessionStorage.getItem(DEPLOY_ID_KEY);
      if (stored && stored !== deployId) {
        sessionStorage.setItem(DEPLOY_ID_KEY, deployId);
        sessionStorage.removeItem(RELOAD_FLAG);
        reloadOnce("deploy");
        return;
      }
      sessionStorage.setItem(DEPLOY_ID_KEY, deployId);
    }

    const checkFreshDeployId = async () => {
      const now = Date.now();
      if (checking || now - lastCheckAt < CHECK_COOLDOWN_MS) return;
      checking = true;
      lastCheckAt = now;

      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), 5000);

      try {
        const response = await fetch("/deploy-id", {
          cache: "no-store",
          signal: controller.signal,
        });
        if (!response.ok) return;
        const payload = (await response.json()) as { id?: string };
        const remoteId = payload.id ?? null;
        const localId = readDeployIdFromDom();
        if (remoteId && localId && remoteId !== localId) {
          sessionStorage.setItem(DEPLOY_ID_KEY, remoteId);
          sessionStorage.removeItem(RELOAD_FLAG);
          reloadOnce("deploy-remote");
        }
      } catch {
        // ignore transient network errors
      } finally {
        window.clearTimeout(timeout);
        checking = false;
      }
    };

    const onVisibility = () => {
      if (document.visibilityState === "visible") {
        void checkFreshDeployId();
      }
    };

    window.addEventListener("error", onError, true);
    window.addEventListener("unhandledrejection", onRejection);
    document.addEventListener("visibilitychange", onVisibility);

    const timer = window.setTimeout(() => sessionStorage.removeItem(RELOAD_FLAG), 8000);

    return () => {
      window.removeEventListener("error", onError, true);
      window.removeEventListener("unhandledrejection", onRejection);
      document.removeEventListener("visibilitychange", onVisibility);
      window.clearTimeout(timer);
    };
  }, []);

  return null;
}
