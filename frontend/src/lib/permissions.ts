import type { Role } from "./types";

export const MANAGE_USERS = "users:manage";
export const VIEW_USERS = "users:view";
export const VIEW_ALL_SECURITY_DATA = "security:view_all";
export const MANAGE_ALERTS = "alerts:manage";
export const VIEW_LOGS = "logs:view";
export const VIEW_REPORTS = "reports:view";
export const VIEW_ANALYTICS = "analytics:view";
export const INVESTIGATE_THREATS = "threats:investigate";

// Mirrors app/core/permissions.py ROLE_PERMISSIONS on the backend — used only
// to decide which nav items/actions to render; the backend is the real
// enforcement point for every one of these.
const ROLE_PERMISSIONS: Record<Role, string[]> = {
  admin: [
    MANAGE_USERS,
    VIEW_USERS,
    VIEW_ALL_SECURITY_DATA,
    MANAGE_ALERTS,
    VIEW_LOGS,
    VIEW_REPORTS,
    VIEW_ANALYTICS,
    INVESTIGATE_THREATS,
  ],
  security_analyst: [VIEW_USERS, VIEW_LOGS, INVESTIGATE_THREATS, MANAGE_ALERTS, VIEW_ANALYTICS],
  auditor: [VIEW_REPORTS, VIEW_LOGS, VIEW_ANALYTICS],
  user: [],
};

export function hasPermission(role: Role | undefined, permission: string): boolean {
  if (!role) return false;
  return ROLE_PERMISSIONS[role]?.includes(permission) ?? false;
}
