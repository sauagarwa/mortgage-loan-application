import { z } from 'zod';

export const RiskDimensionScoreSchema = z.object({
  name: z.string(),
  score: z.number(),
  weight: z.number(),
  weighted_score: z.number(),
  agent: z.string(),
  positive_factors: z.array(z.string()),
  risk_factors: z.array(z.string()),
  mitigating_factors: z.array(z.string()),
  explanation: z.string().nullable(),
});

export const RiskConditionSchema = z.object({
  condition: z.string(),
  status: z.string().default('pending'),
});

export const RiskAssessmentSchema = z.object({
  id: z.string(),
  application_id: z.string(),
  status: z.string(),
  overall_score: z.number().nullable(),
  risk_band: z.string().nullable(),
  confidence: z.number().nullable(),
  recommendation: z.string().nullable(),
  summary: z.string().nullable(),
  dimensions: z.array(RiskDimensionScoreSchema).default([]),
  conditions: z.array(RiskConditionSchema).default([]),
  processing_metadata: z.record(z.unknown()).nullable(),
});

export const DecisionSchema = z.object({
  id: z.string(),
  application_id: z.string(),
  decision: z.string(),
  ai_recommendation: z.string().nullable(),
  servicer_agreed_with_ai: z.boolean().nullable(),
  override_justification: z.string().nullable(),
  conditions: z.array(z.string()),
  adverse_action_reasons: z.array(z.string()),
  interest_rate: z.number().nullable(),
  approved_loan_amount: z.number().nullable(),
  approved_term_years: z.number().nullable(),
  monthly_payment: z.number().nullable(),
  notes: z.string().nullable(),
  explanation: z.string().nullable(),
  decided_by_name: z.string().nullable(),
  decided_by_role: z.string().nullable(),
  decided_at: z.string().nullable(),
});

export const DashboardStatsSchema = z.object({
  pending_review: z.number(),
  in_progress: z.number(),
  decided_today: z.number(),
  average_processing_time_hours: z.number().nullable(),
  approval_rate: z.number().nullable(),
  risk_distribution: z.object({
    low: z.number(),
    medium: z.number(),
    high: z.number(),
    very_high: z.number(),
  }),
  recent_applications: z.array(
    z.object({
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
    }),
  ),
});

export type RiskDimensionScore = z.infer<typeof RiskDimensionScoreSchema>;
export type RiskCondition = z.infer<typeof RiskConditionSchema>;
export type RiskAssessment = z.infer<typeof RiskAssessmentSchema>;
export type Decision = z.infer<typeof DecisionSchema>;
export type DashboardStats = z.infer<typeof DashboardStatsSchema>;

export interface DecisionCreateInput {
  decision: 'approved' | 'denied' | 'conditionally_approved';
  conditions?: string[];
  adverse_action_reasons?: string[];
  interest_rate?: number;
  approved_loan_amount?: number;
  approved_term_years?: number;
  notes?: string;
  override_ai_recommendation?: boolean;
  override_justification?: string;
}

export interface InfoRequestItem {
  type: 'document' | 'clarification';
  document_type?: string;
  description?: string;
  question?: string;
}

export interface InfoRequestInput {
  requested_items: InfoRequestItem[];
  due_date?: string;
}
