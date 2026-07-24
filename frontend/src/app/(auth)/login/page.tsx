"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/contexts/auth-context";
import { ApiError } from "@/lib/api";
import { Button, Card, ErrorText, Input, Label } from "@/components/ui";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mfaCode, setMfaCode] = useState("");
  const [mfaRequired, setMfaRequired] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const result = await login(email, password, mfaCode || undefined);
      if (result.mfaRequired) {
        setMfaRequired(true);
      } else {
        router.replace("/dashboard");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card className="p-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label>Email</Label>
          <Input
            type="email"
            required
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={mfaRequired}
          />
        </div>
        <div>
          <Label>Password</Label>
          <Input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={mfaRequired}
          />
        </div>
        {mfaRequired && (
          <div>
            <Label>6-digit authentication code</Label>
            <Input
              inputMode="numeric"
              autoFocus
              maxLength={6}
              value={mfaCode}
              onChange={(e) => setMfaCode(e.target.value)}
              placeholder="123456"
            />
          </div>
        )}
        {error && <ErrorText>{error}</ErrorText>}
        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? "Signing in..." : mfaRequired ? "Verify" : "Sign in"}
        </Button>
        <div className="flex items-center justify-between text-sm text-text-secondary">
          <Link href="/forgot-password" className="hover:text-series-1">
            Forgot password?
          </Link>
          <Link href="/register" className="hover:text-series-1">
            Create an account
          </Link>
        </div>
      </form>
    </Card>
  );
}
