"use client";

import { useEffect, useState } from "react";
import * as api from "@/lib/api";
import { ApiError } from "@/lib/api";
import type { AuditLog } from "@/lib/types";
import { PageHeader, Card, Input, Select, Button, ErrorText } from "@/components/ui";
import { OutcomeBadge } from "@/components/badges";
import { Pagination } from "@/components/pagination";

const CATEGORIES = [
  "authentication",
  "account",
  "user_management",
  "incident_response",
  "general",
];

export default function LogsPage() {
  const [items, setItems] = useState<AuditLog[]>([]);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      const res = await api.listLogs({ page, page_size: 15, search, category, status });
      setItems(res.items);
      setPages(res.pages);
      setTotal(res.total);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load audit logs.");
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, category, status]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    load();
  }

  return (
    <div>
      <PageHeader title="Audit Logs" description="Complete trail of authentication and administrative activity." />

      <Card className="mb-4 p-4">
        <form onSubmit={handleSearch} className="flex flex-wrap items-end gap-3">
          <div className="min-w-[220px] flex-1">
            <Input
              placeholder="Search by user or action..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">All categories</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c.replace("_", " ")}
              </option>
            ))}
          </Select>
          <Select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All statuses</option>
            <option value="successful">Successful</option>
            <option value="failed">Failed</option>
          </Select>
          <Button type="submit" variant="secondary">
            Search
          </Button>
        </form>
      </Card>

      {error && <ErrorText>{error}</ErrorText>}

      <Card className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-border-hairline text-xs uppercase tracking-wide text-text-muted">
            <tr>
              <th className="px-4 py-3 font-medium">User</th>
              <th className="px-4 py-3 font-medium">Action</th>
              <th className="px-4 py-3 font-medium">Time</th>
              <th className="px-4 py-3 font-medium">IP Address</th>
              <th className="px-4 py-3 font-medium">Device / Browser</th>
              <th className="px-4 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-hairline">
            {items.map((log) => (
              <tr key={log.id}>
                <td className="px-4 py-3 text-text-primary">{log.user_email ?? "—"}</td>
                <td className="px-4 py-3 text-text-secondary">{log.action}</td>
                <td className="px-4 py-3 text-text-secondary">{new Date(log.created_at).toLocaleString()}</td>
                <td className="px-4 py-3 tabular-nums text-text-secondary">{log.ip_address ?? "—"}</td>
                <td className="px-4 py-3 text-text-secondary">
                  {log.device ?? "—"} {log.browser ? `· ${log.browser}` : ""}
                </td>
                <td className="px-4 py-3">
                  <OutcomeBadge status={log.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && !error && <p className="p-4 text-sm text-text-muted">No log entries found.</p>}
        <Pagination page={page} pages={pages} total={total} onChange={setPage} />
      </Card>
    </div>
  );
}
