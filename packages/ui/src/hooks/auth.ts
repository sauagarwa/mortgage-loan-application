import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth/auth-provider';
import { apiGet, apiPut } from '../services/api-client';

interface UserProfile {
  keycloak_id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  role: string;
  is_active: boolean;
}

interface UserProfileUpdate {
  phone?: string;
}

export function useUserProfile() {
  const { isAuthenticated } = useAuth();

  return useQuery({
    queryKey: ['user', 'profile'],
    queryFn: () => apiGet<UserProfile>('/api/v1/auth/me'),
    enabled: isAuthenticated,
  });
}

export function useUpdateUserProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UserProfileUpdate) =>
      apiPut<UserProfile>('/api/v1/auth/me', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'profile'] });
    },
  });
}

export function useRequireAuth() {
  const { isAuthenticated, isLoading, login } = useAuth();

  return {
    isAuthenticated,
    isLoading,
    ensureAuth: () => {
      if (!isAuthenticated && !isLoading) {
        login();
      }
    },
  };
}
