"use client";

import { useEffect, useState } from "react";
import * as api from "@/lib/api";
import { ApiError } from "@/lib/api";
import type { Role, User } from "@/lib/types";
import { PageHeader, Card, Input, Select, Button, ErrorText, Label } from "@/components/ui";
import { Pagination } from "@/components/pagination";
import { hasPermission, MANAGE_USERS } from "@/lib/permissions";
import { useAuth } from "@/contexts/auth-context";

const ROLES: Role[] = ["admin", "security_analyst", "auditor", "user"];

export default function UsersPage() {
  const { user: currentUser } = useAuth();
  const canManage = hasPermission(currentUser?.role, MANAGE_USERS);

  const [items, setItems] = useState<User[]>([]);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [resetTarget, setResetTarget] = useState<User | null>(null);

  async function load() {
    try {
      const res = await api.listUsers({ page, page_size: 10, search, role: roleFilter });
      setItems(res.items);
      setPages(res.pages);
      setTotal(res.total);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load users.");
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, roleFilter]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    load();
  }

  async function toggleActive(u: User) {
    await api.updateUser(u.id, { is_active: !u.is_active });
    load();
  }

  async function changeRole(u: User, role: Role) {
    await api.updateUser(u.id, { role });
    load();
  }

  async function removeUser(u: User) {
    if (!confirm(`Delete ${u.email}? This cannot be undone.`)) return;
    await api.deleteUser(u.id);
    load();
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <PageHeader title="Users" description="Manage accounts, roles, and access." />
        {canManage && <Button onClick={() => setShowCreate(true)}>Add user</Button>}
      </div>

      <Card className="mb-4 p-4">
        <form onSubmit={handleSearch} className="flex flex-wrap items-end gap-3">
          <div className="min-w-[220px] flex-1">
            <Input
              placeholder="Search by name or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
            <option value="">All roles</option>
            {ROLES.map((r) => (
              <option key={r} value={r}>
                {r.replace("_", " ")}
              </option>
            ))}
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
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Email</th>
              <th className="px-4 py-3 font-medium">Role</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Threat Score</th>
              {canManage && <th className="px-4 py-3 font-medium">Actions</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-border-hairline">
            {items.map((u) => (
              <tr key={u.id}>
                <td className="px-4 py-3 text-text-primary">{u.full_name}</td>
                <td className="px-4 py-3 text-text-secondary">{u.email}</td>
                <td className="px-4 py-3">
                  {canManage ? (
                    <Select value={u.role} onChange={(e) => changeRole(u, e.target.value as Role)}>
                      {ROLES.map((r) => (
                        <option key={r} value={r}>
                          {r.replace("_", " ")}
                        </option>
                      ))}
                    </Select>
                  ) : (
                    <span className="capitalize text-text-secondary">{u.role.replace("_", " ")}</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className={u.is_active ? "text-status-good" : "text-status-critical"}>
                    {u.is_active ? "Active" : "Disabled"}
                  </span>
                </td>
                <td className="px-4 py-3 tabular-nums text-text-secondary">{u.threat_score}</td>
                {canManage && (
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-2">
                      <Button variant="secondary" onClick={() => toggleActive(u)}>
                        {u.is_active ? "Disable" : "Enable"}
                      </Button>
                      <Button variant="secondary" onClick={() => setResetTarget(u)}>
                        Reset password
                      </Button>
                      <Button variant="danger" onClick={() => removeUser(u)}>
                        Delete
                      </Button>
                    </div>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && !error && <p className="p-4 text-sm text-text-muted">No users found.</p>}
        <Pagination page={page} pages={pages} total={total} onChange={setPage} />
      </Card>

      {showCreate && <CreateUserModal onClose={() => setShowCreate(false)} onCreated={load} />}
      {resetTarget && (
        <ResetPasswordModal user={resetTarget} onClose={() => setResetTarget(null)} onDone={load} />
      )}
    </div>
  );
}

function CreateUserModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("user");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.createUser({ email, full_name: fullName, password, role });
      onCreated();
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create user.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Card className="w-full max-w-md p-5">
        <h3 className="mb-4 text-sm font-semibold text-text-primary">Add user</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label>Full name</Label>
            <Input required value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
          <div>
            <Label>Email</Label>
            <Input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <Label>Temporary password</Label>
            <Input type="password" required minLength={10} value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <div>
            <Label>Role</Label>
            <Select value={role} onChange={(e) => setRole(e.target.value as Role)} className="w-full">
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r.replace("_", " ")}
                </option>
              ))}
            </Select>
          </div>
          {error && <ErrorText>{error}</ErrorText>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Creating..." : "Create user"}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}

function ResetPasswordModal({
  user,
  onClose,
  onDone,
}: {
  user: User;
  onClose: () => void;
  onDone: () => void;
}) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.adminResetPassword(user.id, password);
      onDone();
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to reset password.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Card className="w-full max-w-md p-5">
        <h3 className="mb-4 text-sm font-semibold text-text-primary">Reset password for {user.email}</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label>New password</Label>
            <Input type="password" required minLength={10} value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          {error && <ErrorText>{error}</ErrorText>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Saving..." : "Reset password"}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
