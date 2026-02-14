import { createFileRoute, Link, useNavigate } from '@tanstack/react-router';
import { useState } from 'react';
import { useApplication } from '../../../hooks/applications';
import { useRiskAssessment, useDecision, useCreateDecision } from '../../../hooks/decisions';
import { useCreditReport } from '../../../hooks/credit-report';
import { useDocuments } from '../../../hooks/documents';
import { Badge } from '../../../components/atoms/badge/badge';
import { Button } from '../../../components/atoms/button/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../../../components/atoms/card/card';
import { CreditReportCard } from '../../../components/credit-report/credit-report-card';
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FileText,
  Shield,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { DOCUMENT_TYPE_LABELS } from '../../../schemas/documents';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const Route = createFileRoute('/servicer/review/$applicationId' as any)({
  component: ServicerReviewPage,
});

const RISK_COLORS: Record<string, string> = {
  low: 'text-green-600 bg-green-50',
  medium: 'text-yellow-600 bg-yellow-50',
  high: 'text-orange-600 bg-orange-50',
  very_high: 'text-red-600 bg-red-50',
  critical: 'text-red-700 bg-red-100',
};

function ServicerReviewPage() {
  const { applicationId } = Route.useParams();
  const navigate = useNavigate();
  const { data: app, isLoading: appLoading } = useApplication(applicationId);
  const { data: riskAssessment } = useRiskAssessment(applicationId);
  const { data: existingDecision } = useDecision(applicationId);
  const { data: creditReport } = useCreditReport(applicationId);
  const { data: documents } = useDocuments(applicationId);
  const createDecision = useCreateDecision(applicationId);

  const [showDecisionForm, setShowDecisionForm] = useState(false);
  const [decisionForm, setDecisionForm] = useState({
    decision: 'approved' as 'approved' | 'denied' | 'conditionally_approved',
    interest_rate: '',
    conditions: '',
    adverse_action_reasons: '',
    notes: '',
    override_ai_recommendation: false,
    override_justification: '',
  });

  if (appLoading) {
    return (
      <div className="mx-auto max-w-6xl p-4 sm:p-6 lg:p-8">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (!app) {
    return (
      <div className="mx-auto max-w-6xl p-4 sm:p-6 lg:p-8">
        <p className="text-muted-foreground">Application not found.</p>
      </div>
    );
  }

  const handleCreateDecision = async () => {
    try {
      await createDecision.mutateAsync({
        decision: decisionForm.decision,
        interest_rate: decisionForm.interest_rate
          ? Number(decisionForm.interest_rate)
          : undefined,
        conditions: decisionForm.conditions
          ? decisionForm.conditions.split('\n').filter(Boolean)
          : [],
        adverse_action_reasons: decisionForm.adverse_action_reasons
          ? decisionForm.adverse_action_reasons.split('\n').filter(Boolean)
          : [],
        notes: decisionForm.notes || undefined,
        override_ai_recommendation: decisionForm.override_ai_recommendation,
        override_justification: decisionForm.override_justification || undefined,
      });
      navigate({ to: '/servicer' });
    } catch {
      // Error handled by mutation
    }
  };

  const personalInfo = app.personal_info as Record<string, unknown>;
  const employmentInfo = app.employment_info as Record<string, unknown>;
  const financialInfo = app.financial_info as Record<string, unknown>;
  const propertyInfo = app.property_info as Record<string, unknown>;

  return (
    <div className="mx-auto max-w-6xl p-4 sm:p-6 lg:p-8">
      <Link
        to="/servicer"
        className="mb-4 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Queue
      </Link>

      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">
            Review: {app.application_number}
          </h1>
          <p className="text-sm text-muted-foreground">
            Applicant: {app.applicant_name} &middot; {app.loan_product_name}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge>{app.status.replace(/_/g, ' ')}</Badge>
          {app.loan_amount != null && (
            <span className="text-xl font-bold">
              ${app.loan_amount.toLocaleString()}
            </span>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main content - Application data */}
        <div className="space-y-6 lg:col-span-2">
          {/* Risk Assessment */}
          {app.risk_assessment?.status === 'in_progress' || app.risk_assessment?.status === 'pending' ? (
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
                  <CardTitle className="text-lg">AI Risk Assessment In Progress</CardTitle>
                </div>
                <CardDescription>
                  The AI risk engine is analyzing this application. Results will appear automatically.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3 rounded-lg border border-blue-200 bg-blue-50 p-4">
                  <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                  <div className="text-sm text-blue-800">
                    <p className="font-medium">Analyzing application data...</p>
                    <p className="text-blue-600">
                      Credit profile, income stability, debt ratios, and property assessment
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : riskAssessment ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Shield className="h-5 w-5" />
                    <CardTitle className="text-lg">AI Risk Assessment</CardTitle>
                  </div>
                  {riskAssessment.risk_band && (
                    <div
                      className={`rounded-full px-3 py-1 text-sm font-bold capitalize ${RISK_COLORS[riskAssessment.risk_band] ?? ''}`}
                    >
                      {riskAssessment.risk_band.replace('_', ' ')} Risk
                      {riskAssessment.overall_score != null &&
                        ` (${riskAssessment.overall_score})`}
                    </div>
                  )}
                </div>
                {riskAssessment.recommendation && (
                  <CardDescription>
                    AI Recommendation:{' '}
                    <span className="font-medium capitalize text-foreground">
                      {riskAssessment.recommendation.replace(/_/g, ' ')}
                    </span>
                    {riskAssessment.confidence != null && (
                      <span className="ml-2 text-muted-foreground">
                        (Confidence: {(riskAssessment.confidence * 100).toFixed(0)}%)
                      </span>
                    )}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent>
                {riskAssessment.summary && (
                  <p className="mb-4 text-sm">{riskAssessment.summary}</p>
                )}

                {/* Dimension scores */}
                {riskAssessment.dimensions.length > 0 && (
                  <div className="space-y-4">
                    {riskAssessment.dimensions.map((dim) => (
                      <div key={dim.name} className="rounded-lg border p-3">
                        <div className="mb-2 flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium capitalize">
                              {dim.name.replace(/_/g, ' ')}
                            </span>
                            <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                              {dim.agent === 'rule_engine' ? 'Rules' : 'AI'}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-muted-foreground">
                              Weight: {(dim.weight * 100).toFixed(0)}%
                            </span>
                            <Badge variant="outline">
                              {dim.score.toFixed(0)}
                            </Badge>
                          </div>
                        </div>
                        {/* Score bar */}
                        <div className="mb-2 h-2 overflow-hidden rounded-full bg-secondary">
                          <div
                            className={`h-full rounded-full transition-all ${
                              dim.score >= 70
                                ? 'bg-green-500'
                                : dim.score >= 50
                                  ? 'bg-yellow-500'
                                  : 'bg-red-500'
                            }`}
                            style={{ width: `${dim.score}%` }}
                          />
                        </div>
                        {dim.positive_factors.length > 0 && (
                          <div className="mt-2">
                            {dim.positive_factors.map((f, i) => (
                              <p
                                key={i}
                                className="flex items-start gap-1 text-xs text-green-700"
                              >
                                <CheckCircle2 className="mt-0.5 h-3 w-3 shrink-0" />
                                {f}
                              </p>
                            ))}
                          </div>
                        )}
                        {dim.risk_factors.length > 0 && (
                          <div className="mt-1">
                            {dim.risk_factors.map((f, i) => (
                              <p
                                key={i}
                                className="flex items-start gap-1 text-xs text-red-700"
                              >
                                <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />
                                {f}
                              </p>
                            ))}
                          </div>
                        )}
                        {dim.mitigating_factors.length > 0 && (
                          <div className="mt-1">
                            {dim.mitigating_factors.map((f, i) => (
                              <p
                                key={i}
                                className="flex items-start gap-1 text-xs text-blue-700"
                              >
                                <Shield className="mt-0.5 h-3 w-3 shrink-0" />
                                {f}
                              </p>
                            ))}
                          </div>
                        )}
                        {dim.explanation && (
                          <p className="mt-1 text-xs text-muted-foreground">
                            {dim.explanation}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Processing metadata */}
                {riskAssessment.processing_metadata && (
                  <div className="mt-4 rounded-lg border border-dashed p-3">
                    <p className="mb-1 text-xs font-medium text-muted-foreground">
                      Processing Details
                    </p>
                    <div className="grid grid-cols-2 gap-1 text-xs text-muted-foreground">
                      {riskAssessment.processing_metadata.llm_provider && (
                        <div>
                          Provider: <span className="text-foreground">{String(riskAssessment.processing_metadata.llm_provider)}</span>
                        </div>
                      )}
                      {riskAssessment.processing_metadata.model && (
                        <div>
                          Model: <span className="text-foreground">{String(riskAssessment.processing_metadata.model)}</span>
                        </div>
                      )}
                      {riskAssessment.processing_metadata.total_tokens_used != null && (
                        <div>
                          Tokens: <span className="text-foreground">{String(riskAssessment.processing_metadata.total_tokens_used)}</span>
                        </div>
                      )}
                      {riskAssessment.processing_metadata.duration_seconds != null && (
                        <div>
                          Duration: <span className="text-foreground">{Number(riskAssessment.processing_metadata.duration_seconds).toFixed(1)}s</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ) : null}

          {/* Credit Bureau Report */}
          {creditReport && <CreditReportCard report={creditReport} />}

          {/* Applicant information cards */}
          <div className="grid gap-4 sm:grid-cols-2">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Personal</CardTitle>
              </CardHeader>
              <CardContent className="space-y-1 text-sm">
                <div>{String(personalInfo.first_name ?? '')} {String(personalInfo.last_name ?? '')}</div>
                <div className="text-muted-foreground">{String(personalInfo.email ?? '')}</div>
                <div className="text-muted-foreground">Citizenship: {String(personalInfo.citizenship_status ?? 'N/A')}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Employment</CardTitle>
              </CardHeader>
              <CardContent className="space-y-1 text-sm">
                <div>{String(employmentInfo.employer_name ?? 'N/A')} - {String(employmentInfo.job_title ?? '')}</div>
                <div>Income: ${Number(employmentInfo.annual_income ?? 0).toLocaleString()}/yr</div>
                <div className="text-muted-foreground">{String(employmentInfo.years_at_current_job ?? 0)} years at current job</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Financial</CardTitle>
              </CardHeader>
              <CardContent className="space-y-1 text-sm">
                <div>Credit Score: {String(financialInfo.credit_score_self_reported ?? 'N/A')}</div>
                <div>Assets: ${Number(financialInfo.total_assets ?? 0).toLocaleString()}</div>
                {app.dti_ratio != null && <div>DTI Ratio: {app.dti_ratio.toFixed(1)}%</div>}
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Property</CardTitle>
              </CardHeader>
              <CardContent className="space-y-1 text-sm">
                <div>Price: ${Number(propertyInfo.purchase_price ?? 0).toLocaleString()}</div>
                <div>Down Payment: ${Number(propertyInfo.down_payment ?? 0).toLocaleString()}</div>
                <div className="text-muted-foreground">{String(propertyInfo.property_type ?? 'N/A')} - {String(propertyInfo.property_use ?? 'N/A')}</div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Sidebar: Decision panel */}
        <div className="space-y-6">
          {/* Existing decision */}
          {existingDecision && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Decision Made</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Decision</span>
                  <Badge className="capitalize">
                    {existingDecision.decision.replace(/_/g, ' ')}
                  </Badge>
                </div>
                {existingDecision.interest_rate && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Rate</span>
                    <span>{existingDecision.interest_rate}%</span>
                  </div>
                )}
                {existingDecision.decided_by_name && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">By</span>
                    <span>{existingDecision.decided_by_name}</span>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Decision form */}
          {!existingDecision && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Make Decision</CardTitle>
                <CardDescription>
                  Review the application and render your decision.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {!showDecisionForm ? (
                  <div className="space-y-2">
                    <Button
                      className="w-full"
                      onClick={() => {
                        setDecisionForm((p) => ({ ...p, decision: 'approved' }));
                        setShowDecisionForm(true);
                      }}
                    >
                      <CheckCircle2 className="h-4 w-4" />
                      Approve
                    </Button>
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={() => {
                        setDecisionForm((p) => ({
                          ...p,
                          decision: 'conditionally_approved',
                        }));
                        setShowDecisionForm(true);
                      }}
                    >
                      <AlertTriangle className="h-4 w-4" />
                      Conditional Approve
                    </Button>
                    <Button
                      variant="destructive"
                      className="w-full"
                      onClick={() => {
                        setDecisionForm((p) => ({ ...p, decision: 'denied' }));
                        setShowDecisionForm(true);
                      }}
                    >
                      <XCircle className="h-4 w-4" />
                      Deny
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div>
                      <label className="mb-1 block text-sm font-medium capitalize">
                        Decision: {decisionForm.decision.replace(/_/g, ' ')}
                      </label>
                    </div>

                    {decisionForm.decision !== 'denied' && (
                      <div>
                        <label className="mb-1 block text-xs font-medium">
                          Interest Rate (%)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          className="w-full rounded-md border bg-background px-3 py-1.5 text-sm"
                          placeholder="6.75"
                          value={decisionForm.interest_rate}
                          onChange={(e) =>
                            setDecisionForm((p) => ({
                              ...p,
                              interest_rate: e.target.value,
                            }))
                          }
                        />
                      </div>
                    )}

                    {(decisionForm.decision === 'conditionally_approved' ||
                      decisionForm.decision === 'approved') && (
                      <div>
                        <label className="mb-1 block text-xs font-medium">
                          Conditions (one per line)
                        </label>
                        <textarea
                          className="w-full rounded-md border bg-background px-3 py-1.5 text-sm"
                          rows={3}
                          placeholder="Employment verification within 10 days"
                          value={decisionForm.conditions}
                          onChange={(e) =>
                            setDecisionForm((p) => ({
                              ...p,
                              conditions: e.target.value,
                            }))
                          }
                        />
                      </div>
                    )}

                    {decisionForm.decision === 'denied' && (
                      <div>
                        <label className="mb-1 block text-xs font-medium">
                          Adverse Action Reasons (one per line)
                        </label>
                        <textarea
                          className="w-full rounded-md border bg-background px-3 py-1.5 text-sm"
                          rows={3}
                          placeholder="DTI exceeds program limits"
                          value={decisionForm.adverse_action_reasons}
                          onChange={(e) =>
                            setDecisionForm((p) => ({
                              ...p,
                              adverse_action_reasons: e.target.value,
                            }))
                          }
                        />
                      </div>
                    )}

                    <div>
                      <label className="mb-1 block text-xs font-medium">
                        Notes
                      </label>
                      <textarea
                        className="w-full rounded-md border bg-background px-3 py-1.5 text-sm"
                        rows={2}
                        value={decisionForm.notes}
                        onChange={(e) =>
                          setDecisionForm((p) => ({
                            ...p,
                            notes: e.target.value,
                          }))
                        }
                      />
                    </div>

                    <label className="flex items-center gap-2 text-xs">
                      <input
                        type="checkbox"
                        checked={decisionForm.override_ai_recommendation}
                        onChange={(e) =>
                          setDecisionForm((p) => ({
                            ...p,
                            override_ai_recommendation: e.target.checked,
                          }))
                        }
                      />
                      Override AI recommendation
                    </label>

                    {decisionForm.override_ai_recommendation && (
                      <div>
                        <label className="mb-1 block text-xs font-medium">
                          Override Justification
                        </label>
                        <textarea
                          className="w-full rounded-md border bg-background px-3 py-1.5 text-sm"
                          rows={2}
                          value={decisionForm.override_justification}
                          onChange={(e) =>
                            setDecisionForm((p) => ({
                              ...p,
                              override_justification: e.target.value,
                            }))
                          }
                        />
                      </div>
                    )}

                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowDecisionForm(false)}
                      >
                        Cancel
                      </Button>
                      <Button
                        size="sm"
                        className="flex-1"
                        onClick={handleCreateDecision}
                        disabled={createDecision.isPending}
                      >
                        {createDecision.isPending
                          ? 'Submitting...'
                          : 'Confirm Decision'}
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Documents */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Documents</CardTitle>
              <CardDescription>
                {documents?.total ?? 0} documents
              </CardDescription>
            </CardHeader>
            <CardContent>
              {documents?.items.length ? (
                <div className="space-y-2">
                  {documents.items.map((doc) => (
                    <div
                      key={doc.id}
                      className="flex items-center gap-2 text-sm"
                    >
                      {doc.status === 'processing' ? (
                        <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                      ) : doc.status === 'processed' ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : doc.status === 'error' ? (
                        <AlertCircle className="h-4 w-4 text-destructive" />
                      ) : (
                        <FileText className="h-4 w-4 text-muted-foreground" />
                      )}
                      <div className="min-w-0 flex-1">
                        <span className="block truncate">{doc.filename}</span>
                        <span className="text-xs text-muted-foreground">
                          {DOCUMENT_TYPE_LABELS[doc.document_type] ?? doc.document_type}
                          {doc.extraction_confidence != null && (
                            <span className="ml-1">
                              ({Math.round(doc.extraction_confidence * 100)}%)
                            </span>
                          )}
                        </span>
                      </div>
                      <Badge variant="outline" className="shrink-0 text-xs">
                        {doc.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  No documents uploaded.
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
