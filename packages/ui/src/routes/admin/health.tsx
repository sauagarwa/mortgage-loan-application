import { createFileRoute } from '@tanstack/react-router';
import { Activity, CheckCircle2, RefreshCw, XCircle } from 'lucide-react';
import { useAuth } from '../../auth/auth-provider';
import { useSystemHealth } from '../../hooks/admin';
import { Button } from '../../components/atoms/button/button';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../../components/atoms/card/card';
import { useQueryClient } from '@tanstack/react-query';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const Route = createFileRoute('/admin/health' as any)({
  component: SystemHealthPage,
});

const STATUS_CONFIG: Record<
  string,
  { icon: React.ReactNode; bg: string; text: string }
> = {
  healthy: {
    icon: <CheckCircle2 className="h-5 w-5 text-green-500" />,
    bg: 'bg-green-50 border-green-200 dark:bg-green-900/10 dark:border-green-800',
    text: 'text-green-700 dark:text-green-400',
  },
  degraded: {
    icon: <Activity className="h-5 w-5 text-yellow-500" />,
    bg: 'bg-yellow-50 border-yellow-200 dark:bg-yellow-900/10 dark:border-yellow-800',
    text: 'text-yellow-700 dark:text-yellow-400',
  },
  unhealthy: {
    icon: <XCircle className="h-5 w-5 text-red-500" />,
    bg: 'bg-red-50 border-red-200 dark:bg-red-900/10 dark:border-red-800',
    text: 'text-red-700 dark:text-red-400',
  },
};

function SystemHealthPage() {
  const { hasRole } = useAuth();
  const { data: health, isLoading, dataUpdatedAt } = useSystemHealth();
  const queryClient = useQueryClient();

  if (!hasRole('admin')) {
    return (
      <div className="flex items-center justify-center p-12">
        <p className="text-muted-foreground">Admin access required.</p>
      </div>
    );
  }

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['admin', 'health'] });
  };

  const overall = STATUS_CONFIG[health?.overall_status ?? 'unhealthy'] ?? STATUS_CONFIG.unhealthy;

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Activity className="h-6 w-6 text-primary" />
          <h1 className="text-2xl font-bold">System Health</h1>
        </div>
        <div className="flex items-center gap-3">
          {dataUpdatedAt > 0 && (
            <span className="text-xs text-muted-foreground">
              Updated: {new Date(dataUpdatedAt).toLocaleTimeString()}
            </span>
          )}
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            <RefreshCw className="mr-1 h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      {isLoading ? (
        <p className="text-muted-foreground">Checking system health...</p>
      ) : !health ? (
        <p className="text-muted-foreground">Unable to fetch health data.</p>
      ) : (
        <>
          {/* Overall Status */}
          <Card className={overall.bg}>
            <CardContent className="flex items-center gap-3 p-4">
              {overall.icon}
              <div>
                <p className={`font-semibold capitalize ${overall.text}`}>
                  System {health.overall_status}
                </p>
                <p className="text-xs text-muted-foreground">
                  {health.components.filter((c) => c.status === 'healthy').length}/
                  {health.components.length} components healthy
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Component Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {health.components.map((c) => {
              const cfg = STATUS_CONFIG[c.status] ?? STATUS_CONFIG.unhealthy;
              return (
                <Card key={c.name} className={cfg.bg}>
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center gap-2 text-base">
                      {cfg.icon}
                      {c.name}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-1 text-sm">
                    <p className={cfg.text}>{c.message}</p>
                    {c.latency_ms != null && (
                      <p className="text-xs text-muted-foreground">
                        Latency: {c.latency_ms}ms
                      </p>
                    )}
                    {c.details &&
                      Object.entries(c.details).map(([key, val]) => (
                        <p key={key} className="text-xs text-muted-foreground">
                          {key.replace(/_/g, ' ')}:{' '}
                          {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                        </p>
                      ))}
                  </CardContent>
                </Card>
              );
            })}
          </div>

          <p className="text-xs text-muted-foreground">
            Auto-refreshes every 30 seconds.
          </p>
        </>
      )}
    </div>
  );
}
