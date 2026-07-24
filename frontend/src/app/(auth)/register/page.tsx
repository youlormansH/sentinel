"use client";

import Link from "next/link";
import { useState } from "react";
import { useAuth } from "@/contexts/auth-context";
import { ApiError } from "@/lib/api";
import { Button, Card, ErrorText, Input, Label } from "@/components/ui";

export default function RegisterPage() {
  const { register } = useAuth();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(email, fullName, password);
      setDone(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (done) {
    return (
      <Card className="p-6 text-center">
        <p className="text-text-primary">Account created. Check your email (or the backend logs in dev) for a verification link.</p>
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
          <Label>Full name</Label>
          <Input required autoFocus value={fullName} onChange={(e) => setFullName(e.target.value)} />
        </div>
        <div>
          <Label>Email</Label>
          <Input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div>
          <Label>Password</Label>
          <Input
            type="password"
            required
            minLength={10}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <p className="mt-1 text-xs text-text-muted">
            10+ characters, with uppercase, lowercase, a digit, and a symbol.
          </p>
        </div>
        {error && <ErrorText>{error}</ErrorText>}
        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? "Creating account..." : "Create account"}
        </Button>
        <p className="text-center text-sm text-text-secondary">
          Already have an account?{" "}
          <Link href="/login" className="text-series-1 hover:underline">
            Sign in
          </Link>
        </p>
      </form>
    </Card>
  );
}
