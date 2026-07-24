import type { AlertStatus, Severity } from "@/lib/types";

const SEVERITY_STYLES: Record<Severity, string> = {
  low: "bg-status-good/15 text-status-good",
  medium: "bg-status-warning/20 text-[#8a6400] dark:text-status-warning",
  high: "bg-status-serious/20 text-[#a8451f] dark:text-status-serious",
  critical: "bg-status-critical/15 text-status-critical",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium capitalize ${SEVERITY_STYLES[severity]}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {severity}
    </span>
  );
}

const STATUS_STYLES: Record<AlertStatus, string> = {
  open: "bg-status-critical/15 text-status-critical",
  investigating: "bg-status-warning/20 text-[#8a6400] dark:text-status-warning",
  resolved: "bg-status-good/15 text-status-good",
  dismissed: "bg-text-muted/15 text-text-muted",
};

export function AlertStatusBadge({ status }: { status: AlertStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium capitalize ${STATUS_STYLES[status]}`}
    >
      {status}
    </span>
  );
}

export function OutcomeBadge({ status }: { status: "successful" | "failed" }) {
  const style =
    status === "successful" ? "bg-status-good/15 text-status-good" : "bg-status-critical/15 text-status-critical";
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium capitalize ${style}`}>
      {status}
    </span>
  );
}
