import { useCallback, useEffect, useRef, useState } from 'react';
import {
  createChatSession,
  getChatHistory,
  linkChatSession,
  sendChatMessage,
  uploadChatFile,
} from '../services/chat';
import { useAuth } from '../auth/auth-provider';
import type { ChatMessage } from '../schemas/chat';

const SESSION_KEY = 'mortgage-ai-chat-session';

interface DisplayMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  message_type: string;
  metadata?: Record<string, unknown>;
  timestamp: string;
}

interface FileRequest {
  document_type: string;
  reason: string;
}

export function useChat() {
  const { isAuthenticated } = useAuth();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [currentTool, setCurrentTool] = useState<string | null>(null);
  const [fileRequest, setFileRequest] = useState<FileRequest | null>(null);
  const [authRequired, setAuthRequired] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cancelRef = useRef<(() => void) | null>(null);
  const sessionLinked = useRef(false);

  // Initialize or resume session
  useEffect(() => {
    const stored = localStorage.getItem(SESSION_KEY);
    if (stored) {
      setSessionId(stored);
      // Load history
      getChatHistory(stored)
        .then((history) => {
          const displayMsgs: DisplayMessage[] = history.messages
            .filter((m: ChatMessage) => m.role === 'user' || m.role === 'assistant')
            .map((m: ChatMessage) => ({
              id: m.id,
              role: m.role as 'user' | 'assistant',
              content: m.content,
              message_type: m.message_type,
              metadata: m.metadata as Record<string, unknown> | undefined,
              timestamp: m.created_at,
            }));
          setMessages(displayMsgs);
        })
        .catch(() => {
          // Session expired, create new one
          localStorage.removeItem(SESSION_KEY);
          initSession();
        });
    } else {
      initSession();
    }
  }, []);

  // Link session when user authenticates
  useEffect(() => {
    if (isAuthenticated && sessionId && !sessionLinked.current) {
      sessionLinked.current = true;
      linkChatSession(sessionId).catch((err) => {
        console.error('Failed to link session:', err);
        sessionLinked.current = false;
      });
    }
  }, [isAuthenticated, sessionId]);

  async function initSession() {
    try {
      setIsLoading(true);
      const session = await createChatSession();
      setSessionId(session.session_id);
      localStorage.setItem(SESSION_KEY, session.session_id);
      // Load the welcome message
      const history = await getChatHistory(session.session_id);
      const displayMsgs: DisplayMessage[] = history.messages.map((m: ChatMessage) => ({
        id: m.id,
        role: m.role as 'user' | 'assistant',
        content: m.content,
        message_type: m.message_type,
        metadata: m.metadata as Record<string, unknown> | undefined,
        timestamp: m.created_at,
      }));
      setMessages(displayMsgs);
    } catch (err) {
      setError('Failed to start chat session.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }

  const sendMessage = useCallback(
    (content: string) => {
      if (!sessionId || !content.trim() || isThinking) return;

      // Add user message immediately
      const userMsg: DisplayMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content,
        message_type: 'text',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsThinking(true);
      setCurrentTool(null);
      setFileRequest(null);
      setAuthRequired(false);
      setError(null);

      let assistantContent = '';

      const cancel = sendChatMessage(
        sessionId,
        content,
        (eventType, data) => {
          switch (eventType) {
            case 'text':
              assistantContent += (data.content as string) || '';
              break;
            case 'tool_start':
              setCurrentTool(data.tool as string);
              break;
            case 'structured':
              // Add structured message (loan cards, summary)
              setMessages((prev) => [
                ...prev,
                {
                  id: `structured-${Date.now()}`,
                  role: 'assistant',
                  content: '',
                  message_type: (data.type as string) || 'structured',
                  metadata: data,
                  timestamp: new Date().toISOString(),
                },
              ]);
              break;
            case 'file_request':
              setFileRequest({
                document_type: (data.document_type as string) || 'other',
                reason: (data.reason as string) || '',
              });
              break;
            case 'auth_required':
              setAuthRequired(true);
              break;
          }
        },
        () => {
          // Done
          if (assistantContent) {
            setMessages((prev) => [
              ...prev,
              {
                id: `assistant-${Date.now()}`,
                role: 'assistant',
                content: assistantContent,
                message_type: 'text',
                timestamp: new Date().toISOString(),
              },
            ]);
          }
          setIsThinking(false);
          setCurrentTool(null);
        },
        (err) => {
          setError(err.message);
          setIsThinking(false);
          setCurrentTool(null);
        },
      );

      cancelRef.current = cancel;
    },
    [sessionId, isThinking],
  );

  const uploadFile = useCallback(
    async (file: File, documentType: string) => {
      if (!sessionId) return;

      try {
        const result = await uploadChatFile(sessionId, file, documentType);
        // Add file upload message
        setMessages((prev) => [
          ...prev,
          {
            id: `file-${Date.now()}`,
            role: 'user',
            content: `Uploaded: ${file.name}`,
            message_type: 'file_upload',
            metadata: {
              document_id: result.document_id,
              filename: result.filename,
              document_type: result.document_type,
              status: result.status,
            },
            timestamp: new Date().toISOString(),
          },
        ]);
        setFileRequest(null);

        // Send a follow-up message to let the agent know
        sendMessage(`I've uploaded my ${documentType.replace(/_/g, ' ')}.`);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Upload failed');
      }
    },
    [sessionId, sendMessage],
  );

  const startNewChat = useCallback(() => {
    localStorage.removeItem(SESSION_KEY);
    setMessages([]);
    sessionLinked.current = false;
    initSession();
  }, []);

  return {
    sessionId,
    messages,
    isLoading,
    isThinking,
    currentTool,
    fileRequest,
    authRequired,
    error,
    sendMessage,
    uploadFile,
    startNewChat,
  };
}
