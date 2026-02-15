import { apiGet, apiPost, apiUpload } from './api-client';
import type {
  ChatFileUploadResponse,
  ChatHistory,
  ChatLinkResponse,
  ChatSession,
} from '../schemas/chat';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function createChatSession(): Promise<ChatSession> {
  return apiPost<ChatSession>('/api/v1/chat/sessions');
}

export function sendChatMessage(
  sessionId: string,
  content: string,
  onEvent: (eventType: string, data: Record<string, unknown>) => void,
  onDone: () => void,
  onError: (error: Error) => void,
): () => void {
  const controller = new AbortController();

  (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/sessions/${sessionId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
        signal: controller.signal,
      });

      if (!response.ok) {
        const err = await response.json().catch(() => null);
        throw new Error(err?.detail || `Error: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE events from buffer
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let currentEvent = '';
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith('data: ')) {
            const dataStr = line.slice(6);
            try {
              const data = JSON.parse(dataStr);
              if (currentEvent === 'done') {
                onDone();
              } else if (currentEvent) {
                onEvent(currentEvent, data);
              }
            } catch {
              // Skip malformed JSON
            }
            currentEvent = '';
          }
        }
      }

      onDone();
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return;
      onError(err instanceof Error ? err : new Error(String(err)));
    }
  })();

  return () => controller.abort();
}

export async function uploadChatFile(
  sessionId: string,
  file: File,
  documentType: string,
): Promise<ChatFileUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('document_type', documentType);
  return apiUpload<ChatFileUploadResponse>(
    `/api/v1/chat/sessions/${sessionId}/files`,
    formData,
  );
}

export async function linkChatSession(
  sessionId: string,
): Promise<ChatLinkResponse> {
  return apiPost<ChatLinkResponse>(`/api/v1/chat/sessions/${sessionId}/link`);
}

export async function getChatHistory(
  sessionId: string,
): Promise<ChatHistory> {
  return apiGet<ChatHistory>(`/api/v1/chat/sessions/${sessionId}/history`);
}
