"use client";

import { useEffect, useState } from "react";
import * as api from "@/lib/api";
import { ApiError } from "@/lib/api";
import type { SessionInfo } from "@/lib/types";
import { PageHeader, Card, Input, Button, ErrorText, Label } from "@/components/ui";
import { useAuth } from "@/contexts/auth-context";

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [setupData, setSetupData] = useState<{ secret: string; otpauth_url: string } | null>(null);
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function loadSessions() {
    try {
      setSessions(await api.listSessions());
    } catch {
      // non-fatal
    }
  }

  useEffect(() => {
    loadSessions();
  }, []);

  async function startMfaSetup() {
    setError(null);
    try {
      const data = await api.mfaSetup();
      setSetupData(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to start MFA setup.");
    }
  }

  async function confirmMfaEnable(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.mfaEnable(code);
      setSetupData(null);
      setCode("");
      setMessage("Multi-factor authentication enabled.");
      await refreshUser();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Invalid code.");
    }
  }

  async function disableMfa(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.mfaDisable(code);
      setCode("");
      setMessage("Multi-factor authentication disabled.");
      await refreshUser();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Invalid code.");
    }
  }

  async function revoke(id: string) {
    await api.revokeSession(id);
    loadSessions();
  }

  return (
    <div className="max-w-2xl space-y-6">
      <PageHeader title="Settings" description="Manage multi-factor authentication and active sessions." />

      {message && <p className="text-sm text-status-good">{message}</p>}
      {error && <ErrorText>{error}</ErrorText>}

      <Card className="p-5">
        <h3 className="mb-2 text-sm font-semibold text-text-primary">Multi-factor authentication</h3>
        <p className="mb-4 text-sm text-text-secondary">
          Status: <span className={user?.mfa_enabled ? "text-status-good" : "text-text-muted"}>
            {user?.mfa_enabled ? "Enabled" : "Disabled"}
          </span>
        </p>

        {!user?.mfa_enabled && !setupData && <Button onClick={startMfaSetup}>Set up MFA</Button>}

        {setupData && (
          <form onSubmit={confirmMfaEnable} className="space-y-3">
            <p className="text-sm text-text-secondary">
              Add this key to your authenticator app (Google Authenticator, 1Password, Authy...):
            </p>
            <code className="block break-all rounded-lg bg-surface-page p-3 text-xs text-text-primary">
              {setupData.secret}
            </code>
            <div>
              <Label>Enter the 6-digit code to confirm</Label>
              <Input value={code} onChange={(e) => setCode(e.target.value)} maxLength={6} />
            </div>
            <Button type="submit">Enable MFA</Button>
          </form>
        )}

        {user?.mfa_enabled && (
          <form onSubmit={disableMfa} className="space-y-3">
            <div>
              <Label>Enter your current code to disable MFA</Label>
              <Input value={code} onChange={(e) => setCode(e.target.value)} maxLength={6} />
            </div>
            <Button variant="danger" type="submit">
              Disable MFA
            </Button>
          </form>
        )}
      </Card>

      <Card className="p-5">
        <h3 className="mb-3 text-sm font-semibold text-text-primary">Active sessions</h3>
        <div className="space-y-2">
          {sessions.map((s) => (
            <div key={s.id} className="flex items-center justify-between rounded-lg bg-surface-page px-3 py-2 text-sm">
              <div>
                <p className="text-text-primary">
                  {s.device ?? "Unknown device"} &middot; {s.ip_address ?? "unknown IP"}
                </p>
                <p className="text-xs text-text-muted">
                  Created {new Date(s.created_at).toLocaleString()} · Expires{" "}
                  {new Date(s.expires_at).toLocaleString()}
                </p>
              </div>
              <Button variant="secondary" onClick={() => revoke(s.id)}>
                Revoke
              </Button>
            </div>
          ))}
          {sessions.length === 0 && <p className="text-sm text-text-muted">No active sessions.</p>}
        </div>
      </Card>
    </div>
  );
}
