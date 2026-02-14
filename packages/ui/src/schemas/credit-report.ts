import { z } from 'zod';

export const TradelineSchema = z.object({
  account_type: z.string(),
  creditor: z.string(),
  opened_date: z.string(),
  credit_limit: z.number().nullable(),
  current_balance: z.number(),
  monthly_payment: z.number(),
  status: z.string(),
  payment_history_24m: z.array(z.string()),
});

export const PublicRecordSchema = z.object({
  record_type: z.string(),
  filed_date: z.string(),
  status: z.string(),
  amount: z.number().nullable(),
});

export const InquirySchema = z.object({
  date: z.string(),
  creditor: z.string(),
  inquiry_type: z.string(),
});

export const FraudAlertSchema = z.object({
  alert_type: z.string(),
  severity: z.string(),
  description: z.string(),
});

export const CollectionSchema = z.object({
  agency: z.string(),
  original_creditor: z.string(),
  amount: z.number(),
  status: z.string(),
  reported_date: z.string(),
});

export const CreditReportSchema = z.object({
  id: z.string(),
  application_id: z.string(),
  credit_score: z.number(),
  score_model: z.string(),
  score_factors: z.array(z.string()),
  tradelines: z.array(TradelineSchema),
  public_records: z.array(PublicRecordSchema),
  inquiries: z.array(InquirySchema),
  collections: z.array(CollectionSchema),
  fraud_alerts: z.array(FraudAlertSchema),
  fraud_score: z.number(),
  total_accounts: z.number(),
  open_accounts: z.number(),
  credit_utilization: z.number().nullable(),
  oldest_account_months: z.number().nullable(),
  avg_account_age_months: z.number().nullable(),
  on_time_payments_pct: z.number().nullable(),
  late_payments_30d: z.number(),
  late_payments_60d: z.number(),
  late_payments_90d: z.number(),
  pulled_at: z.string().nullable(),
});

export type Tradeline = z.infer<typeof TradelineSchema>;
export type PublicRecord = z.infer<typeof PublicRecordSchema>;
export type Inquiry = z.infer<typeof InquirySchema>;
export type FraudAlert = z.infer<typeof FraudAlertSchema>;
export type Collection = z.infer<typeof CollectionSchema>;
export type CreditReport = z.infer<typeof CreditReportSchema>;
