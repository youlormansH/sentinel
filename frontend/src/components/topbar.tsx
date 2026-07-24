"use client";

import { useState } from "react";
import { useAuth } from "@/contexts/auth-context";
import { useAlertsSocket } from "@/lib/use-alerts-socket";
import { ThemeToggle } from "./theme-toggle";
import { Button } from "./ui";

export function Topbar() {
  const { logout } = useAuth();
  const [liveCount, setLiveCount] = useState(0);

  useAlertsSocket((evt) => {
    if (evt.event === "new_alert") setLiveCount((c) => c + 1);
  });

  return (
    <header className="flex items-center justify-end gap-3 border-b border-border-hairline bg-surface-card px-6 py-4">
      <div className="flex items-center gap-3">
        {liveCount > 0 && (
          <span className="flex items-center gap-1.5 rounded-full bg-status-critical/15 px-3 py-1 text-xs font-medium text-status-critical">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-status-critical" />
            {liveCount} new alert{liveCount > 1 ? "s" : ""}
          </span>
        )}
        <ThemeToggle />
        <Button variant="secondary" onClick={() => logout()}>
          Log out
        </Button>
      </div>
    </header>
  );
}
