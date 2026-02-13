import { createFileRoute, Link } from '@tanstack/react-router';
import { useState } from 'react';
import { useApplications } from '../../hooks/applications';
import { Badge } from '../../components/atoms/badge/badge';
import { Button } from '../../components/atoms/button/button';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../../components/atoms/card/card';
import { FileText, Plus } from 'lucide-react';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const Route = createFileRoute('/applications/' as any)({
  component: ApplicationsPage,
});

const STATUS_LABELS: Record<string, string> = {
  draft: 'Draft',
  submitted: 'Submitted',
  documents_processing: 'Processing',
  risk_assessment_in_progress: 'Assessing',
  under_review: 'Under Review',
  additional_info_requested: 'Info Requested',
  approved: 'Approved',
  conditionally_approved: 'Cond. Approved',
  denied: 'Denied',
  withdrawn: 'Withdrawn',
};

const STATUS_VARIANTS: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  draft: 'outline',
  submitted: 'secondary',
  documents_processing: 'secondary',
  risk_assessment_in_progress: 'secondary',
  under_review: 'default',
  additional_info_requested: 'outline',
  approved: 'default',
  conditionally_approved: 'default',
  denied: 'destructive',
  withdrawn: 'outline',
};

const STATUS_FILTERS = [
  { value: '', label: 'All' },
  { value: 'draft', label: 'Draft' },
  { value: 'submitted', label: 'Submitted' },
  { value: 'under_review', label: 'Under Review' },
  { value: 'approved', label: 'Approved' },
  { value: 'denied', label: 'Denied' },
];

function ApplicationsPage() {
  const [statusFilter, setStatusFilter] = useState('');
  const { data, isLoading } = useApplications(
    statusFilter ? { status: statusFilter } : undefined,
  );

  return (
    <div className="mx-auto max-w-7xl p-4 sm:p-6 lg:p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">My Applications</h1>
          <p className="text-muted-foreground">
            View and manage your mortgage applications.
          </p>
        </div>
        <Link to="/applications/new">
          <Button>
            <Plus className="h-4 w-4" />
            New Application
          </Button>
        </Link>
      </div>

      {/* Status filter */}
      <div className="mb-4 flex flex-wrap gap-2">
        {STATUS_FILTERS.map((filter) => (
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

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            Applications ({data?.total ?? 0})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="py-8 text-center text-muted-foreground">
              Loading...
            </div>
          ) : !data?.items.length ? (
            <div className="py-8 text-center">
              <FileText className="mx-auto mb-3 h-12 w-12 text-muted-foreground/50" />
              <p className="mb-4 text-muted-foreground">
                No applications found.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {data.items.map((app) => (
                <Link
                  key={app.id}
                  to="/applications/$applicationId"
                  params={{ applicationId: app.id }}
                  className="flex items-center justify-between rounded-lg border p-4 transition-colors hover:bg-accent/50"
                >
                  <div>
                    <p className="font-medium">{app.application_number}</p>
                    <p className="text-sm text-muted-foreground">
                      {app.loan_type ?? 'Unknown'} &middot;{' '}
                      {app.created_at
                        ? new Date(app.created_at).toLocaleDateString()
                        : ''}
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    {app.loan_amount != null && (
                      <span className="text-sm font-medium">
                        ${app.loan_amount.toLocaleString()}
                      </span>
                    )}
                    {app.risk_band && (
                      <Badge variant="outline" className="capitalize">
                        {app.risk_band} risk
                      </Badge>
                    )}
                    <Badge variant={STATUS_VARIANTS[app.status] ?? 'outline'}>
                      {STATUS_LABELS[app.status] ?? app.status}
                    </Badge>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
