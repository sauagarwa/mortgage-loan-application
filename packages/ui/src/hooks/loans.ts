import { useMutation, useQuery } from '@tanstack/react-query';
import { useAuth } from '../auth/auth-provider';
import {
  checkEligibility,
  getLoanProduct,
  getLoanProducts,
} from '../services/loans';
import type { EligibilityCheckRequest } from '../schemas/loans';

export function useLoanProducts(params?: { type?: string; term?: number }) {
  const { isAuthenticated } = useAuth();

  return useQuery({
    queryKey: ['loans', params],
    queryFn: () => getLoanProducts(params),
    enabled: isAuthenticated,
  });
}

export function useLoanProduct(loanId: string | undefined) {
  const { isAuthenticated } = useAuth();

  return useQuery({
    queryKey: ['loans', loanId],
    queryFn: () => getLoanProduct(loanId!),
    enabled: isAuthenticated && !!loanId,
  });
}

export function useEligibilityCheck(loanId: string) {
  return useMutation({
    mutationFn: (data: EligibilityCheckRequest) =>
      checkEligibility(loanId, data),
  });
}
