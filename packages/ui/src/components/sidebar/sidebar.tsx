import { Link, useRouterState } from '@tanstack/react-router';
import { useAuth } from '../../auth/auth-provider';
import {
  BarChart3,
  ClipboardList,
  FileText,
  Home,
  LayoutDashboard,
  MessageSquare,
  ScrollText,
  Settings,
  Users,
} from 'lucide-react';
import { cn } from '../../lib/utils';

interface NavItem {
  label: string;
  to: string;
  icon: React.ReactNode;
  roles?: string[];
}

const navItems: NavItem[] = [
  { label: 'Home', to: '/', icon: <Home className="h-4 w-4" /> },
  {
    label: 'New Application',
    to: '/chat',
    icon: <MessageSquare className="h-4 w-4" />,
  },
  {
    label: 'Dashboard',
    to: '/dashboard',
    icon: <LayoutDashboard className="h-4 w-4" />,
  },
  {
    label: 'Loan Products',
    to: '/loans',
    icon: <ScrollText className="h-4 w-4" />,
  },
  {
    label: 'My Applications',
    to: '/applications',
    icon: <FileText className="h-4 w-4" />,
    roles: ['applicant'],
  },
  {
    label: 'Review Queue',
    to: '/servicer',
    icon: <Users className="h-4 w-4" />,
    roles: ['loan_servicer', 'admin'],
  },
  {
    label: 'Analytics',
    to: '/servicer/analytics',
    icon: <BarChart3 className="h-4 w-4" />,
    roles: ['loan_servicer', 'admin'],
  },
  {
    label: 'Audit Log',
    to: '/audit-log',
    icon: <ClipboardList className="h-4 w-4" />,
    roles: ['loan_servicer', 'admin'],
  },
  {
    label: 'Admin',
    to: '/admin',
    icon: <Settings className="h-4 w-4" />,
    roles: ['admin'],
  },
];

export function Sidebar() {
  const { user, isAuthenticated } = useAuth();
  const routerState = useRouterState();
  const currentPath = routerState.location.pathname;

  if (!isAuthenticated) return null;

  const visibleItems = navItems.filter((item) => {
    if (!item.roles) return true;
    return item.roles.some((role) => user?.roles.includes(role));
  });

  return (
    <aside className="hidden w-56 shrink-0 border-r bg-background md:block">
      <nav className="flex flex-col gap-1 p-3">
        {visibleItems.map((item) => {
          const isActive =
            item.to === '/'
              ? currentPath === '/'
              : currentPath.startsWith(item.to);

          return (
            <Link
              key={item.to}
              to={item.to}
              className={cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-accent text-accent-foreground'
                  : 'text-muted-foreground hover:bg-accent/50 hover:text-accent-foreground',
              )}
            >
              {item.icon}
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
