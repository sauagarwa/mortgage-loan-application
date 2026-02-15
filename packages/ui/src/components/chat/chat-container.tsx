import { useEffect, useRef } from 'react';
import { ChatHeader } from './chat-header';
import { ChatMessage } from './chat-message';
import { ChatInput } from './chat-input';
import { ChatTypingIndicator } from './chat-typing-indicator';
import { useChat } from '../../hooks/chat';
import { useAuth } from '../../auth/auth-provider';
import { Button } from '../atoms/button/button';
import { LogIn } from 'lucide-react';

export function ChatContainer() {
  const {
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
  } = useChat();

  const { login } = useAuth();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isThinking]);

  function handleFileSelect(file: File) {
    const docType = fileRequest?.document_type || 'other';
    uploadFile(file, docType);
  }

  return (
    <div className="flex h-screen flex-col">
      <ChatHeader onNewChat={startNewChat} />
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl py-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="flex gap-1">
                <span className="inline-block h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:0ms]" />
                <span className="inline-block h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:150ms]" />
                <span className="inline-block h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:300ms]" />
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  role={msg.role}
                  content={msg.content}
                  messageType={msg.message_type}
                  metadata={msg.metadata}
                />
              ))}
              {isThinking && <ChatTypingIndicator toolName={currentTool} />}
              {authRequired && (
                <div className="flex items-start gap-3 px-4 py-2">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-medium text-primary-foreground">
                    AI
                  </div>
                  <div className="space-y-2 rounded-2xl rounded-tl-sm bg-muted px-4 py-3">
                    <p className="text-sm">
                      To submit your application, you need to sign in first.
                    </p>
                    <Button size="sm" onClick={login} className="gap-1.5">
                      <LogIn className="h-4 w-4" />
                      Sign In to Continue
                    </Button>
                  </div>
                </div>
              )}
              {error && (
                <div className="px-4 py-2">
                  <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
                    {error}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
      <div className="mx-auto w-full max-w-3xl">
        <ChatInput
          onSend={sendMessage}
          onFileSelect={handleFileSelect}
          disabled={isLoading || isThinking}
          fileRequest={fileRequest}
        />
      </div>
    </div>
  );
}
