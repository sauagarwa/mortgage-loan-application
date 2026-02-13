import { z } from 'zod';

export const NotificationSchema = z.object({
  id: z.string(),
  type: z.string(),
  title: z.string(),
  message: z.string(),
  application_id: z.string().nullable(),
  is_read: z.boolean(),
  created_at: z.string(),
});

export const NotificationListSchema = z.object({
  items: z.array(NotificationSchema),
  total: z.number(),
  unread_count: z.number(),
});

export const UnreadCountSchema = z.object({
  unread_count: z.number(),
});

export type Notification = z.infer<typeof NotificationSchema>;
export type NotificationList = z.infer<typeof NotificationListSchema>;
export type UnreadCount = z.infer<typeof UnreadCountSchema>;
