"use client";

import { useState } from "react";
import * as api from "@/lib/api";
import { ApiError } from "@/lib/api";
import { PageHeader, Card, Button, ErrorText } from "@/components/ui";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const SUGGESTIONS = [
  "Summarize today's security events.",
  "What should I investigate first?",
  "Why might a brute-force alert be a false positive?",
  "Generate an incident report for the most recent critical alert.",
];

export default function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send(question: string) {
    if (!question.trim()) return;
    setError(null);
    setMessages((m) => [...m, { role: "user", content: question }]);
    setInput("");
    setLoading(true);
    try {
      const res = await api.askAiAnalyst(question);
      setMessages((m) => [...m, { role: "assistant", content: res.answer }]);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Failed to reach the AI Security Analyst."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-full max-h-[calc(100vh-8rem)] flex-col">
      <PageHeader
        title="AI Security Analyst"
        description="Ask questions about today's alerts and audit logs. Answers are grounded in real platform data."
      />

      {messages.length === 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              className="rounded-full border border-border-strong bg-surface-raised px-3 py-1.5 text-xs text-text-secondary hover:border-series-1 hover:text-series-1"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <Card className="flex flex-1 flex-col overflow-hidden p-0">
        <div className="flex-1 space-y-4 overflow-y-auto p-5">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[80%] whitespace-pre-wrap rounded-xl px-4 py-2.5 text-sm ${
                  m.role === "user"
                    ? "bg-series-1 text-white"
                    : "bg-surface-page text-text-primary"
                }`}
              >
                {m.content}
              </div>
            </div>
          ))}
          {loading && <p className="text-sm text-text-muted">Analyzing...</p>}
          {error && <ErrorText>{error}</ErrorText>}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
          className="flex gap-2 border-t border-border-hairline p-4"
        >
          <input
            className="flex-1 rounded-lg border border-border-strong bg-surface-raised px-3 py-2 text-sm text-text-primary focus:border-series-1 focus:outline-none"
            placeholder="Ask about today's security events..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <Button type="submit" disabled={loading}>
            Send
          </Button>
        </form>
      </Card>
    </div>
  );
}
