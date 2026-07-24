"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import * as api from "@/lib/api";
import { ApiError } from "@/lib/api";
import { Card } from "@/components/ui";

function VerifyEmailContent() {
  const params = useSearchParams();
  const token = params.get("token") ?? "";
  const [status, setStatus] = useState<"pending" | "success" | "error">("pending");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("Missing verification token.");
      return;
    }
    api
      .verifyEmail(token)
      .then(() => setStatus("success"))
      .catch((err) => {
        setStatus("error");
        setMessage(err instanceof ApiError ? err.message : "Verification failed.");
      });
  }, [token]);

  return (
    <Card className="p-6 text-center">
      {status === "pending" && <p className="text-text-secondary">Verifying your email...</p>}
      {status === "success" && <p className="text-text-primary">Your email has been verified.</p>}
      {status === "error" && <p className="text-status-critical">{message}</p>}
      <Link href="/login" className="mt-4 inline-block text-sm text-series-1 hover:underline">
        Back to sign in
      </Link>
    </Card>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense>
      <VerifyEmailContent />
    </Suspense>
  );
}
