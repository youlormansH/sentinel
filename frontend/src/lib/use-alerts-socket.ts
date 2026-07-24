"use client";

import { useEffect, useRef } from "react";
import { API_BASE_URL } from "./api";
import { getAccessToken } from "./token-store";
import type { Alert } from "./types";

type AlertEvent =
  | { event: "new_alert"; data: Alert }
  | { event: "alert_updated"; data: Partial<Alert> & { id: string } };

export function useAlertsSocket(onEvent: (evt: AlertEvent) => void) {
  const handlerRef = useRef(onEvent);
  handlerRef.current = onEvent;

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;

    const wsUrl = `${API_BASE_URL.replace(/^http/, "ws")}/api/v1/ws/alerts?token=${encodeURIComponent(token)}`;
    let socket: WebSocket;
    let closedByClient = false;

    try {
      socket = new WebSocket(wsUrl);
    } catch {
      return;
    }

    socket.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data) as AlertEvent;
        handlerRef.current(parsed);
      } catch {
        // ignore malformed frames
      }
    };

    return () => {
      closedByClient = true;
      socket.close();
      void closedByClient;
    };
  }, []);
}
