import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../auth/auth-provider';
import {
  deleteDocument,
  getDocumentDownloadUrl,
  getDocuments,
  uploadDocument,
} from '../services/documents';

export function useDocuments(applicationId: string | undefined) {
  const { isAuthenticated } = useAuth();

  return useQuery({
    queryKey: ['documents', applicationId],
    queryFn: () => getDocuments(applicationId!),
    enabled: isAuthenticated && !!applicationId,
    refetchInterval: (query) => {
      // Auto-poll while any documents are still processing
      const items = query.state.data?.items;
      const hasProcessing = items?.some(
        (d) => d.status === 'uploaded' || d.status === 'processing'
      );
      return hasProcessing ? 5000 : false;
    },
  });
}

export function useUploadDocument(applicationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      file,
      documentType,
      description,
    }: {
      file: File;
      documentType: string;
      description?: string;
    }) => uploadDocument(applicationId, file, documentType, description),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['documents', applicationId],
      });
    },
  });
}

export function useDocumentDownloadUrl(
  applicationId: string,
  documentId: string,
) {
  const { isAuthenticated } = useAuth();

  return useQuery({
    queryKey: ['documents', applicationId, documentId, 'download'],
    queryFn: () => getDocumentDownloadUrl(applicationId, documentId),
    enabled: isAuthenticated && !!applicationId && !!documentId,
  });
}

export function useDeleteDocument(applicationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) =>
      deleteDocument(applicationId, documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['documents', applicationId],
      });
    },
  });
}
