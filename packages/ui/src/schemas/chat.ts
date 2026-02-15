import { z } from 'zod';

export const ChatSessionSchema = z.object({
  session_id: z.string(),
  conversation_id: z.string(),
});
export type ChatSession = z.infer<typeof ChatSessionSchema>;

export const ChatMessageSchema = z.object({
  id: z.string(),
  role: z.enum(['user', 'assistant', 'system', 'tool']),
  content: z.string(),
  message_type: z.string(),
  metadata: z.record(z.unknown()).nullable().optional(),
  created_at: z.string(),
});
export type ChatMessage = z.infer<typeof ChatMessageSchema>;

export const ChatHistorySchema = z.object({
  session_id: z.string(),
  conversation_id: z.string(),
  current_phase: z.string(),
  messages: z.array(ChatMessageSchema),
});
export type ChatHistory = z.infer<typeof ChatHistorySchema>;

export const ChatFileUploadResponseSchema = z.object({
  document_id: z.string(),
  filename: z.string(),
  document_type: z.string(),
  status: z.string(),
});
export type ChatFileUploadResponse = z.infer<typeof ChatFileUploadResponseSchema>;

export const ChatLinkResponseSchema = z.object({
  linked: z.boolean(),
  user_id: z.string(),
  application_id: z.string().nullable().optional(),
});
export type ChatLinkResponse = z.infer<typeof ChatLinkResponseSchema>;

// SSE event types
export interface ChatEvent {
  event_type: 'text' | 'tool_start' | 'structured' | 'file_request' | 'auth_required' | 'done';
  data: Record<string, unknown>;
}

export interface LoanCardData {
  id: string;
  name: string;
  type: string;
  term_years: number;
  rate_type: string;
  min_down_payment_pct: number | null;
  min_credit_score: number | null;
  max_dti_ratio: number | null;
  max_loan_amount: number | null;
  description: string | null;
  features: string[];
}
