"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { fetchUserMe, type AppUser } from "@/lib/auth";
import { ProductShell } from "@/components/layout/ProductShell";

const AUTH_PATHS = new Set(["/app/login", "/app/register"]);

export function ProductAuthGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<AppUser | null>(null);
  const [checking, setChecking] = useState(true);
  const isAuthPath = AUTH_PATHS.has(pathname);

  useEffect(() => {
    if (isAuthPath) {
      setChecking(false);
      return;
    }

    let active = true;
    setChecking(true);
    fetchUserMe()
      .then((nextUser) => {
        if (!active) return;
        if (!nextUser) {
          const next = `${pathname}${window.location.search}`;
          router.replace(`/app/login?next=${encodeURIComponent(next)}`);
          return;
        }
        setUser(nextUser);
      })
      .finally(() => {
        if (active) setChecking(false);
      });

    return () => {
      active = false;
    };
  }, [isAuthPath, pathname, router]);

  if (isAuthPath) return <>{children}</>;

  if (checking || !user) {
    return (
      <main className="auth-page">
        <div className="auth-card auth-card--status">Проверяем сессию…</div>
      </main>
    );
  }

  return <ProductShell user={user}>{children}</ProductShell>;
}
