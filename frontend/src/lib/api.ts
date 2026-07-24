import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "./token-store";
import type {
  Alert,
  AlertStatus,
  AnalyticsReport,
  AuditLog,
  DashboardMetrics,
  Page,
  Role,
  Severity,
  SessionInfo,
  User,
} from "./types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_V1 = `${API_BASE_URL}/api/v1`;

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

let refreshPromise: Promise<boolean> | null = null;

async function doRefresh(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;
  const res = await fetch(`${API_V1}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res.ok) {
    clearTokens();
    return false;
  }
  const data = await res.json();
  setTokens(data.access_token, data.refresh_token);
  return true;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  { auth = true, retry = true }: { auth?: boolean; retry?: boolean } = {}
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (auth) {
    const token = getAccessToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${API_V1}${path}`, { ...options, headers });

  if (res.status === 401 && auth && retry) {
    refreshPromise ??= doRefresh().finally(() => {
      refreshPromise = null;
    });
    const refreshed = await refreshPromise;
    if (refreshed) {
      return request<T>(path, options, { auth, retry: false });
    }
  }

  if (res.status === 204) return undefined as T;

  const text = await res.text();
  const data = text ? JSON.parse(text) : undefined;

  if (!res.ok) {
    const message =
      typeof data?.detail === "string"
        ? data.detail
        : Array.isArray(data?.detail)
        ? data.detail.map((d: { msg: string }) => d.msg).join("; ")
        : "Request failed";
    throw new ApiError(message, res.status);
  }

  return data as T;
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------
export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  mfa_required: boolean;
}

export async function login(email: string, password: string, mfaCode?: string) {
  return request<TokenPair>(
    "/auth/login",
    { method: "POST", body: JSON.stringify({ email, password, mfa_code: mfaCode }) },
    { auth: false }
  );
}

export async function register(email: string, fullName: string, password: string) {
  return request<User>(
    "/auth/register",
    { method: "POST", body: JSON.stringify({ email, full_name: fullName, password }) },
    { auth: false }
  );
}

export async function logout() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return;
  await request<void>("/auth/logout", { method: "POST", body: JSON.stringify({ refresh_token: refreshToken }) });
}

export async function fetchMe() {
  return request<User>("/auth/me");
}

export async function forgotPassword(email: string) {
  return request<void>("/auth/forgot-password", { method: "POST", body: JSON.stringify({ email }) }, { auth: false });
}

export async function resetPassword(token: string, newPassword: string) {
  return request<void>(
    "/auth/reset-password",
    { method: "POST", body: JSON.stringify({ token, new_password: newPassword }) },
    { auth: false }
  );
}

export async function verifyEmail(token: string) {
  return request<void>("/auth/verify-email", { method: "POST", body: JSON.stringify({ token }) }, { auth: false });
}

export async function mfaSetup() {
  return request<{ secret: string; otpauth_url: string }>("/auth/mfa/setup", { method: "POST" });
}

export async function mfaEnable(code: string) {
  return request<void>("/auth/mfa/enable", { method: "POST", body: JSON.stringify({ code }) });
}

export async function mfaDisable(code: string) {
  return request<void>("/auth/mfa/disable", { method: "POST", body: JSON.stringify({ code }) });
}

export async function listSessions() {
  return request<SessionInfo[]>("/auth/sessions");
}

export async function revokeSession(id: string) {
  return request<void>(`/auth/sessions/${id}`, { method: "DELETE" });
}

// ---------------------------------------------------------------------------
// Users
// ---------------------------------------------------------------------------
export async function listUsers(params: { page?: number; page_size?: number; search?: string; role?: string }) {
  const qs = new URLSearchParams();
  if (params.page) qs.set("page", String(params.page));
  if (params.page_size) qs.set("page_size", String(params.page_size));
  if (params.search) qs.set("search", params.search);
  if (params.role) qs.set("role", params.role);
  return request<Page<User>>(`/users?${qs.toString()}`);
}

export async function createUser(payload: { email: string; full_name: string; password: string; role: Role }) {
  return request<User>("/users", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateUser(
  id: string,
  payload: Partial<{ full_name: string; role: Role; is_active: boolean }>
) {
  return request<User>(`/users/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function deleteUser(id: string) {
  return request<void>(`/users/${id}`, { method: "DELETE" });
}

export async function adminResetPassword(id: string, newPassword: string) {
  return request<void>(`/users/${id}/reset-password`, {
    method: "POST",
    body: JSON.stringify({ new_password: newPassword }),
  });
}

// ---------------------------------------------------------------------------
// Logs
// ---------------------------------------------------------------------------
export async function listLogs(params: {
  page?: number;
  page_size?: number;
  search?: string;
  category?: string;
  status?: string;
}) {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== "") qs.set(k, String(v));
  });
  return request<Page<AuditLog>>(`/logs?${qs.toString()}`);
}

// ---------------------------------------------------------------------------
// Alerts
// ---------------------------------------------------------------------------
export async function listAlerts(params: {
  page?: number;
  page_size?: number;
  severity?: string;
  category?: string;
  status?: string;
  search?: string;
}) {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== "") qs.set(k, String(v));
  });
  return request<Page<Alert>>(`/alerts?${qs.toString()}`);
}

export async function createAlert(payload: {
  severity: Severity;
  category: string;
  description: string;
  user_id?: string;
  source_ip?: string;
}) {
  return request<Alert>("/alerts", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateAlert(
  id: string,
  payload: Partial<{ status: AlertStatus; notes: string; severity: Severity }>
) {
  return request<Alert>(`/alerts/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

// ---------------------------------------------------------------------------
// Dashboard / analytics
// ---------------------------------------------------------------------------
export async function getMetrics() {
  return request<DashboardMetrics>("/metrics");
}

export async function getAnalytics(days = 7) {
  return request<AnalyticsReport>(`/analytics?days=${days}`);
}

// ---------------------------------------------------------------------------
// AI analyst
// ---------------------------------------------------------------------------
export async function askAiAnalyst(question: string, alertId?: string) {
  return request<{ answer: string; model: string; context_used: Record<string, unknown> }>("/ai/query", {
    method: "POST",
    body: JSON.stringify({ question, alert_id: alertId }),
  });
}
