import type { DashboardPayload } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function resolveApiUrl(path: string): string {
  if (API_BASE.startsWith("http://") || API_BASE.startsWith("https://")) {
    return new URL(path, API_BASE).toString();
  }
  return new URL(`${API_BASE.replace(/\/$/, "")}${path}`, window.location.origin).toString();
}

function resolveSocketUrl(path: string): string {
  if (API_BASE.startsWith("http://") || API_BASE.startsWith("https://")) {
    const apiBase = new URL(API_BASE);
    const protocol = apiBase.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${apiBase.host}${path}`;
  }

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const normalizedBase = API_BASE.startsWith("/") ? API_BASE : `/${API_BASE}`;
  return `${protocol}//${window.location.host}${normalizedBase.replace(/\/$/, "")}${path}`;
}

export async function fetchDashboard(): Promise<DashboardPayload> {
  const response = await fetch(resolveApiUrl("/api/dashboard"));
  if (!response.ok) {
    throw new Error("Failed to load dashboard data");
  }
  return response.json() as Promise<DashboardPayload>;
}

export async function approveAction(actionId: number): Promise<void> {
  const response = await fetch(resolveApiUrl(`/api/actions/${actionId}/approve`), {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error("Failed to approve action");
  }
}

export function createDashboardSocket(onMessage: (payload: DashboardPayload) => void): WebSocket {
  const socket = new WebSocket(resolveSocketUrl("/ws/dashboard"));
  socket.onmessage = (event) => {
    onMessage(JSON.parse(event.data) as DashboardPayload);
  };
  return socket;
}
