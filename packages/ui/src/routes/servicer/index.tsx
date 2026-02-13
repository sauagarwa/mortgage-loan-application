import { createFileRoute, Link } from '@tanstack/react-router';
import { useState } from 'react';
import { useAuth } from '../../auth/auth-provider';
import { useDashboardStats } from '../../hooks/decisions';
import { useApplications } from '../../hooks/applications';
import { Badge } from '../../components/atoms/badge/badge';
import { Button } from '../../components/atoms/button/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../../components/atoms/card/card';
import { ClipboardCheck, Clock, CheckCircle2, TrendingUp } from 'lucide-react';
import { useServicerWebSocket } from '../../hooks/useWebSocket';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const Route = createFileRoute('/servicer/' as any)({
  component: ServicerDashboard,
});

const STATUS_LABELS: Record<string, string> = {
  submitted: 'Submitted',
  documents_processing: 'Processing',
  risk_assessment_in_progress: 'Assessing',
  under_review: 'Under Review',
  additional_info_requested: 'Info Requested',
  approved: 'Approved',
  conditionally_approved: 'Cond. Approved',
  denied: 'Denied',
};

const STATUS_VARIANTS: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  submitted: 'secondary',
  documents_processing: 'secondary',
  risk_assessment_in_progress: 'secondary',
  under_review: 'default',
  additional_info_requested: 'outline',
  approved: 'default',
  conditionally_approved: 'default',
  denied: 'destructive',
};

const RISK_COLORS: Record<string, string> = {
  low: 'text-green-600',
  medium: 'text-yellow-600',
  high: 'text-orange-600',
  very_high: 'text-red-600',
};

function ServicerDashboard() {
  const { user } = useAuth();
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const [statusFilter, setStatusFilter] = useState('');
  useServicerWebSocket();
  const { data: applications } = useApplications(
    statusFilter
      ? { status: statusFilter, sort_by: 'submitted_at', sort_order: 'desc' }
      : { sort_by: 'submitted_at', sort_order: 'desc' },
  );

  if (!user?.roles.some((r) => r === 'loan_servicer' || r === 'admin')) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <h2 className="mb-2 text-2xl font-bold">Access Denied</h2>
          <p className="text-muted-foreground">
            This page is only available to loan servicers and administrators.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl p-4 sm:p-6 lg:p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Servicer Dashboard</h1>
        <p className="text-muted-foreground">
          Overview of loan applications and review queue.
        </p>
      </div>

      {/* Stats cards */}
      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardDescription>Pending Review</CardDescription>
            <ClipboardCheck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {statsLoading ? '...' : stats?.pending_review ?? 0}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardDescription>In Progress</CardDescription>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {statsLoading ? '...' : stats?.in_progress ?? 0}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardDescription>Decided Today</CardDescription>
            <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {statsLoading ? '...' : stats?.decided_today ?? 0}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardDescription>Approval Rate (30d)</CardDescription>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {statsLoading
                ? '...'
                : stats?.approval_rate != null
                  ? `${(stats.approval_rate * 100).toFixed(0)}%`
                  : 'N/A'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Risk Distribution */}
      {stats?.risk_distribution && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="text-base">Risk Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-6">
              {Object.entries(stats.risk_distribution).map(([band, count]) => (
                <div key={band} className="text-center">
                  <p className={`text-2xl font-bold ${RISK_COLORS[band] ?? ''}`}>
                    {count}
                  </p>
                  <p className="text-xs capitalize text-muted-foreground">
                    {band.replace('_', ' ')}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Application Queue */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Application Queue</CardTitle>
              <CardDescription>
                {applications?.total ?? 0} total applications
              </CardDescription>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 pt-2">
            {[
              { value: '', label: 'All' },
              { value: 'submitted', label: 'Submitted' },
              { value: 'under_review', label: 'Under Review' },
              { value: 'additional_info_requested', label: 'Info Requested' },
            ].map((filter) => (
              <Button
                key={filter.value}
                variant={statusFilter === filter.value ? 'default' : 'outline'}
                size="sm"
                onClick={() => setStatusFilter(filter.value)}
              >
                {filter.label}
              </Button>
            ))}
          </div>
        </CardHeader>
        <CardContent>
          {!applications?.items.length ? (
            <p className="py-8 text-center text-muted-foreground">
              No applications in the queue.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-2 pr-4 font-medium">Application</th>
                    <th className="pb-2 pr-4 font-medium">Applicant</th>
                    <th className="pb-2 pr-4 font-medium">Loan Type</th>
                    <th className="pb-2 pr-4 font-medium">Amount</th>
                    <th className="pb-2 pr-4 font-medium">Risk</th>
                    <th className="pb-2 pr-4 font-medium">Status</th>
                    <th className="pb-2 font-medium">Submitted</th>
                  </tr>
                </thead>
                <tbody>
                  {applications.items.map((app) => (
                    <tr key={app.id} className="border-b last:border-0">
                      <td className="py-3 pr-4">
                        <Link
                          to="/servicer/review/$applicationId"
                          params={{ applicationId: app.id }}
                          className="font-medium text-primary hover:underline"
                        >
                          {app.application_number}
                        </Link>
                      </td>
                      <td className="py-3 pr-4">
                        {app.applicant_name ?? 'Unknown'}
                      </td>
                      <td className="py-3 pr-4 text-muted-foreground">
                        {app.loan_type ?? 'N/A'}
                      </td>
                      <td className="py-3 pr-4">
                        {app.loan_amount != null
                          ? `$${app.loan_amount.toLocaleString()}`
                          : 'N/A'}
                      </td>
                      <td className="py-3 pr-4">
                        {app.risk_band ? (
                          <span
                            className={`font-medium capitalize ${RISK_COLORS[app.risk_band] ?? ''}`}
                          >
                            {app.risk_band.replace('_', ' ')}
                            {app.risk_score != null && ` (${app.risk_score})`}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">N/A</span>
                        )}
                      </td>
                      <td className="py-3 pr-4">
                        <Badge
                          variant={STATUS_VARIANTS[app.status] ?? 'outline'}
                        >
                          {STATUS_LABELS[app.status] ?? app.status}
                        </Badge>
                      </td>
                      <td className="py-3 text-muted-foreground">
                        {app.submitted_at
                          ? new Date(app.submitted_at).toLocaleDateString()
                          : 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
