import { createFileRoute, Link } from '@tanstack/react-router';
import { useAuth } from '../auth/auth-provider';
import { useApplications } from '../hooks/applications';
import { Badge } from '../components/atoms/badge/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../components/atoms/card/card';
import { Button } from '../components/atoms/button/button';
import { FileText, Plus } from 'lucide-react';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const Route = createFileRoute('/dashboard' as any)({
  component: Dashboard,
});

const STATUS_LABELS: Record<string, string> = {
  draft: 'Draft',
  submitted: 'Submitted',
  documents_processing: 'Processing Documents',
  risk_assessment_in_progress: 'Risk Assessment',
  under_review: 'Under Review',
  additional_info_requested: 'Info Requested',
  approved: 'Approved',
  conditionally_approved: 'Conditionally Approved',
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

function Dashboard() {
  const { user, isAuthenticated, login } = useAuth();
  const { data: applications, isLoading } = useApplications({ limit: 10 });

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <h2 className="mb-4 text-2xl font-bold">Welcome to MortgageAI</h2>
          <p className="mb-6 text-muted-foreground">
            Sign in to view your dashboard and manage applications.
          </p>
          <Button onClick={login}>Sign In</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl p-4 sm:p-6 lg:p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">
            Welcome back, {user?.firstName}
          </h1>
          <p className="text-muted-foreground">
            Here is an overview of your mortgage applications.
          </p>
        </div>
        <Link to="/applications/new">
          <Button>
            <Plus className="h-4 w-4" />
            New Application
          </Button>
        </Link>
      </div>

      {/* Stats cards */}
      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Applications</CardDescription>
            <CardTitle className="text-3xl">
              {applications?.total ?? 0}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>In Progress</CardDescription>
            <CardTitle className="text-3xl">
              {applications?.items.filter(
                (a) =>
                  !['approved', 'denied', 'withdrawn', 'draft'].includes(
                    a.status,
                  ),
              ).length ?? 0}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Approved</CardDescription>
            <CardTitle className="text-3xl">
              {applications?.items.filter(
                (a) =>
                  a.status === 'approved' ||
                  a.status === 'conditionally_approved',
              ).length ?? 0}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Drafts</CardDescription>
            <CardTitle className="text-3xl">
              {applications?.items.filter((a) => a.status === 'draft').length ??
                0}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Recent applications */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recent Applications</CardTitle>
          <CardDescription>Your most recent mortgage applications</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="py-8 text-center text-muted-foreground">
              Loading applications...
            </div>
          ) : !applications?.items.length ? (
            <div className="py-8 text-center">
              <FileText className="mx-auto mb-3 h-12 w-12 text-muted-foreground/50" />
              <p className="mb-4 text-muted-foreground">
                No applications yet. Start your first mortgage application.
              </p>
              <Link to="/applications/new">
                <Button variant="outline">
                  <Plus className="h-4 w-4" />
                  Start Application
                </Button>
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {applications.items.map((app) => (
                <Link
                  key={app.id}
                  to="/applications/$applicationId"
                  params={{ applicationId: app.id }}
                  className="flex items-center justify-between rounded-lg border p-4 transition-colors hover:bg-accent/50"
                >
                  <div className="flex items-center gap-4">
                    <div>
                      <p className="font-medium">{app.application_number}</p>
                      <p className="text-sm text-muted-foreground">
                        {app.loan_type ?? 'Unknown loan type'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    {app.loan_amount && (
                      <span className="text-sm font-medium">
                        ${app.loan_amount.toLocaleString()}
                      </span>
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
