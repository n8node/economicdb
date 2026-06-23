const TOKEN_KEY = "macro_admin_token";
const USER_TOKEN_KEY = "macro_user_token";

export type AdminUser = {
  id: number;
  email: string;
  role: string;
};

export type AppUser = {
  id: number;
  email: string;
  email_verified: boolean;
  created_at: string;
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

export function getUserToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(USER_TOKEN_KEY);
}

export function setUserToken(token: string): void {
  localStorage.setItem(USER_TOKEN_KEY, token);
}

export function clearUserToken(): void {
  localStorage.removeItem(USER_TOKEN_KEY);
}

type UserAuthPayload = {
  access_token: string;
  user: AppUser;
};

export async function registerUser(email: string, password: string): Promise<AppUser> {
  const { apiFetch } = await import("./api");
  const data = await apiFetch<UserAuthPayload>("/auth/register", {
    method: "POST",
    body: JSON.stringify({
      email,
      password,
      personal_data_consent: true,
    }),
  });
  setUserToken(data.access_token);
  return data.user;
}

export async function loginUser(email: string, password: string): Promise<AppUser> {
  const { apiFetch } = await import("./api");
  const data = await apiFetch<UserAuthPayload>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setUserToken(data.access_token);
  return data.user;
}

export async function fetchUserMe(): Promise<AppUser | null> {
  const token = getUserToken();
  if (!token) return null;

  const { getApiBase } = await import("./api");
  const response = await fetch(`${getApiBase()}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });

  if (!response.ok) {
    clearUserToken();
    return null;
  }

  return response.json() as Promise<AppUser>;
}
