"use client";

import { useEffect, useState } from "react";
import * as api from "@/lib/api";
import { ApiError } from "@/lib/api";
import type { Alert, AlertStatus, Severity } from "@/lib/types";
import { PageHeader, Card, Select, Input, Button, ErrorText } from "@/components/ui";
import { SeverityBadge, AlertStatusBadge } from "@/components/badges";
import { Pagination } from "@/components/pagination";
import { hasPermission, MANAGE_ALERTS } from "@/lib/permissions";
import { useAuth } from "@/contexts/auth-context";
import { useAlertsSocket } from "@/lib/use-alerts-socket";

export default function AlertsPage() {
  const { user } = useAuth();
  const canManage = hasPermission(user?.role, MANAGE_ALERTS);

  const [items, setItems] = useState<Alert[]>([]);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Alert | null>(null);
  const [notesDraft, setNotesDraft] = useState("");

  async function load() {
    try {
      const res = await api.listAlerts({ page, page_size: 10, severity, status, search });
      setItems(res.items);
      setPages(res.pages);
      setTotal(res.total);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load alerts.");
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, severity, status]);

  useAlertsSocket((evt) => {
    if (evt.event === "new_alert" || evt.event === "alert_updated") load();
  });

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    load();
  }

  async function updateStatus(alert: Alert, newStatus: AlertStatus) {
    await api.updateAlert(alert.id, { status: newStatus });
    load();
  }

  async function saveNotes() {
    if (!selected) return;
    await api.updateAlert(selected.id, { notes: notesDraft });
    setSelected(null);
    load();
  }

  return (
    <div>
      <PageHeader title="Security Alerts" description="Automatically detected threats and manually created alerts." />

      <Card className="mb-4 p-4">
        <form onSubmit={handleSearch} className="flex flex-wrap items-end gap-3">
          <div className="flex-1 min-w-[200px]">
            <Input placeholder="Search description..." value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <Select value={severity} onChange={(e) => setSeverity(e.target.value)}>
            <option value="">All severities</option>
            {(["low", "medium", "high", "critical"] as Severity[]).map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </Select>
          <Select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All statuses</option>
            {(["open", "investigating", "resolved", "dismissed"] as AlertStatus[]).map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </Select>
          <Button type="submit" variant="secondary">
            Search
          </Button>
        </form>
      </Card>

      {error && <ErrorText>{error}</ErrorText>}

      <Card>
        <div className="divide-y divide-border-hairline">
          {items.map((a) => (
            <div key={a.id} className="flex flex-col gap-3 p-4 md:flex-row md:items-center md:justify-between">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <SeverityBadge severity={a.severity} />
                  <AlertStatusBadge status={a.status} />
                  <span className="text-xs text-text-muted">{a.category}</span>
                </div>
                <p className="mt-1.5 text-sm text-text-primary">{a.description}</p>
                <p className="mt-1 text-xs text-text-muted">
                  {new Date(a.created_at).toLocaleString()}
                  {a.source_ip ? ` · ${a.source_ip}` : ""}
                </p>
                {a.notes && <p className="mt-1 text-xs italic text-text-secondary">Notes: {a.notes}</p>}
              </div>
              {canManage && (
                <div className="flex shrink-0 flex-wrap gap-2">
                  <Select value={a.status} onChange={(e) => updateStatus(a, e.target.value as AlertStatus)}>
                    {(["open", "investigating", "resolved", "dismissed"] as AlertStatus[]).map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </Select>
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setSelected(a);
                      setNotesDraft(a.notes ?? "");
                    }}
                  >
                    Add note
                  </Button>
                </div>
              )}
            </div>
          ))}
          {items.length === 0 && !error && <p className="p-4 text-sm text-text-muted">No alerts found.</p>}
        </div>
        <Pagination page={page} pages={pages} total={total} onChange={setPage} />
      </Card>

      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <Card className="w-full max-w-md p-5">
            <h3 className="mb-3 text-sm font-semibold text-text-primary">Investigation notes</h3>
            <textarea
              className="h-32 w-full rounded-lg border border-border-strong bg-surface-raised p-3 text-sm text-text-primary focus:border-series-1 focus:outline-none"
              value={notesDraft}
              onChange={(e) => setNotesDraft(e.target.value)}
              placeholder="What did you find? What actions were taken?"
            />
            <div className="mt-3 flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setSelected(null)}>
                Cancel
              </Button>
              <Button onClick={saveNotes}>Save</Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
