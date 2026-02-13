import { apiDelete, apiGet, apiPost, apiPut } from './api-client';
import type {
  Application,
  ApplicationCreateInput,
  ApplicationSubmitResponse,
  ApplicationUpdateInput,
  PaginatedApplications,
} from '../schemas/applications';

export interface ListApplicationsParams {
  status?: string;
  risk_rating?: string;
  assigned_to_me?: boolean;
  limit?: number;
  offset?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export async function getApplications(
  params?: ListApplicationsParams,
): Promise<PaginatedApplications> {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.set('status', params.status);
  if (params?.risk_rating) searchParams.set('risk_rating', params.risk_rating);
  if (params?.assigned_to_me) searchParams.set('assigned_to_me', 'true');
  if (params?.limit) searchParams.set('limit', String(params.limit));
  if (params?.offset) searchParams.set('offset', String(params.offset));
  if (params?.sort_by) searchParams.set('sort_by', params.sort_by);
  if (params?.sort_order) searchParams.set('sort_order', params.sort_order);

  const query = searchParams.toString();
  return apiGet<PaginatedApplications>(
    `/api/v1/applications${query ? `?${query}` : ''}`,
  );
}

export async function getApplication(
  applicationId: string,
): Promise<Application> {
  return apiGet<Application>(`/api/v1/applications/${applicationId}`);
}

export async function createApplication(
  data: ApplicationCreateInput,
): Promise<Application> {
  return apiPost<Application>('/api/v1/applications', data);
}

export async function updateApplication(
  applicationId: string,
  data: ApplicationUpdateInput,
): Promise<Application> {
  return apiPut<Application>(`/api/v1/applications/${applicationId}`, data);
}

export async function submitApplication(
  applicationId: string,
): Promise<ApplicationSubmitResponse> {
  return apiPost<ApplicationSubmitResponse>(
    `/api/v1/applications/${applicationId}/submit`,
  );
}

export async function assignApplication(
  applicationId: string,
  servicerId: string,
): Promise<void> {
  await apiPost(`/api/v1/applications/${applicationId}/assign`, {
    servicer_id: servicerId,
  });
}
