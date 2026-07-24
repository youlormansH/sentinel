"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import * as api from "@/lib/api";
import type { Alert, AnalyticsReport, DashboardMetrics } from "@/lib/types";
import { PageHeader, Card } from "@/components/ui";
import { StatCard } from "@/components/stat-card";
import { TrendLineChart, CategoryBarChart } from "@/components/charts";
import { SeverityBadge, AlertStatusBadge } from "@/components/badges";
import { useAlertsSocket } from "@/lib/use-alerts-socket";

const SERIES_COLORS = [
  "var(--series-1)",
  "var(--series-2)",
  "var(--series-3)",
  "var(--series-4)",
  "var(--series-5)",
];

const THREAT_LEVEL_TONE = {
  low: "good",
  medium: "warning",
  high: "critical",
  critical: "critical",
} as const;

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsReport | null>(null);
  const [recentAlerts, setRecentAlerts] = useState<Alert[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function loadData() {
    try {
      const [m, a, alertsPage] = await Promise.all([
        api.getMetrics(),
        api.getAnalytics(7),
        api.listAlerts({ page: 1, page_size: 5 }),
      ]);
      setMetrics(m);
      setAnalytics(a);
      setRecentAlerts(alertsPage.items);
    } catch {
      setError("You may not have permission to view security data, or the API is unreachable.");
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  useAlertsSocket((evt) => {
    if (evt.event === "new_alert") loadData();
  });

  if (error) {
    return (
      <div className="text-sm text-status-critical">{error}</div>
    );
  }

  if (!metrics || !analytics) {
    return <div className="text-text-secondary">Loading dashboard...</div>;
  }

  return (
    <div>
      <PageHeader title="Security Dashboard" description="Real-time overview of accounts, sessions, and threats." />

      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-5">
        <StatCard label="Total Users" value={metrics.total_users} />
        <StatCard label="Active Sessions" value={metrics.active_sessions} />
        <StatCard label="Successful Logins (24h)" value={metrics.successful_logins_24h} tone="good" />
        <StatCard label="Failed Logins (24h)" value={metrics.failed_logins_24h} tone="critical" />
        <StatCard label="Open Alerts" value={metrics.open_alerts} tone="warning" />
        <StatCard label="Security Score" value={`${metrics.security_score}/100`} />
        <StatCard
          label="Threat Level"
          value={metrics.threat_level}
          tone={THREAT_LEVEL_TONE[metrics.threat_level]}
        />
        <StatCard label="API Requests (24h)" value={metrics.api_requests_24h} />
        <StatCard label="Suspicious Events (24h)" value={metrics.suspicious_events_24h} tone="warning" />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className="p-5">
          <h3 className="mb-3 text-sm font-semibold text-text-primary">Login Activity (7 days)</h3>
          <TrendLineChart
            series={[
              { name: "Successful", data: analytics.daily_login_activity, color: "var(--status-good)" },
              { name: "Failed", data: analytics.failed_login_trend, color: "var(--status-critical)" },
            ]}
          />
        </Card>
        <Card className="p-5">
          <h3 className="mb-3 text-sm font-semibold text-text-primary">Alert Severity Breakdown</h3>
          <CategoryBarChart
            data={analytics.alert_severity_breakdown.map((s) => ({ category: s.category, count: s.count }))}
            color="var(--status-serious)"
          />
        </Card>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className="p-5">
          <h3 className="mb-3 text-sm font-semibold text-text-primary">Threat Categories</h3>
          <CategoryBarChart data={analytics.threat_categories} color={SERIES_COLORS[0]} />
        </Card>
        <Card className="p-5">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-text-primary">Recent Alerts</h3>
            <Link href="/alerts" className="text-xs text-series-1 hover:underline">
              View all
            </Link>
          </div>
          <div className="space-y-3">
            {recentAlerts.length === 0 && <p className="text-sm text-text-muted">No alerts yet.</p>}
            {recentAlerts.map((a) => (
              <div key={a.id} className="flex items-start justify-between gap-3 border-b border-border-hairline pb-3 last:border-0 last:pb-0">
                <div>
                  <p className="text-sm text-text-primary">{a.description}</p>
                  <p className="mt-1 text-xs text-text-muted">
                    {a.category} &middot; {new Date(a.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="flex shrink-0 flex-col items-end gap-1.5">
                  <SeverityBadge severity={a.severity} />
                  <AlertStatusBadge status={a.status} />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
