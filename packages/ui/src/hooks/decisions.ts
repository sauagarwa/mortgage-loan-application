import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth/auth-provider';
import {
  createDecision,
  getDashboardStats,
  getDecision,
  getRiskAssessment,
  requestInfo,
} from '../services/decisions';
import type { DecisionCreateInput, InfoRequestInput } from '../schemas/decisions';

export function useRiskAssessment(applicationId: string | undefined) {
  const { isAuthenticated } = useAuth();

  return useQuery({
    queryKey: ['risk-assessment', applicationId],
    queryFn: () => getRiskAssessment(applicationId!),
    enabled: isAuthenticated && !!applicationId,
  });
}

export function useDecision(applicationId: string | undefined) {
  const { isAuthenticated } = useAuth();

  return useQuery({
    queryKey: ['decision', applicationId],
    queryFn: () => getDecision(applicationId!),
    enabled: isAuthenticated && !!applicationId,
    retry: false,
  });
}

export function useCreateDecision(applicationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: DecisionCreateInput) =>
      createDecision(applicationId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['decision', applicationId],
      });
      queryClient.invalidateQueries({
        queryKey: ['applications', applicationId],
      });
      queryClient.invalidateQueries({ queryKey: ['applications'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}

export function useRequestInfo(applicationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: InfoRequestInput) => requestInfo(applicationId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['applications', applicationId],
      });
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    },
  });
}

export function useDashboardStats() {
  const { isAuthenticated } = useAuth();

  return useQuery({
    queryKey: ['dashboard'],
    queryFn: getDashboardStats,
    enabled: isAuthenticated,
  });
}
