import { z } from 'zod';

export const DocumentSchema = z.object({
  id: z.string(),
  document_type: z.string(),
  filename: z.string(),
  file_size: z.number(),
  mime_type: z.string(),
  status: z.string(),
  extracted_data: z.record(z.unknown()).nullable(),
  extraction_confidence: z.number().nullable(),
  uploaded_at: z.string().nullable(),
  processed_at: z.string().nullable(),
});

export const DocumentListSchema = z.object({
  items: z.array(DocumentSchema),
  total: z.number(),
});

export const DocumentUploadResponseSchema = z.object({
  id: z.string(),
  application_id: z.string(),
  document_type: z.string(),
  filename: z.string(),
  file_size: z.number(),
  mime_type: z.string(),
  status: z.string(),
  uploaded_at: z.string().nullable(),
});

export const DocumentDownloadResponseSchema = z.object({
  download_url: z.string(),
  expires_in_seconds: z.number(),
});

export type DocumentItem = z.infer<typeof DocumentSchema>;
export type DocumentList = z.infer<typeof DocumentListSchema>;
export type DocumentUploadResponse = z.infer<typeof DocumentUploadResponseSchema>;
export type DocumentDownloadResponse = z.infer<typeof DocumentDownloadResponseSchema>;

export const DOCUMENT_TYPE_LABELS: Record<string, string> = {
  government_id: 'Government ID',
  pay_stub: 'Pay Stub',
  w2: 'W-2 Form',
  tax_return: 'Tax Return',
  bank_statement: 'Bank Statement',
  employment_letter: 'Employment Letter',
  proof_of_assets: 'Proof of Assets',
  purchase_agreement: 'Purchase Agreement',
  rental_history: 'Rental History',
  other: 'Other',
};
