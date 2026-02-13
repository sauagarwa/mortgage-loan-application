import { apiDelete, apiGet, apiUpload } from './api-client';
import type {
  DocumentDownloadResponse,
  DocumentList,
  DocumentUploadResponse,
} from '../schemas/documents';

export async function getDocuments(
  applicationId: string,
): Promise<DocumentList> {
  return apiGet<DocumentList>(
    `/api/v1/applications/${applicationId}/documents`,
  );
}

export async function uploadDocument(
  applicationId: string,
  file: File,
  documentType: string,
  description?: string,
): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('document_type', documentType);
  if (description) {
    formData.append('description', description);
  }

  return apiUpload<DocumentUploadResponse>(
    `/api/v1/applications/${applicationId}/documents`,
    formData,
  );
}

export async function getDocumentDownloadUrl(
  applicationId: string,
  documentId: string,
): Promise<DocumentDownloadResponse> {
  return apiGet<DocumentDownloadResponse>(
    `/api/v1/applications/${applicationId}/documents/${documentId}/download`,
  );
}

export async function deleteDocument(
  applicationId: string,
  documentId: string,
): Promise<void> {
  await apiDelete(
    `/api/v1/applications/${applicationId}/documents/${documentId}`,
  );
}
