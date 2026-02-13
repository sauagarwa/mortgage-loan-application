import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth/auth-provider';
import {
  createLLMConfig,
  getAnalytics,
  getLLMConfigs,
  getSystemHealth,
  getUsers,
  type ListUsersParams,
  testLLMConfig,
  updateLLMConfig,
  updateUser,
} from '../services/admin';
import type {
  AdminUserUpdateInput,
  LLMProviderCreateInput,
  LLMProviderUpdateInput,
} from '../schemas/admin';

// LLM Config
export function useLLMConfigs() {
  const { isAuthenticated, hasRole } = useAuth();
  return useQuery({
    queryKey: ['admin', 'llm-config'],
    queryFn: getLLMConfigs,
    enabled: isAuthenticated && hasRole('admin'),
  });
}

export function useCreateLLMConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: LLMProviderCreateInput) => createLLMConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'llm-config'] });
    },
  });
}

export function useUpdateLLMConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      provider,
      data,
    }: {
      provider: string;
      data: LLMProviderUpdateInput;
    }) => updateLLMConfig(provider, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'llm-config'] });
    },
  });
}

export function useTestLLMConfig() {
  return useMutation({
    mutationFn: (provider: string) => testLLMConfig(provider),
  });
}

// Users
export function useAdminUsers(params?: ListUsersParams) {
  const { isAuthenticated, hasRole } = useAuth();
  return useQuery({
    queryKey: ['admin', 'users', params],
    queryFn: () => getUsers(params),
    enabled: isAuthenticated && hasRole('admin'),
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      userId,
      data,
    }: {
      userId: string;
      data: AdminUserUpdateInput;
    }) => updateUser(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });
}

// System Health
export function useSystemHealth() {
  const { isAuthenticated, hasRole } = useAuth();
  return useQuery({
    queryKey: ['admin', 'health'],
    queryFn: getSystemHealth,
    enabled: isAuthenticated && hasRole('admin'),
    refetchInterval: 30000,
  });
}

// Analytics
export function useAnalytics() {
  const { isAuthenticated, hasRole } = useAuth();
  return useQuery({
    queryKey: ['servicer', 'analytics'],
    queryFn: getAnalytics,
    enabled:
      isAuthenticated && (hasRole('admin') || hasRole('loan_servicer')),
  });
}
