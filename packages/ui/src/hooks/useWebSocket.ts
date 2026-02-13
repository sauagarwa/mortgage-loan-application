import { useCallback, useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import keycloak from '../auth/keycloak';

const WS_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
)
  .replace('http://', 'ws://')
  .replace('https://', 'wss://');

interface WebSocketMessage {
  type: string;
  data?: Record<string, unknown>;
}

export function useApplicationWebSocket(applicationId: string | undefined) {
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const pingInterval = useRef<ReturnType<typeof setInterval>>();

  useEffect(() => {
    if (!applicationId || !keycloak.authenticated || !keycloak.token) return;

    const url = `${WS_BASE_URL}/api/v1/ws/applications/${applicationId}?token=${keycloak.token}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const msg: WebSocketMessage = JSON.parse(event.data);
        setLastMessage(msg);

        if (msg.type === 'assessment_complete' || msg.type === 'decision_made') {
          queryClient.invalidateQueries({
            queryKey: ['application', applicationId],
          });
          queryClient.invalidateQueries({ queryKey: ['notifications'] });
        }
        if (msg.type === 'document_processed') {
          queryClient.invalidateQueries({
            queryKey: ['documents', applicationId],
          });
        }
        if (msg.type === 'status_change') {
          queryClient.invalidateQueries({
            queryKey: ['application', applicationId],
          });
        }
      } catch {
        // ignore invalid messages
      }
    };

    ws.onopen = () => {
      pingInterval.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 30000);
    };

    ws.onerror = () => {
      // Silently handle — auto-polling via TanStack Query is the fallback
    };

    return () => {
      if (pingInterval.current) clearInterval(pingInterval.current);
      ws.close();
      wsRef.current = null;
    };
  }, [applicationId, queryClient]);

  return { lastMessage };
}

export function useServicerWebSocket() {
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const pingInterval = useRef<ReturnType<typeof setInterval>>();

  useEffect(() => {
    if (!keycloak.authenticated || !keycloak.token) return;

    const url = `${WS_BASE_URL}/api/v1/ws/servicer/notifications?token=${keycloak.token}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const msg: WebSocketMessage = JSON.parse(event.data);
        setLastMessage(msg);

        if (
          msg.type === 'new_application' ||
          msg.type === 'assessment_complete'
        ) {
          queryClient.invalidateQueries({ queryKey: ['servicer'] });
          queryClient.invalidateQueries({ queryKey: ['notifications'] });
        }
      } catch {
        // ignore
      }
    };

    ws.onopen = () => {
      pingInterval.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 30000);
    };

    return () => {
      if (pingInterval.current) clearInterval(pingInterval.current);
      ws.close();
      wsRef.current = null;
    };
  }, [queryClient]);

  const sendMessage = useCallback((msg: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(msg);
    }
  }, []);

  return { lastMessage, sendMessage };
}
