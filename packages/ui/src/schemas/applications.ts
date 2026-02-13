import { z } from 'zod';

export const DocumentSummarySchema = z.object({
  id: z.string(),
  document_type: z.string(),
  filename: z.string(),
  status: z.string(),
  uploaded_at: z.string().nullable(),
});

export const RiskAssessmentSummarySchema = z.object({
  id: z.string(),
  status: z.string(),
  overall_score: z.number().nullable(),
  risk_band: z.string().nullable(),
  recommendation: z.string().nullable(),
});

export const DecisionSummarySchema = z.object({
  id: z.string(),
  decision: z.string(),
  decided_at: z.string().nullable(),
});

export const ApplicationSchema = z.object({
  id: z.string(),
  application_number: z.string(),
  status: z.string(),
  loan_product_id: z.string(),
  loan_product_name: z.string().nullable(),
  loan_product_type: z.string().nullable(),
  applicant_id: z.string(),
  applicant_name: z.string().nullable(),
  assigned_servicer_id: z.string().nullable(),
  assigned_servicer_name: z.string().nullable(),
  personal_info: z.record(z.unknown()).default({}),
  employment_info: z.record(z.unknown()).default({}),
  financial_info: z.record(z.unknown()).default({}),
  property_info: z.record(z.unknown()).default({}),
  declarations: z.record(z.unknown()).default({}),
  loan_amount: z.number().nullable(),
  down_payment: z.number().nullable(),
  dti_ratio: z.number().nullable(),
  documents: z.array(DocumentSummarySchema).default([]),
  risk_assessment: RiskAssessmentSummarySchema.nullable(),
  decision: DecisionSummarySchema.nullable(),
  submitted_at: z.string().nullable(),
  decided_at: z.string().nullable(),
  created_at: z.string().nullable(),
  updated_at: z.string().nullable(),
});

export const ApplicationListItemSchema = z.object({
  id: z.string(),
  application_number: z.string(),
  status: z.string(),
  applicant_name: z.string().nullable(),
  loan_type: z.string().nullable(),
  loan_amount: z.number().nullable(),
  risk_score: z.number().nullable(),
  risk_band: z.string().nullable(),
  submitted_at: z.string().nullable(),
  created_at: z.string().nullable(),
  assigned_servicer: z.string().nullable(),
});

export const PaginatedApplicationsSchema = z.object({
  items: z.array(ApplicationListItemSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
});

export const ApplicationSubmitResponseSchema = z.object({
  id: z.string(),
  status: z.string(),
  submitted_at: z.string(),
  message: z.string(),
});

export type Application = z.infer<typeof ApplicationSchema>;
export type ApplicationListItem = z.infer<typeof ApplicationListItemSchema>;
export type PaginatedApplications = z.infer<typeof PaginatedApplicationsSchema>;
export type ApplicationSubmitResponse = z.infer<typeof ApplicationSubmitResponseSchema>;

export interface AddressInput {
  street: string;
  city: string;
  state: string;
  zip_code: string;
}

export interface PersonalInfoInput {
  first_name: string;
  last_name: string;
  date_of_birth?: string;
  ssn_last_four?: string;
  email: string;
  phone?: string;
  address?: AddressInput;
  citizenship_status?: string;
  visa_type?: string;
  years_in_country?: number;
}

export interface EmploymentInfoInput {
  employment_status?: string;
  employer_name?: string;
  job_title?: string;
  years_at_current_job?: number;
  years_in_field?: number;
  annual_income?: number;
  additional_income?: number;
  additional_income_source?: string;
  is_self_employed?: boolean;
}

export interface MonthlyDebtsInput {
  car_loan?: number;
  student_loans?: number;
  credit_cards?: number;
  other?: number;
}

export interface FinancialInfoInput {
  credit_score_self_reported?: number;
  has_credit_history?: boolean;
  monthly_debts?: MonthlyDebtsInput;
  total_assets?: number;
  liquid_assets?: number;
  checking_balance?: number;
  savings_balance?: number;
  retirement_accounts?: number;
  investment_accounts?: number;
  bankruptcy_history?: boolean;
  foreclosure_history?: boolean;
}

export interface PropertyInfoInput {
  property_type?: string;
  property_use?: string;
  purchase_price?: number;
  down_payment?: number;
  address?: AddressInput;
}

export interface DeclarationsInput {
  outstanding_judgments?: boolean;
  party_to_lawsuit?: boolean;
  federal_debt_delinquent?: boolean;
  alimony_obligation?: boolean;
  co_signer_on_other_loan?: boolean;
  us_citizen?: boolean;
  primary_residence?: boolean;
}

export interface ApplicationCreateInput {
  loan_product_id: string;
  personal_info?: PersonalInfoInput;
  employment_info?: EmploymentInfoInput;
  financial_info?: FinancialInfoInput;
  property_info?: PropertyInfoInput;
  declarations?: DeclarationsInput;
}

export interface ApplicationUpdateInput {
  loan_product_id?: string;
  personal_info?: PersonalInfoInput;
  employment_info?: EmploymentInfoInput;
  financial_info?: FinancialInfoInput;
  property_info?: PropertyInfoInput;
  declarations?: DeclarationsInput;
}
