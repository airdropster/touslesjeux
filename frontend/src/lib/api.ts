// KNOWN LIMITATION: API key is exposed in client-side code. This is acceptable
// for a local/internal tool. For public deployment, replace with session-based
// auth (e.g., login flow that sets an httpOnly cookie).
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const API_KEY = import.meta.env.VITE_API_KEY || "changeme";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
      ...options.headers,
    },
  });
  if (!resp.ok) {
    const error = await resp.json().catch(() => ({ error: { message: resp.statusText } }));
    throw new Error(error.error?.message || resp.statusText);
  }
  return resp.json();
}

export const api = {
  // Games
  getGames: (params: string = "") => request<any>(`/api/games?${params}`),
  getGame: (id: number) => request<any>(`/api/games/${id}`),
  createGame: (data: any) => request<any>("/api/games", { method: "POST", body: JSON.stringify(data) }),
  updateGame: (id: number, data: any) => request<any>(`/api/games/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteGame: (id: number) => request<any>(`/api/games/${id}`, { method: "DELETE" }),
  reprocessGame: (id: number) => request<any>(`/api/games/${id}/reprocess`, { method: "POST" }),
  getGamesStats: () => request<any>("/api/games/stats"),
  exportGames: (params: string = "") => request<any[]>(`/api/games/export?${params}`),

  // Collections
  launchCollection: (data: { categories: string[]; target_count: number }) =>
    request<any>("/api/collections/launch", { method: "POST", body: JSON.stringify(data) }),
  getCollections: (params: string = "") => request<any>(`/api/collections?${params}`),
  getCollection: (id: number) => request<any>(`/api/collections/${id}`),
  cancelCollection: (id: number) => request<any>(`/api/collections/${id}/cancel`, { method: "POST" }),

  // SSE URL (not a fetch call — pass API key via query param since EventSource can't send headers)
  getStreamUrl: (id: number) => `${API_BASE}/api/collections/${id}/stream?api_key=${encodeURIComponent(API_KEY)}`,
};
