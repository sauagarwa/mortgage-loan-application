import { Upload, User } from 'lucide-react';
import { ChatLoanCard } from './chat-loan-card';
import { ChatSummaryCard } from './chat-summary-card';
import type { LoanCardData } from '../../schemas/chat';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  messageType: string;
  metadata?: Record<string, unknown>;
}

export function ChatMessage({ role, content, messageType, metadata }: ChatMessageProps) {
  const isUser = role === 'user';

  // Render structured content
  if (messageType === 'loan_cards' && metadata?.products) {
    const products = metadata.products as LoanCardData[];
    return (
      <div className="flex items-start gap-3 px-4 py-2">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-medium text-primary-foreground">
          AI
        </div>
        <div className="max-w-[90%] space-y-2">
          <div className="grid gap-2 sm:grid-cols-2">
            {products.map((product) => (
              <ChatLoanCard key={product.id} product={product} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (messageType === 'summary' && metadata?.summary) {
    return (
      <div className="flex items-start gap-3 px-4 py-2">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-medium text-primary-foreground">
          AI
        </div>
        <div className="max-w-[85%]">
          <ChatSummaryCard summary={metadata.summary as Record<string, unknown>} />
        </div>
      </div>
    );
  }

  if (messageType === 'file_upload') {
    return (
      <div className={`flex items-start gap-3 px-4 py-2 ${isUser ? 'flex-row-reverse' : ''}`}>
        <div
          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-medium ${
            isUser
              ? 'bg-blue-600 text-white'
              : 'bg-primary text-primary-foreground'
          }`}
        >
          {isUser ? <User className="h-4 w-4" /> : 'AI'}
        </div>
        <div
          className={`flex items-center gap-2 rounded-2xl px-4 py-3 text-sm ${
            isUser
              ? 'rounded-tr-sm bg-blue-600 text-white'
              : 'rounded-tl-sm bg-muted'
          }`}
        >
          <Upload className="h-4 w-4" />
          {content}
        </div>
      </div>
    );
  }

  // Default text message
  return (
    <div className={`flex items-start gap-3 px-4 py-2 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-medium ${
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-primary text-primary-foreground'
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : 'AI'}
      </div>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? 'rounded-tr-sm bg-blue-600 text-white'
            : 'rounded-tl-sm bg-muted'
        }`}
      >
        {content.split('\n').map((line, i) => (
          <p key={i} className={i > 0 ? 'mt-2' : ''}>
            {line}
          </p>
        ))}
      </div>
    </div>
  );
}
