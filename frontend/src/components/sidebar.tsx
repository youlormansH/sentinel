"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/auth-context";
import { hasPermission, VIEW_ALL_SECURITY_DATA, VIEW_ANALYTICS, VIEW_LOGS, VIEW_USERS } from "@/lib/permissions";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", permission: null },
  { href: "/alerts", label: "Alerts", permission: VIEW_ALL_SECURITY_DATA },
  { href: "/logs", label: "Audit Logs", permission: VIEW_LOGS },
  { href: "/analytics", label: "Analytics", permission: VIEW_ANALYTICS },
  { href: "/users", label: "Users", permission: VIEW_USERS },
  { href: "/assistant", label: "AI Analyst", permission: VIEW_ALL_SECURITY_DATA },
  { href: "/settings", label: "Settings", permission: null },
] as const;

export function Sidebar() {
  const { user } = useAuth();
  const pathname = usePathname();

  return (
    <aside className="flex h-full w-60 shrink-0 flex-col border-r border-border-hairline bg-surface-card">
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-series-1 text-white">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2 4 5v6c0 5 3.5 9 8 11 4.5-2 8-6 8-11V5l-8-3z" />
          </svg>
        </div>
        <span className="text-lg font-semibold text-text-primary">Sentinel</span>
      </div>
      <nav className="flex-1 space-y-1 px-3">
        {NAV_ITEMS.filter((item) => !item.permission || hasPermission(user?.role, item.permission)).map((item) => {
          const active = pathname?.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`block rounded-lg px-3 py-2 text-sm font-medium transition ${
                active
                  ? "bg-series-1/10 text-series-1"
                  : "text-text-secondary hover:bg-surface-page hover:text-text-primary"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-border-hairline px-5 py-4 text-xs text-text-muted">
        Signed in as
        <div className="truncate text-sm font-medium text-text-primary">{user?.email}</div>
        <div className="capitalize">{user?.role.replace("_", " ")}</div>
      </div>
    </aside>
  );
}
