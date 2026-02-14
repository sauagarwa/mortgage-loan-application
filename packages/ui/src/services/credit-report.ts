import { apiGet } from './api-client';
import type { CreditReport } from '../schemas/credit-report';

export async function getCreditReport(
  applicationId: string,
): Promise<CreditReport> {
  return apiGet<CreditReport>(
    `/api/v1/applications/${applicationId}/credit-report`,
  );
}
