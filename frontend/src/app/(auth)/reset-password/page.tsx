"use client";

import Link from "next/link";
import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import * as api from "@/lib/api";
import { ApiError } from "@/lib/api";
import { Button, Card, ErrorText, Input, Label } from "@/components/ui";

function ResetPasswordForm() {
  const params = useSearchParams();
  const token = params.get("token") ?? "";
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.resetPassword(token, password);
      setDone(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  }

  if (!token) {
    return <Card className="p-6 text-center text-text-secondary">Missing or invalid reset link.</Card>;
  }

  if (done) {
    return (
      <Card className="p-6 text-center">
        <p className="text-text-primary">Password updated. You can now sign in.</p>
        <Link href="/login" className="mt-4 inline-block text-sm text-series-1 hover:underline">
          Back to sign in
        </Link>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label>New password</Label>
          <Input
            type="password"
            required
            minLength={10}
            autoFocus
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        {error && <ErrorText>{error}</ErrorText>}
        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? "Updating..." : "Update password"}
        </Button>
      </form>
    </Card>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense>
      <ResetPasswordForm />
    </Suspense>
  );
}
