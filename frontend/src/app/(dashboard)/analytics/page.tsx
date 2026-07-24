"use client";

import { useEffect, useState } from "react";
import * as api from "@/lib/api";
import { ApiError } from "@/lib/api";
import type { AnalyticsReport } from "@/lib/types";
import { PageHeader, Card, Select, ErrorText } from "@/components/ui";
import { TrendLineChart, CategoryBarChart } from "@/components/charts";

export default function AnalyticsPage() {
  const [days, setDays] = useState(7);
  const [data, setData] = useState<AnalyticsReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getAnalytics(days)
      .then(setData)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load analytics."));
  }, [days]);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <PageHeader title="Analytics" description="Trends across logins, incidents, and system performance." />
        <Select value={days} onChange={(e) => setDays(Number(e.target.value))}>
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </Select>
      </div>

      {error && <ErrorText>{error}</ErrorText>}

      {data && (
        <div className="space-y-4">
          <Card className="p-5">
            <h3 className="mb-3 text-sm font-semibold text-text-primary">Daily Login Activity</h3>
            <TrendLineChart
              series={[
                { name: "Successful", data: data.daily_login_activity, color: "var(--status-good)" },
                { name: "Failed", data: data.failed_login_trend, color: "var(--status-critical)" },
              ]}
            />
          </Card>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card className="p-5">
              <h3 className="mb-3 text-sm font-semibold text-text-primary">Security Incidents</h3>
              <TrendLineChart
                series={[{ name: "Alerts created", data: data.security_incidents, color: "var(--series-7)" }]}
              />
            </Card>
            <Card className="p-5">
              <h3 className="mb-3 text-sm font-semibold text-text-primary">System Performance (avg response ms)</h3>
              <TrendLineChart
                series={[{ name: "Avg response time", data: data.system_performance, color: "var(--series-1)" }]}
              />
            </Card>
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card className="p-5">
              <h3 className="mb-3 text-sm font-semibold text-text-primary">Threat Categories</h3>
              <CategoryBarChart data={data.threat_categories} color="var(--series-2)" />
            </Card>
            <Card className="p-5">
              <h3 className="mb-3 text-sm font-semibold text-text-primary">Alert Severity Breakdown</h3>
              <CategoryBarChart
                data={data.alert_severity_breakdown.map((s) => ({ category: s.category, count: s.count }))}
                color="var(--status-serious)"
              />
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
