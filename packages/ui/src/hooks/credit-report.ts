import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../auth/auth-provider';
import { getCreditReport } from '../services/credit-report';

export function useCreditReport(applicationId: string | undefined) {
  const { isAuthenticated } = useAuth();

  return useQuery({
    queryKey: ['credit-report', applicationId],
    queryFn: () => getCreditReport(applicationId!),
    enabled: isAuthenticated && !!applicationId,
    retry: false,
  });
}
