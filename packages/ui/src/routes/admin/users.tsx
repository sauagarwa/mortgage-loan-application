import { createFileRoute } from '@tanstack/react-router';
import { useState } from 'react';
import { Search, Users } from 'lucide-react';
import { useAuth } from '../../auth/auth-provider';
import { useAdminUsers, useUpdateUser } from '../../hooks/admin';
import { Badge } from '../../components/atoms/badge/badge';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const Route = createFileRoute('/admin/users' as any)({
  component: UserManagementPage,
});

const ROLE_VARIANTS: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  admin: 'destructive',
  loan_servicer: 'default',
  applicant: 'secondary',
};

function UserManagementPage() {
  const { hasRole } = useAuth();
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [page, setPage] = useState(0);
  const pageSize = 25;
  const updateUser = useUpdateUser();

  const { data, isLoading } = useAdminUsers({
    search: search || undefined,
    role: roleFilter || undefined,
    limit: pageSize,
    offset: page * pageSize,
  });

  if (!hasRole('admin')) {
    return (
      <div className="flex items-center justify-center p-12">
        <p className="text-muted-foreground">Admin access required.</p>
      </div>
    );
  }

  const handleRoleChange = (userId: string, newRole: string) => {
    updateUser.mutate({ userId, data: { role: newRole } });
  };

  const handleToggleActive = (userId: string, currentActive: boolean) => {
    updateUser.mutate({ userId, data: { is_active: !currentActive } });
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-3">
        <Users className="h-6 w-6 text-primary" />
        <h1 className="text-2xl font-bold">User Management</h1>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by name or email..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(0);
            }}
            className="h-9 w-64 rounded-md border bg-background pl-9 pr-3 text-sm outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
        <select
          value={roleFilter}
          onChange={(e) => {
            setRoleFilter(e.target.value);
            setPage(0);
          }}
          className="h-9 rounded-md border bg-background px-3 text-sm outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="">All roles</option>
          <option value="admin">Admin</option>
          <option value="loan_servicer">Loan Servicer</option>
          <option value="applicant">Applicant</option>
        </select>
      </div>

      {/* User Table */}
      <div className="overflow-x-auto rounded-lg border">
        <table className="w-full text-sm">
          <thead className="border-b bg-muted/50">
            <tr>
              <th className="px-4 py-3 text-left font-medium">User</th>
              <th className="px-4 py-3 text-left font-medium">Role</th>
              <th className="px-4 py-3 text-left font-medium">Status</th>
              <th className="px-4 py-3 text-left font-medium">Applications</th>
              <th className="px-4 py-3 text-left font-medium">Last Login</th>
              <th className="px-4 py-3 text-left font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                  Loading...
                </td>
              </tr>
            ) : data?.items.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                  No users found.
                </td>
              </tr>
            ) : (
              data?.items.map((u) => (
                <tr key={u.id} className="border-b last:border-0 hover:bg-muted/30">
                  <td className="px-4 py-3">
                    <div className="font-medium">
                      {u.first_name} {u.last_name}
                    </div>
                    <div className="text-xs text-muted-foreground">{u.email}</div>
                  </td>
                  <td className="px-4 py-3">
                    <select
                      value={u.role}
                      onChange={(e) => handleRoleChange(u.id, e.target.value)}
                      className="rounded-md border bg-background px-2 py-1 text-xs"
                    >
                      <option value="applicant">Applicant</option>
                      <option value="loan_servicer">Loan Servicer</option>
                      <option value="admin">Admin</option>
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={u.is_active ? 'default' : 'destructive'}>
                      {u.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-center">{u.application_count}</td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {u.last_login_at
                      ? new Date(u.last_login_at).toLocaleDateString()
                      : 'Never'}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleToggleActive(u.id, u.is_active)}
                      className={`rounded-md px-2 py-1 text-xs ${
                        u.is_active
                          ? 'text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20'
                          : 'text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20'
                      }`}
                    >
                      {u.is_active ? 'Deactivate' : 'Activate'}
                    </button>
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
