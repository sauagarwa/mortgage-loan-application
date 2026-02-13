import { createFileRoute } from '@tanstack/react-router';
import { useState } from 'react';
import { ClipboardList, Search } from 'lucide-react';
import { useAuditLogs } from '../hooks/audit';
import { useAuth } from '../auth/auth-provider';

export const Route = createFileRoute('/audit-log')({
  component: AuditLogPage,
});

const ACTION_COLORS: Record<string, string> = {
  create: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  update: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  delete: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  submit: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
  assign: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
};

function getActionColor(action: string): string {
  for (const [key, color] of Object.entries(ACTION_COLORS)) {
    if (action.includes(key)) return color;
  }
  return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400';
}

function formatTimestamp(ts: string): string {
  return new Date(ts).toLocaleString();
}

function AuditLogPage() {
  const { hasRole } = useAuth();
  const [actionFilter, setActionFilter] = useState('');
  const [resourceTypeFilter, setResourceTypeFilter] = useState('');
  const [emailFilter, setEmailFilter] = useState('');
  const [page, setPage] = useState(0);
  const pageSize = 25;

  const { data, isLoading } = useAuditLogs({
    action: actionFilter || undefined,
    resource_type: resourceTypeFilter || undefined,
    user_email: emailFilter || undefined,
    limit: pageSize,
    offset: page * pageSize,
  });

  if (!hasRole('admin') && !hasRole('loan_servicer')) {
    return (
      <div className="flex items-center justify-center p-12">
        <p className="text-muted-foreground">
          You do not have permission to view audit logs.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-3">
        <ClipboardList className="h-6 w-6 text-primary" />
        <h1 className="text-2xl font-bold">Audit Log</h1>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Filter by email..."
            value={emailFilter}
            onChange={(e) => {
              setEmailFilter(e.target.value);
              setPage(0);
            }}
            className="h-9 rounded-md border bg-background pl-9 pr-3 text-sm outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
        <select
          value={resourceTypeFilter}
          onChange={(e) => {
            setResourceTypeFilter(e.target.value);
            setPage(0);
          }}
          className="h-9 rounded-md border bg-background px-3 text-sm outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="">All resources</option>
          <option value="application">Application</option>
          <option value="document">Document</option>
          <option value="decision">Decision</option>
          <option value="notification">Notification</option>
          <option value="info_request">Info Request</option>
          <option value="risk_assessment">Risk Assessment</option>
        </select>
        <select
          value={actionFilter}
          onChange={(e) => {
            setActionFilter(e.target.value);
            setPage(0);
          }}
          className="h-9 rounded-md border bg-background px-3 text-sm outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="">All actions</option>
          <option value="create_application">Create Application</option>
          <option value="submit_application">Submit Application</option>
          <option value="update_application">Update Application</option>
          <option value="assign_application">Assign Application</option>
          <option value="create_decision">Create Decision</option>
          <option value="create_document">Create Document</option>
          <option value="delete_notification">Delete Notification</option>
          <option value="mark_read">Mark Read</option>
          <option value="mark_all_read">Mark All Read</option>
        </select>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border">
        <table className="w-full text-sm">
          <thead className="border-b bg-muted/50">
            <tr>
              <th className="px-4 py-3 text-left font-medium">Timestamp</th>
              <th className="px-4 py-3 text-left font-medium">User</th>
              <th className="px-4 py-3 text-left font-medium">Action</th>
              <th className="px-4 py-3 text-left font-medium">Resource</th>
              <th className="px-4 py-3 text-left font-medium">Details</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                  Loading...
                </td>
              </tr>
            ) : data?.items.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                  No audit log entries found.
                </td>
              </tr>
            ) : (
              data?.items.map((log) => (
                <tr key={log.id} className="border-b last:border-0 hover:bg-muted/30">
                  <td className="whitespace-nowrap px-4 py-3 text-xs text-muted-foreground">
                    {formatTimestamp(log.timestamp)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-xs">{log.user_email || 'System'}</div>
                    {log.user_role && (
                      <span className="text-[10px] text-muted-foreground">
                        {log.user_role}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${getActionColor(log.action)}`}
                    >
                      {log.action.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-xs font-medium">
                      {log.resource_type.replace(/_/g, ' ')}
                    </div>
                    {log.resource_id && (
                      <span className="font-mono text-[10px] text-muted-foreground">
                        {log.resource_id.slice(0, 8)}...
                      </span>
                    )}
                  </td>
                  <td className="max-w-xs px-4 py-3">
                    {log.details && (
                      <div className="text-xs text-muted-foreground">
                        <span className="font-medium">
                          {(log.details as Record<string, unknown>).method as string}
                        </span>{' '}
                        {(log.details as Record<string, unknown>).path as string}
                        {(log.details as Record<string, unknown>).status_code && (
                          <span className="ml-1 text-green-600">
                            [{(log.details as Record<string, unknown>).status_code as number}]
                          </span>
                        )}
                      </div>
                    )}
                    {log.ip_address && (
                      <div className="text-[10px] text-muted-foreground/50">
                        IP: {log.ip_address}
                      </div>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {data && data.total > pageSize && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            Showing {page * pageSize + 1}-
            {Math.min((page + 1) * pageSize, data.total)} of {data.total}
          </span>
          <div className="flex gap-2">
            <button
              disabled={page === 0}
              onClick={() => setPage((p) => p - 1)}
              className="rounded-md border px-3 py-1.5 text-sm disabled:opacity-50"
            >
              Previous
            </button>
            <button
              disabled={(page + 1) * pageSize >= data.total}
              onClick={() => setPage((p) => p + 1)}
              className="rounded-md border px-3 py-1.5 text-sm disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
