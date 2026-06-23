export function getApiBase(): string {
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_URL || "/api/v1";
  }
  const internal = process.env.INTERNAL_API_URL;
  if (internal) {
    return `${internal.replace(/\/$/, "")}/api/v1`;
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://backend:8080/api/v1";
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const base = getApiBase();
  const url = `${base.replace(/\/$/, "")}${path.startsWith("/") ? path : `/${path}`}`;
  const response = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let message = `API ${response.status}`;
    try {
      const data = (await response.json()) as { detail?: string };
      if (data.detail) message = data.detail;
    } catch {
      // Keep the status-only message when the backend returns an empty body.
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}
