"use client";

import Link from "next/link";
import { useState } from "react";
import * as api from "@/lib/api";
import { Button, Card, Input, Label } from "@/components/ui";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.forgotPassword(email);
    } finally {
      setSubmitting(false);
      setSubmitted(true);
    }
  }

  if (submitted) {
    return (
      <Card className="p-6 text-center">
        <p className="text-text-primary">
          If an account exists for that email, a reset link has been sent.
        </p>
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
          <Label>Email</Label>
          <Input type="email" required autoFocus value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? "Sending..." : "Send reset link"}
        </Button>
      </form>
    </Card>
  );
}
