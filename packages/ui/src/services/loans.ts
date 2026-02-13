import { apiGet, apiPost } from './api-client';
import type {
  EligibilityCheckRequest,
  EligibilityCheckResponse,
  LoanProduct,
  LoanProductList,
} from '../schemas/loans';

export async function getLoanProducts(params?: {
  type?: string;
  term?: number;
}): Promise<LoanProductList> {
  const searchParams = new URLSearchParams();
  if (params?.type) searchParams.set('type', params.type);
  if (params?.term) searchParams.set('term', String(params.term));

  const query = searchParams.toString();
  const path = `/api/v1/loans${query ? `?${query}` : ''}`;
  return apiGet<LoanProductList>(path);
}

export async function getLoanProduct(loanId: string): Promise<LoanProduct> {
  return apiGet<LoanProduct>(`/api/v1/loans/${loanId}`);
}

export async function checkEligibility(
  loanId: string,
  data: EligibilityCheckRequest,
): Promise<EligibilityCheckResponse> {
  return apiPost<EligibilityCheckResponse>(
    `/api/v1/loans/${loanId}/eligibility-check`,
    data,
  );
}
