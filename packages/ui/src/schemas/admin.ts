import { z } from 'zod';

// LLM Config
export const LLMProviderSchema = z.object({
  id: z.string(),
  provider: z.string(),
  is_active: z.boolean(),
  is_default: z.boolean(),
  base_url: z.string(),
  api_key_set: z.boolean(),
  default_model: z.string(),
  max_tokens: z.number(),
  temperature: z.number(),
  rate_limit_rpm: z.number().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const LLMTestResultSchema = z.object({
  provider: z.string(),
  success: z.boolean(),
  message: z.string(),
  latency_ms: z.number().nullable(),
});

// User Management
export const AdminUserSchema = z.object({
  id: z.string(),
  keycloak_id: z.string(),
  email: z.string(),
  first_name: z.string(),
  last_name: z.string(),
  phone: z.string().nullable(),
  role: z.string(),
  is_active: z.boolean(),
  last_login_at: z.string().nullable(),
  application_count: z.number(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const AdminUserListSchema = z.object({
  items: z.array(AdminUserSchema),
  total: z.number(),
});

// System Health
export const ComponentHealthSchema = z.object({
  name: z.string(),
  status: z.string(),
  message: z.string(),
  latency_ms: z.number().nullable(),
  details: z.record(z.unknown()).nullable(),
});

export const SystemHealthSchema = z.object({
  overall_status: z.string(),
  components: z.array(ComponentHealthSchema),
  checked_at: z.string(),
});

// Analytics
export const ApprovalRateByBandSchema = z.object({
  risk_band: z.string(),
  total: z.number(),
  approved: z.number(),
  rate: z.number().nullable(),
});

export const OverrideStatsSchema = z.object({
  total_decisions: z.number(),
  total_overrides: z.number(),
  override_rate: z.number().nullable(),
  ai_approve_servicer_deny: z.number(),
  ai_deny_servicer_approve: z.number(),
  ai_conditional_servicer_different: z.number(),
});

export const ProcessingTimeStatsSchema = z.object({
  average_hours: z.number().nullable(),
  median_hours: z.number().nullable(),
  min_hours: z.number().nullable(),
  max_hours: z.number().nullable(),
});

export const VolumeByStatusSchema = z.object({
  status: z.string(),
  count: z.number(),
});

export const AnalyticsSchema = z.object({
  approval_rate_overall: z.number().nullable(),
  approval_rate_by_band: z.array(ApprovalRateByBandSchema),
  processing_time: ProcessingTimeStatsSchema,
  volume_by_status: z.array(VolumeByStatusSchema),
  override_stats: OverrideStatsSchema,
  total_applications: z.number(),
  total_decisions: z.number(),
});

export type LLMProvider = z.infer<typeof LLMProviderSchema>;
export type LLMTestResult = z.infer<typeof LLMTestResultSchema>;
export type AdminUser = z.infer<typeof AdminUserSchema>;
export type AdminUserList = z.infer<typeof AdminUserListSchema>;
export type ComponentHealth = z.infer<typeof ComponentHealthSchema>;
export type SystemHealth = z.infer<typeof SystemHealthSchema>;
export type Analytics = z.infer<typeof AnalyticsSchema>;
export type OverrideStats = z.infer<typeof OverrideStatsSchema>;
export type VolumeByStatus = z.infer<typeof VolumeByStatusSchema>;
export type ApprovalRateByBand = z.infer<typeof ApprovalRateByBandSchema>;

export interface LLMProviderUpdateInput {
  is_active?: boolean;
  is_default?: boolean;
  base_url?: string;
  api_key?: string;
  default_model?: string;
  max_tokens?: number;
  temperature?: number;
  rate_limit_rpm?: number;
}

export interface LLMProviderCreateInput {
  provider: string;
  base_url: string;
  api_key?: string;
  default_model: string;
  max_tokens?: number;
  temperature?: number;
  rate_limit_rpm?: number;
  is_active?: boolean;
  is_default?: boolean;
}

export interface AdminUserUpdateInput {
  role?: string;
  is_active?: boolean;
}
