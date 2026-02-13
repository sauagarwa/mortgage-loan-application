import { z } from 'zod';

export const LoanProductSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.string(),
  term_years: z.number(),
  rate_type: z.string(),
  min_down_payment_pct: z.number(),
  min_credit_score: z.number().nullable(),
  max_dti_ratio: z.number().nullable(),
  max_loan_amount: z.number().nullable(),
  description: z.string().nullable(),
  eligibility_requirements: z.array(z.string()),
  features: z.array(z.string()),
  is_active: z.boolean(),
});

export const LoanProductListSchema = z.object({
  items: z.array(LoanProductSchema),
  total: z.number(),
});

export const EligibilityCheckResponseSchema = z.object({
  eligible: z.boolean(),
  estimated_rate: z.string().nullable(),
  estimated_monthly_payment: z.number().nullable(),
  max_loan_amount: z.number().nullable(),
  warnings: z.array(z.string()),
  suggestions: z.array(z.string()),
});

export type LoanProduct = z.infer<typeof LoanProductSchema>;
export type LoanProductList = z.infer<typeof LoanProductListSchema>;
export type EligibilityCheckResponse = z.infer<typeof EligibilityCheckResponseSchema>;

export interface EligibilityCheckRequest {
  annual_income: number;
  monthly_debts: number;
  credit_score_range: string;
  down_payment_amount: number;
  property_value: number;
  citizenship_status: string;
}
