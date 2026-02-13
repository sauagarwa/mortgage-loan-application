import { apiGet, apiPost } from './api-client';
import type {
  DashboardStats,
  Decision,
  DecisionCreateInput,
  InfoRequestInput,
  RiskAssessment,
} from '../schemas/decisions';

export async function getRiskAssessment(
  applicationId: string,
): Promise<RiskAssessment> {
  return apiGet<RiskAssessment>(
    `/api/v1/applications/${applicationId}/risk-assessment`,
  );
}

export async function getDecision(applicationId: string): Promise<Decision> {
  return apiGet<Decision>(
    `/api/v1/applications/${applicationId}/decision`,
  );
}

export async function createDecision(
  applicationId: string,
  data: DecisionCreateInput,
): Promise<Decision> {
  return apiPost<Decision>(
    `/api/v1/applications/${applicationId}/decision`,
    data,
  );
}

export async function requestInfo(
  applicationId: string,
  data: InfoRequestInput,
): Promise<void> {
  await apiPost(
    `/api/v1/applications/${applicationId}/request-info`,
    data,
  );
}

export async function getDashboardStats(): Promise<DashboardStats> {
  return apiGet<DashboardStats>('/api/v1/servicer/dashboard');
}
