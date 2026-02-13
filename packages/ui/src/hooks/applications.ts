import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth/auth-provider';
import {
  createApplication,
  getApplication,
  getApplications,
  submitApplication,
  updateApplication,
  type ListApplicationsParams,
} from '../services/applications';
import type {
  ApplicationCreateInput,
  ApplicationUpdateInput,
} from '../schemas/applications';

export function useApplications(params?: ListApplicationsParams) {
  const { isAuthenticated } = useAuth();

  return useQuery({
    queryKey: ['applications', params],
    queryFn: () => getApplications(params),
    enabled: isAuthenticated,
  });
}

export function useApplication(applicationId: string | undefined) {
  const { isAuthenticated } = useAuth();

  return useQuery({
    queryKey: ['applications', applicationId],
    queryFn: () => getApplication(applicationId!),
    enabled: isAuthenticated && !!applicationId,
    refetchInterval: (query) => {
      // Auto-poll while risk assessment is in progress
      const app = query.state.data;
      const riskStatus = app?.risk_assessment?.status;
      if (riskStatus === 'pending' || riskStatus === 'in_progress') {
        return 5000;
      }
      // Also poll when submitted but not yet under_review
      if (app?.status === 'submitted') {
        return 5000;
      }
      return false;
    },
  });
}

export function useCreateApplication() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ApplicationCreateInput) => createApplication(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    },
  });
}

export function useUpdateApplication(applicationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ApplicationUpdateInput) =>
      updateApplication(applicationId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['applications', applicationId],
      });
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    },
  });
}

export function useSubmitApplication(applicationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => submitApplication(applicationId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['applications', applicationId],
      });
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    },
  });
}
