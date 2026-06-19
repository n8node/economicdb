"use client";

import { useEffect } from "react";

const RELOAD_FLAG = "macro_chunk_reload";
const DEPLOY_ID_KEY = "macro_deploy_id";

const CHUNK_ERROR =
  /Loading chunk|ChunkLoadError|Failed to fetch dynamically imported module|Importing a module script failed|error loading dynamically imported module/i;

function reloadOnce(reason: string) {
  if (sessionStorage.getItem(RELOAD_FLAG)) return;
  sessionStorage.setItem(RELOAD_FLAG, reason);
  window.location.reload();
}

function readDeployIdFromDom(): string | null {
  return document.querySelector('meta[name="deploy-id"]')?.getAttribute("content") ?? null;
}

function readDeployIdFromHtml(html: string): string | null {
  const match = html.match(/name="deploy-id"\s+content="([^"]+)"/i);
  return match?.[1] ?? null;
}

export function DeployCacheGuard() {
  useEffect(() => {
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
        window.location.reload();
        return;
      }
      sessionStorage.setItem(DEPLOY_ID_KEY, deployId);
    }

    const checkFreshDeployId = async () => {
      try {
        const response = await fetch(window.location.href, {
          cache: "no-store",
          headers: { Accept: "text/html" },
        });
        if (!response.ok) return;
        const html = await response.text();
        const remoteId = readDeployIdFromHtml(html);
        const localId = readDeployIdFromDom();
        if (remoteId && localId && remoteId !== localId) {
          sessionStorage.setItem(DEPLOY_ID_KEY, remoteId);
          sessionStorage.removeItem(RELOAD_FLAG);
          window.location.reload();
        }
      } catch {
        // ignore network errors during deploy window
      }
    };

    window.addEventListener("error", onError, true);
    window.addEventListener("unhandledrejection", onRejection);
    window.addEventListener("focus", checkFreshDeployId);
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "visible") {
        void checkFreshDeployId();
      }
    });

    const timer = window.setTimeout(() => sessionStorage.removeItem(RELOAD_FLAG), 8000);
    const interval = window.setInterval(checkFreshDeployId, 120_000);

    return () => {
      window.removeEventListener("error", onError, true);
      window.removeEventListener("unhandledrejection", onRejection);
      window.removeEventListener("focus", checkFreshDeployId);
      window.clearTimeout(timer);
      window.clearInterval(interval);
    };
  }, []);

  return null;
}
