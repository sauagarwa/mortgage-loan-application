import { createFileRoute } from '@tanstack/react-router';
import { useAuth } from '../../auth/auth-provider';
import { useAnalytics } from '../../hooks/admin';
import {
  BarChart3,
  CheckCircle2,
  Clock,
  GitCompare,
  TrendingUp,
  XCircle,
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../../components/atoms/card/card';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const Route = createFileRoute('/servicer/analytics' as any)({
  component: AnalyticsPage,
});

const STATUS_LABELS: Record<string, string> = {
  submitted: 'Submitted',
  documents_processing: 'Processing Docs',
  risk_assessment_in_progress: 'Risk Assessment',
  under_review: 'Under Review',
  additional_info_requested: 'Info Requested',
  approved: 'Approved',
  conditionally_approved: 'Conditionally Approved',
  denied: 'Denied',
  withdrawn: 'Withdrawn',
};

const STATUS_COLORS: Record<string, string> = {
  submitted: 'bg-blue-500',
  documents_processing: 'bg-blue-400',
  risk_assessment_in_progress: 'bg-indigo-400',
  under_review: 'bg-yellow-500',
  additional_info_requested: 'bg-orange-400',
  approved: 'bg-green-500',
  conditionally_approved: 'bg-green-400',
  denied: 'bg-red-500',
  withdrawn: 'bg-gray-400',
};

const BAND_COLORS: Record<string, string> = {
  low: 'bg-green-500',
  medium: 'bg-yellow-500',
  high: 'bg-orange-500',
  very_high: 'bg-red-500',
};

function AnalyticsPage() {
  const { hasRole } = useAuth();
  const { data, isLoading } = useAnalytics();

  if (!hasRole('admin') && !hasRole('loan_servicer')) {
    return (
      <div className="flex items-center justify-center p-12">
        <p className="text-muted-foreground">Insufficient permissions.</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-6">
        <p className="text-muted-foreground">Loading analytics...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-6">
        <p className="text-muted-foreground">Unable to load analytics.</p>
      </div>
    );
  }

  const maxVolume = Math.max(...(data.volume_by_status.map((v) => v.count) || [1]), 1);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-3">
        <BarChart3 className="h-6 w-6 text-primary" />
        <h1 className="text-2xl font-bold">Analytics Dashboard</h1>
      </div>

      {/* Top-Level Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="flex items-center gap-3 p-4">
            <TrendingUp className="h-8 w-8 text-primary" />
            <div>
              <p className="text-2xl font-bold">{data.total_applications}</p>
              <p className="text-xs text-muted-foreground">Total Applications</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 p-4">
            <CheckCircle2 className="h-8 w-8 text-green-500" />
            <div>
              <p className="text-2xl font-bold">{data.total_decisions}</p>
              <p className="text-xs text-muted-foreground">Total Decisions</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 p-4">
            <TrendingUp className="h-8 w-8 text-blue-500" />
            <div>
              <p className="text-2xl font-bold">
                {data.approval_rate_overall != null
                  ? `${(data.approval_rate_overall * 100).toFixed(1)}%`
                  : 'N/A'}
              </p>
              <p className="text-xs text-muted-foreground">Approval Rate</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 p-4">
            <Clock className="h-8 w-8 text-yellow-500" />
            <div>
              <p className="text-2xl font-bold">
                {data.processing_time.average_hours != null
                  ? `${data.processing_time.average_hours}h`
                  : 'N/A'}
              </p>
              <p className="text-xs text-muted-foreground">Avg Processing Time</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Volume by Status */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Application Volume by Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.volume_by_status.map((v) => (
                <div key={v.status} className="flex items-center gap-3">
                  <span className="w-32 text-xs text-muted-foreground truncate">
                    {STATUS_LABELS[v.status] || v.status}
                  </span>
                  <div className="flex-1">
                    <div
                      className={`h-5 rounded ${STATUS_COLORS[v.status] || 'bg-gray-400'}`}
                      style={{
                        width: `${Math.max((v.count / maxVolume) * 100, 4)}%`,
                      }}
                    />
                  </div>
                  <span className="w-8 text-right text-sm font-medium">
                    {v.count}
                  </span>
                </div>
              ))}
              {data.volume_by_status.length === 0 && (
                <p className="text-sm text-muted-foreground">No data yet.</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Approval Rate by Risk Band */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Approval Rate by Risk Band</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data.approval_rate_by_band.map((b) => (
                <div key={b.risk_band} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="capitalize font-medium">
                      {b.risk_band.replace(/_/g, ' ')}
                    </span>
                    <span>
                      {b.rate != null ? `${(b.rate * 100).toFixed(0)}%` : 'N/A'}
                      <span className="ml-1 text-xs text-muted-foreground">
                        ({b.approved}/{b.total})
                      </span>
                    </span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-muted">
                    <div
                      className={`h-2 rounded-full ${BAND_COLORS[b.risk_band] || 'bg-gray-400'}`}
                      style={{ width: `${(b.rate ?? 0) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
              {data.approval_rate_by_band.length === 0 && (
                <p className="text-sm text-muted-foreground">No data yet.</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Processing Time */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Processing Time</CardTitle>
            <CardDescription>Time from submission to decision</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-lg font-bold">
                  {data.processing_time.min_hours != null
                    ? `${data.processing_time.min_hours}h`
                    : '--'}
                </p>
                <p className="text-xs text-muted-foreground">Minimum</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-bold text-primary">
                  {data.processing_time.average_hours != null
                    ? `${data.processing_time.average_hours}h`
                    : '--'}
                </p>
                <p className="text-xs text-muted-foreground">Average</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-bold">
                  {data.processing_time.max_hours != null
                    ? `${data.processing_time.max_hours}h`
                    : '--'}
                </p>
                <p className="text-xs text-muted-foreground">Maximum</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Override Tracking */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <GitCompare className="h-4 w-4" />
              AI Override Tracking
            </CardTitle>
            <CardDescription>
              Decisions where servicers overrode AI recommendations
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Override Rate</span>
              <span className="text-lg font-bold">
                {data.override_stats.override_rate != null
                  ? `${(data.override_stats.override_rate * 100).toFixed(1)}%`
                  : 'N/A'}
              </span>
            </div>
            <div className="text-sm text-muted-foreground">
              {data.override_stats.total_overrides} overrides out of{' '}
              {data.override_stats.total_decisions} decisions
            </div>

            {data.override_stats.total_overrides > 0 && (
              <div className="space-y-2 border-t pt-3">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <XCircle className="h-3 w-3 text-red-500" />
                    AI approved, servicer denied
                  </div>
                  <span className="font-medium">
                    {data.override_stats.ai_approve_servicer_deny}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-3 w-3 text-green-500" />
                    AI denied, servicer approved
                  </div>
                  <span className="font-medium">
                    {data.override_stats.ai_deny_servicer_approve}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <GitCompare className="h-3 w-3 text-yellow-500" />
                    Other overrides
                  </div>
                  <span className="font-medium">
                    {data.override_stats.ai_conditional_servicer_different}
                  </span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
