export type Role = "admin" | "security_analyst" | "auditor" | "user";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  is_email_verified: boolean;
  mfa_enabled: boolean;
  last_login_at: string | null;
  created_at: string;
  threat_score: number;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface AuditLog {
  id: string;
  user_id: string | null;
  user_email: string | null;
  action: string;
  category: string;
  status: "successful" | "failed";
  ip_address: string | null;
  device: string | null;
  browser: string | null;
  details: string | null;
  created_at: string;
}

export type Severity = "low" | "medium" | "high" | "critical";
export type AlertStatus = "open" | "investigating" | "resolved" | "dismissed";

export interface Alert {
  id: string;
  severity: Severity;
  category: string;
  description: string;
  user_id: string | null;
  source_ip: string | null;
  status: AlertStatus;
  notes: string | null;
  created_at: string;
}

export interface DashboardMetrics {
  total_users: number;
  active_sessions: number;
  successful_logins_24h: number;
  failed_logins_24h: number;
  security_score: number;
  threat_level: Severity;
  open_alerts: number;
  api_requests_24h: number;
  suspicious_events_24h: number;
}

export interface TimeSeriesPoint {
  label: string;
  value: number;
}

export interface CategoryCount {
  category: string;
  count: number;
}

export interface AnalyticsReport {
  daily_login_activity: TimeSeriesPoint[];
  failed_login_trend: TimeSeriesPoint[];
  security_incidents: TimeSeriesPoint[];
  threat_categories: CategoryCount[];
  alert_severity_breakdown: CategoryCount[];
  system_performance: TimeSeriesPoint[];
}

export interface SessionInfo {
  id: string;
  ip_address: string | null;
  user_agent: string | null;
  device: string | null;
  created_at: string;
  expires_at: string;
  revoked: boolean;
}
