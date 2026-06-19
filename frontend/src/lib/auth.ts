const TOKEN_KEY = "macro_admin_token";

export type AdminUser = {
  id: number;
  email: string;
  role: string;
};

export function getAdminToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setAdminToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearAdminToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export async function adminLogin(email: string, password: string): Promise<AdminUser> {
  const { apiFetch, getApiBase } = await import("./api");
  const data = await apiFetch<{
    access_token: string;
    admin: AdminUser;
  }>("/admin/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setAdminToken(data.access_token);
  return data.admin;
}

export async function fetchAdminMe(): Promise<AdminUser | null> {
  const token = getAdminToken();
  if (!token) return null;

  const { getApiBase } = await import("./api");
  const response = await fetch(`${getApiBase()}/admin/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });

  if (!response.ok) {
    clearAdminToken();
    return null;
  }

  return response.json() as Promise<AdminUser>;
}

export async function adminAuthFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAdminToken();
  if (!token) throw new Error("unauthorized");

  const { getApiBase } = await import("./api");
  const url = `${getApiBase().replace(/\/$/, "")}${path.startsWith("/") ? path : `/${path}`}`;
  const response = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...init?.headers,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    if (response.status === 401) clearAdminToken();
    throw new Error(`API ${response.status}`);
  }

  return response.json() as Promise<T>;
}
