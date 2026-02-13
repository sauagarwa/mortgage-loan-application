import { createFileRoute, Link } from '@tanstack/react-router';
import { useApplication } from '../../hooks/applications';
import { useDocuments, useUploadDocument } from '../../hooks/documents';
import { Badge } from '../../components/atoms/badge/badge';
import { Button } from '../../components/atoms/button/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../../components/atoms/card/card';
import { ArrowLeft, FileUp, FileText, Loader2, Upload, CheckCircle2, AlertCircle } from 'lucide-react';
import { useRef, useState } from 'react';
import { DOCUMENT_TYPE_LABELS } from '../../schemas/documents';
import { useApplicationWebSocket } from '../../hooks/useWebSocket';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const Route = createFileRoute('/applications/$applicationId' as any)({
  component: ApplicationDetailPage,
});

const STATUS_LABELS: Record<string, string> = {
  draft: 'Draft',
  submitted: 'Submitted',
  documents_processing: 'Processing Documents',
  risk_assessment_in_progress: 'Risk Assessment In Progress',
  under_review: 'Under Review',
  additional_info_requested: 'Additional Info Requested',
  approved: 'Approved',
  conditionally_approved: 'Conditionally Approved',
  denied: 'Denied',
  withdrawn: 'Withdrawn',
};

function ApplicationDetailPage() {
  const { applicationId } = Route.useParams();
  const { data: app, isLoading } = useApplication(applicationId);
  const { data: documents } = useDocuments(applicationId);
  const uploadDoc = useUploadDocument(applicationId);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadType, setUploadType] = useState('pay_stub');
  useApplicationWebSocket(applicationId);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl p-4 sm:p-6 lg:p-8">
        <p className="text-muted-foreground">Loading application...</p>
      </div>
    );
  }

  if (!app) {
    return (
      <div className="mx-auto max-w-5xl p-4 sm:p-6 lg:p-8">
        <p className="text-muted-foreground">Application not found.</p>
      </div>
    );
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await uploadDoc.mutateAsync({ file, documentType: uploadType });
    } catch {
      // Error handled by mutation
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const personalInfo = app.personal_info as Record<string, unknown>;
  const employmentInfo = app.employment_info as Record<string, unknown>;
  const financialInfo = app.financial_info as Record<string, unknown>;
  const propertyInfo = app.property_info as Record<string, unknown>;

  return (
    <div className="mx-auto max-w-5xl p-4 sm:p-6 lg:p-8">
      <Link
        to="/applications"
        className="mb-4 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Applications
      </Link>

      <div className="mb-6 flex items-start justify-between">
        <div>
          <div className="mb-1 flex items-center gap-3">
            <h1 className="text-2xl font-bold">{app.application_number}</h1>
            <Badge>{STATUS_LABELS[app.status] ?? app.status}</Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            {app.loan_product_name} &middot; Created{' '}
            {app.created_at
              ? new Date(app.created_at).toLocaleDateString()
              : ''}
          </p>
        </div>
        {app.loan_amount != null && (
          <div className="text-right">
            <p className="text-2xl font-bold">
              ${app.loan_amount.toLocaleString()}
            </p>
            <p className="text-sm text-muted-foreground">Loan Amount</p>
          </div>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          {/* Personal Info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Personal Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2 text-sm sm:grid-cols-2">
                <div>
                  <span className="text-muted-foreground">Name: </span>
                  {String(personalInfo.first_name ?? '')} {String(personalInfo.last_name ?? '')}
                </div>
                <div>
                  <span className="text-muted-foreground">Email: </span>
                  {String(personalInfo.email ?? 'N/A')}
                </div>
                <div>
                  <span className="text-muted-foreground">Phone: </span>
                  {String(personalInfo.phone ?? 'N/A')}
                </div>
                <div>
                  <span className="text-muted-foreground">Citizenship: </span>
                  {String(personalInfo.citizenship_status ?? 'N/A')}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Employment */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Employment</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2 text-sm sm:grid-cols-2">
                <div>
                  <span className="text-muted-foreground">Employer: </span>
                  {String(employmentInfo.employer_name ?? 'N/A')}
                </div>
                <div>
                  <span className="text-muted-foreground">Title: </span>
                  {String(employmentInfo.job_title ?? 'N/A')}
                </div>
                <div>
                  <span className="text-muted-foreground">Annual Income: </span>
                  ${Number(employmentInfo.annual_income ?? 0).toLocaleString()}
                </div>
                <div>
                  <span className="text-muted-foreground">Years at Job: </span>
                  {String(employmentInfo.years_at_current_job ?? 'N/A')}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Financial */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Financial Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2 text-sm sm:grid-cols-2">
                <div>
                  <span className="text-muted-foreground">Credit Score: </span>
                  {String(financialInfo.credit_score_self_reported ?? 'N/A')}
                </div>
                <div>
                  <span className="text-muted-foreground">Total Assets: </span>
                  ${Number(financialInfo.total_assets ?? 0).toLocaleString()}
                </div>
                <div>
                  <span className="text-muted-foreground">Liquid Assets: </span>
                  ${Number(financialInfo.liquid_assets ?? 0).toLocaleString()}
                </div>
                {app.dti_ratio != null && (
                  <div>
                    <span className="text-muted-foreground">DTI Ratio: </span>
                    {app.dti_ratio.toFixed(1)}%
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Property */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Property Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2 text-sm sm:grid-cols-2">
                <div>
                  <span className="text-muted-foreground">Type: </span>
                  {String(propertyInfo.property_type ?? 'N/A')}
                </div>
                <div>
                  <span className="text-muted-foreground">Use: </span>
                  {String(propertyInfo.property_use ?? 'N/A')}
                </div>
                <div>
                  <span className="text-muted-foreground">Purchase Price: </span>
                  ${Number(propertyInfo.purchase_price ?? 0).toLocaleString()}
                </div>
                <div>
                  <span className="text-muted-foreground">Down Payment: </span>
                  ${Number(propertyInfo.down_payment ?? 0).toLocaleString()}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar: Documents, Risk Assessment, Decision */}
        <div className="space-y-6">
          {/* Risk Assessment Summary */}
          {app.risk_assessment && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  {(app.risk_assessment.status === 'pending' || app.risk_assessment.status === 'in_progress') && (
                    <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                  )}
                  Risk Assessment
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Status</span>
                    <Badge variant="secondary">{app.risk_assessment.status}</Badge>
                  </div>
                  {app.risk_assessment.overall_score != null && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Score</span>
                      <span className="font-medium">
                        {app.risk_assessment.overall_score}
                      </span>
                    </div>
                  )}
                  {app.risk_assessment.risk_band && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Risk Band</span>
                      <Badge variant="outline" className="capitalize">
                        {app.risk_assessment.risk_band}
                      </Badge>
                    </div>
                  )}
                  {app.risk_assessment.recommendation && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Recommendation</span>
                      <span className="font-medium capitalize">
                        {app.risk_assessment.recommendation.replace(/_/g, ' ')}
                      </span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Decision */}
          {app.decision && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Decision</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Decision</span>
                    <Badge className="capitalize">
                      {app.decision.decision.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                  {app.decision.decided_at && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Date</span>
                      <span>
                        {new Date(app.decision.decided_at).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Documents */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Documents</CardTitle>
              <CardDescription>
                {documents?.total ?? 0} uploaded
              </CardDescription>
            </CardHeader>
            <CardContent>
              {app.status === 'draft' && (
                <div className="mb-4 space-y-2">
                  <select
                    className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                    value={uploadType}
                    onChange={(e) => setUploadType(e.target.value)}
                  >
                    {Object.entries(DOCUMENT_TYPE_LABELS).map(([val, label]) => (
                      <option key={val} value={val}>
                        {label}
                      </option>
                    ))}
                  </select>
                  <input
                    ref={fileInputRef}
                    type="file"
                    className="hidden"
                    accept=".pdf,.png,.jpg,.jpeg,.tiff"
                    onChange={handleFileUpload}
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploadDoc.isPending}
                  >
                    <Upload className="h-4 w-4" />
                    {uploadDoc.isPending ? 'Uploading...' : 'Upload Document'}
                  </Button>
                </div>
              )}

              {documents?.items.length ? (
                <div className="space-y-2">
                  {documents.items.map((doc) => (
                    <div
                      key={doc.id}
                      className="flex items-center gap-2 rounded-md border p-2 text-sm"
                    >
                      {doc.status === 'processing' ? (
                        <Loader2 className="h-4 w-4 shrink-0 animate-spin text-blue-500" />
                      ) : doc.status === 'processed' ? (
                        <CheckCircle2 className="h-4 w-4 shrink-0 text-green-500" />
                      ) : doc.status === 'error' ? (
                        <AlertCircle className="h-4 w-4 shrink-0 text-destructive" />
                      ) : (
                        <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                      )}
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-medium">{doc.filename}</p>
                        <p className="text-xs text-muted-foreground">
                          {DOCUMENT_TYPE_LABELS[doc.document_type] ?? doc.document_type}
                          {doc.extraction_confidence != null && (
                            <span className="ml-1">
                              ({Math.round(doc.extraction_confidence * 100)}% confidence)
                            </span>
                          )}
                        </p>
                      </div>
                      <Badge variant="outline" className="shrink-0 text-xs">
                        {doc.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-4 text-center text-sm text-muted-foreground">
                  <FileUp className="mx-auto mb-2 h-8 w-8 text-muted-foreground/50" />
                  No documents uploaded
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
