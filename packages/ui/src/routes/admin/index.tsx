import { createFileRoute, Link } from '@tanstack/react-router';
import { useAuth } from '../../auth/auth-provider';
import { useSystemHealth } from '../../hooks/admin';
import {
  Activity,
  Bot,
  CheckCircle2,
  Settings,
  Shield,
  Users,
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
export const Route = createFileRoute('/admin/' as any)({
  component: AdminDashboard,
});

const STATUS_ICON: Record<string, React.ReactNode> = {
  healthy: <CheckCircle2 className="h-5 w-5 text-green-500" />,
  degraded: <Activity className="h-5 w-5 text-yellow-500" />,
  unhealthy: <XCircle className="h-5 w-5 text-red-500" />,
};

function AdminDashboard() {
  const { hasRole } = useAuth();
  const { data: health, isLoading } = useSystemHealth();

  if (!hasRole('admin')) {
    return (
      <div className="flex items-center justify-center p-12">
        <p className="text-muted-foreground">Admin access required.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-3">
        <Settings className="h-6 w-6 text-primary" />
        <h1 className="text-2xl font-bold">Admin Dashboard</h1>
      </div>

      {/* Quick Links */}
      <div className="grid gap-4 md:grid-cols-3">
        <Link to="/admin/llm-config">
          <Card className="cursor-pointer transition-shadow hover:shadow-md">
            <CardHeader className="flex flex-row items-center gap-3 pb-2">
              <Bot className="h-5 w-5 text-primary" />
              <CardTitle className="text-lg">LLM Providers</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Configure AI model providers, API keys, and settings
              </CardDescription>
            </CardContent>
          </Card>
        </Link>

        <Link to="/admin/users">
          <Card className="cursor-pointer transition-shadow hover:shadow-md">
            <CardHeader className="flex flex-row items-center gap-3 pb-2">
              <Users className="h-5 w-5 text-primary" />
              <CardTitle className="text-lg">User Management</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                View users, manage roles, activate/deactivate accounts
              </CardDescription>
            </CardContent>
          </Card>
        </Link>

        <Link to="/admin/health">
          <Card className="cursor-pointer transition-shadow hover:shadow-md">
            <CardHeader className="flex flex-row items-center gap-3 pb-2">
              <Shield className="h-5 w-5 text-primary" />
              <CardTitle className="text-lg">System Health</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Monitor all system components and services
              </CardDescription>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* System Status Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            System Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-muted-foreground">Checking system health...</p>
          ) : health ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm">
                {STATUS_ICON[health.overall_status] || STATUS_ICON.unhealthy}
                <span className="font-medium capitalize">
                  Overall: {health.overall_status}
                </span>
              </div>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {health.components.map((c) => (
                  <div
                    key={c.name}
                    className="flex items-center gap-2 rounded-md border p-2 text-sm"
                  >
                    {STATUS_ICON[c.status] || STATUS_ICON.unhealthy}
                    <div>
                      <span className="font-medium">{c.name}</span>
                      {c.latency_ms != null && (
                        <span className="ml-1 text-xs text-muted-foreground">
                          ({c.latency_ms}ms)
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-muted-foreground">Unable to fetch health data.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
