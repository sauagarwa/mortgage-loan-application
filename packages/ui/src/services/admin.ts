import { apiGet, apiPost, apiPut } from './api-client';
import type {
  AdminUserList,
  AdminUser,
  AdminUserUpdateInput,
  Analytics,
  LLMProvider,
  LLMProviderCreateInput,
  LLMProviderUpdateInput,
  LLMTestResult,
  SystemHealth,
} from '../schemas/admin';

// LLM Config
export async function getLLMConfigs(): Promise<LLMProvider[]> {
  return apiGet<LLMProvider[]>('/api/v1/admin/llm-config');
}

export async function createLLMConfig(
  data: LLMProviderCreateInput,
): Promise<LLMProvider> {
  return apiPost<LLMProvider>('/api/v1/admin/llm-config', data);
}

export async function updateLLMConfig(
  provider: string,
  data: LLMProviderUpdateInput,
): Promise<LLMProvider> {
  return apiPut<LLMProvider>(`/api/v1/admin/llm-config/${provider}`, data);
}

export async function testLLMConfig(
  provider: string,
): Promise<LLMTestResult> {
  return apiPost<LLMTestResult>(
    `/api/v1/admin/llm-config/${provider}/test`,
  );
}

// Users
export interface ListUsersParams {
  search?: string;
  role?: string;
  is_active?: boolean;
  limit?: number;
  offset?: number;
}

export async function getUsers(
  params?: ListUsersParams,
): Promise<AdminUserList> {
  const searchParams = new URLSearchParams();
  if (params?.search) searchParams.set('search', params.search);
  if (params?.role) searchParams.set('role', params.role);
  if (params?.is_active !== undefined)
    searchParams.set('is_active', String(params.is_active));
  if (params?.limit) searchParams.set('limit', String(params.limit));
  if (params?.offset) searchParams.set('offset', String(params.offset));
  const query = searchParams.toString();
  return apiGet<AdminUserList>(
    `/api/v1/admin/users${query ? `?${query}` : ''}`,
  );
}

export async function getUser(userId: string): Promise<AdminUser> {
  return apiGet<AdminUser>(`/api/v1/admin/users/${userId}`);
}

export async function updateUser(
  userId: string,
  data: AdminUserUpdateInput,
): Promise<AdminUser> {
  return apiPut<AdminUser>(`/api/v1/admin/users/${userId}`, data);
}

// System Health
export async function getSystemHealth(): Promise<SystemHealth> {
  return apiGet<SystemHealth>('/api/v1/admin/health');
}

// Analytics
export async function getAnalytics(): Promise<Analytics> {
  return apiGet<Analytics>('/api/v1/servicer/analytics');
}
