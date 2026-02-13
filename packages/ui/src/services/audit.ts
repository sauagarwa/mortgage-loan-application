import { apiGet } from './api-client';
import type { AuditLogList } from '../schemas/audit';

export interface ListAuditLogsParams {
  action?: string;
  resource_type?: string;
  resource_id?: string;
  user_email?: string;
  limit?: number;
  offset?: number;
}

export async function getAuditLogs(
  params?: ListAuditLogsParams,
): Promise<AuditLogList> {
  const searchParams = new URLSearchParams();
  if (params?.action) searchParams.set('action', params.action);
  if (params?.resource_type)
    searchParams.set('resource_type', params.resource_type);
  if (params?.resource_id)
    searchParams.set('resource_id', params.resource_id);
  if (params?.user_email) searchParams.set('user_email', params.user_email);
  if (params?.limit) searchParams.set('limit', String(params.limit));
  if (params?.offset) searchParams.set('offset', String(params.offset));

  const query = searchParams.toString();
  return apiGet<AuditLogList>(
    `/api/v1/audit-logs${query ? `?${query}` : ''}`,
  );
}
