import { apiDelete, apiFetch, apiGet } from './api-client';
import type { NotificationList, UnreadCount } from '../schemas/notifications';

export interface ListNotificationsParams {
  unread_only?: boolean;
  limit?: number;
  offset?: number;
}

export async function getNotifications(
  params?: ListNotificationsParams,
): Promise<NotificationList> {
  const searchParams = new URLSearchParams();
  if (params?.unread_only) searchParams.set('unread_only', 'true');
  if (params?.limit) searchParams.set('limit', String(params.limit));
  if (params?.offset) searchParams.set('offset', String(params.offset));

  const query = searchParams.toString();
  return apiGet<NotificationList>(
    `/api/v1/notifications${query ? `?${query}` : ''}`,
  );
}

export async function getUnreadCount(): Promise<UnreadCount> {
  return apiGet<UnreadCount>('/api/v1/notifications/unread-count');
}

export async function markNotificationRead(id: string): Promise<void> {
  await apiFetch(`/api/v1/notifications/${id}/read`, { method: 'PUT' });
}

export async function markAllNotificationsRead(): Promise<void> {
  await apiFetch('/api/v1/notifications/mark-all-read', { method: 'POST' });
}

export async function deleteNotification(id: string): Promise<void> {
  await apiDelete(`/api/v1/notifications/${id}`);
}
