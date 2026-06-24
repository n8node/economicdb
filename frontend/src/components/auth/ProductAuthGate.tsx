"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  fetchUserMe,
  getUserToken,
  readCachedUser,
  type AppUser,
} from "@/lib/auth";
import { ProductShell } from "@/components/layout/ProductShell";
import { NetworkStaleBanner } from "@/components/NetworkStaleBanner";

const AUTH_PATHS = new Set(["/app/login", "/app/register"]);

export function ProductAuthGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isAuthPath = AUTH_PATHS.has(pathname);
  const hasToken = Boolean(getUserToken());

  const [user, setUser] = useState<AppUser | null>(() => (hasToken ? readCachedUser() : null));
  const [checking, setChecking] = useState(() => hasToken && !isAuthPath && !readCachedUser());
  const [networkStale, setNetworkStale] = useState(false);

  useEffect(() => {
    const onStale = () => setNetworkStale(true);
    window.addEventListener("macro:network-stale", onStale);
    return () => window.removeEventListener("macro:network-stale", onStale);
  }, []);

  useEffect(() => {
    if (isAuthPath) return;

    if (!hasToken) {
      const next = `${pathname}${window.location.search}`;
      router.replace(`/app/login?next=${encodeURIComponent(next)}`);
      return;
    }

    let active = true;

    fetchUserMe()
      .then((nextUser) => {
        if (!active) return;
        if (!nextUser) {
          const next = `${pathname}${window.location.search}`;
          router.replace(`/app/login?next=${encodeURIComponent(next)}`);
          return;
        }
        setUser(nextUser);
        setNetworkStale(false);
      })
      .catch(() => {
        if (!active) return;
        if (!readCachedUser()) {
          router.replace("/app/login");
          return;
        }
        setNetworkStale(true);
      })
      .finally(() => {
        if (active) setChecking(false);
      });

    return () => {
      active = false;
    };
  }, [hasToken, isAuthPath, pathname, router]);

  if (isAuthPath) return <>{children}</>;

  if (checking && !user) {
    return (
      <main className="auth-page">
        <div className="auth-card auth-card--status">Проверяем сессию…</div>
      </main>
    );
  }

  if (!user) {
    return (
      <main className="auth-page">
        <div className="auth-card auth-card--status">Проверяем сессию…</div>
      </main>
    );
  }

  return (
    <>
      {networkStale ? <NetworkStaleBanner /> : null}
      <ProductShell user={user}>{children}</ProductShell>
    </>
  );
}
