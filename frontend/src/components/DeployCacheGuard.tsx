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

    const deployId = document.querySelector('meta[name="deploy-id"]')?.getAttribute("content");
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

    window.addEventListener("error", onError, true);
    window.addEventListener("unhandledrejection", onRejection);

    const timer = window.setTimeout(() => sessionStorage.removeItem(RELOAD_FLAG), 8000);

    return () => {
      window.removeEventListener("error", onError, true);
      window.removeEventListener("unhandledrejection", onRejection);
      window.clearTimeout(timer);
    };
  }, []);

  return null;
}
