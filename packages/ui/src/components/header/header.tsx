import { Link } from '@tanstack/react-router';
import { Logo } from '../logo/logo';
import { ModeToggle } from '../mode-toggle/mode-toggle';
import { NotificationBell } from '../notification-bell/notification-bell';
import { useAuth } from '../../auth/auth-provider';
import { LogIn, LogOut, User } from 'lucide-react';

export function Header() {
  const { isAuthenticated, isLoading, user, login, logout } = useAuth();

  return (
    <header className="sticky top-0 z-20 border-b bg-background/80 backdrop-blur">
      <div className="container mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-2">
          <Logo />
          <span className="font-bold">Mortgage AI</span>
        </Link>
        <div className="flex items-center gap-4">
          <ModeToggle />
          {isAuthenticated && <NotificationBell />}
          {!isLoading && (
            <>
              {isAuthenticated && user ? (
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2 text-sm">
                    <User className="h-4 w-4" />
                    <span>{user.firstName} {user.lastName}</span>
                    <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">
                      {user.roles[0]}
                    </span>
                  </div>
                  <button
                    onClick={logout}
                    className="flex items-center gap-1 rounded-md px-3 py-1.5 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  >
                    <LogOut className="h-4 w-4" />
                    Sign Out
                  </button>
                </div>
              ) : (
                <button
                  onClick={login}
                  className="flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-sm text-primary-foreground hover:opacity-90"
                >
                  <LogIn className="h-4 w-4" />
                  Sign In
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </header>
  );
}
