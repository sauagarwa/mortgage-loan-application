import { z } from 'zod';

export const AuditLogSchema = z.object({
  id: z.string(),
  timestamp: z.string(),
  user_id: z.string().nullable(),
  user_email: z.string().nullable(),
  user_role: z.string().nullable(),
  action: z.string(),
  resource_type: z.string(),
  resource_id: z.string().nullable(),
  details: z.record(z.unknown()).nullable(),
  ip_address: z.string().nullable(),
  user_agent: z.string().nullable(),
});

export const AuditLogListSchema = z.object({
  items: z.array(AuditLogSchema),
  total: z.number(),
});

export type AuditLog = z.infer<typeof AuditLogSchema>;
export type AuditLogList = z.infer<typeof AuditLogListSchema>;
