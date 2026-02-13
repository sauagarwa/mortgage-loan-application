import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../auth/auth-provider';
import { getAuditLogs, type ListAuditLogsParams } from '../services/audit';

export function useAuditLogs(params?: ListAuditLogsParams) {
  const { isAuthenticated, hasRole } = useAuth();
  return useQuery({
    queryKey: ['audit-logs', params],
    queryFn: () => getAuditLogs(params),
    enabled: isAuthenticated && (hasRole('admin') || hasRole('loan_servicer')),
  });
}
