interface ChatTypingIndicatorProps {
  toolName?: string | null;
}

export function ChatTypingIndicator({ toolName }: ChatTypingIndicatorProps) {
  return (
    <div className="flex items-start gap-3 px-4 py-2">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-medium text-primary-foreground">
        AI
      </div>
      <div className="rounded-2xl rounded-tl-sm bg-muted px-4 py-3">
        {toolName ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <div className="flex gap-1">
              <span className="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:0ms]" />
              <span className="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:150ms]" />
              <span className="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:300ms]" />
            </div>
            <span className="capitalize">{toolName.replace(/_/g, ' ')}...</span>
          </div>
        ) : (
          <div className="flex gap-1">
            <span className="inline-block h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:0ms]" />
            <span className="inline-block h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:150ms]" />
            <span className="inline-block h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:300ms]" />
          </div>
        )}
      </div>
    </div>
  );
}
