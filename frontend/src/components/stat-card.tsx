import { Card } from "./ui";

export function StatCard({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string;
  value: string | number;
  hint?: string;
  tone?: "default" | "good" | "warning" | "critical";
}) {
  const toneClass = {
    default: "text-text-primary",
    good: "text-status-good",
    warning: "text-status-warning",
    critical: "text-status-critical",
  }[tone];

  return (
    <Card className="p-5">
      <p className="text-xs font-medium uppercase tracking-wide text-text-muted">{label}</p>
      <p className={`mt-2 text-3xl font-semibold tabular-nums ${toneClass}`}>{value}</p>
      {hint && <p className="mt-1 text-xs text-text-secondary">{hint}</p>}
    </Card>
  );
}
