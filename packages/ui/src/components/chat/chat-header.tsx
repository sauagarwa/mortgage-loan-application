import { Link } from '@tanstack/react-router';
import { LogIn, LogOut, MessageSquarePlus, User } from 'lucide-react';
import { Logo } from '../logo/logo';
import { ModeToggle } from '../mode-toggle/mode-toggle';
import { useAuth } from '../../auth/auth-provider';
import { Button } from '../atoms/button/button';

interface ChatHeaderProps {
  onNewChat?: () => void;
}

export function ChatHeader({ onNewChat }: ChatHeaderProps) {
  const { isAuthenticated, isLoading, user, login, logout } = useAuth();

  return (
    <header className="sticky top-0 z-20 border-b bg-background/80 backdrop-blur">
      <div className="flex h-14 items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <Link to="/" className="flex items-center gap-2">
            <Logo />
            <span className="font-bold">MortgageAI</span>
          </Link>
          {onNewChat && (
            <Button variant="ghost" size="sm" onClick={onNewChat} className="gap-1.5">
              <MessageSquarePlus className="h-4 w-4" />
              <span className="hidden sm:inline">New Chat</span>
            </Button>
          )}
        </div>
        <div className="flex items-center gap-3">
          <ModeToggle />
          {!isLoading && (
            <>
              {isAuthenticated && user ? (
                <div className="flex items-center gap-2">
                  <div className="hidden items-center gap-1.5 text-sm sm:flex">
                    <User className="h-4 w-4" />
                    <span>{user.firstName}</span>
                  </div>
                  <Button variant="ghost" size="sm" onClick={logout} className="gap-1.5">
                    <LogOut className="h-4 w-4" />
                    <span className="hidden sm:inline">Sign Out</span>
                  </Button>
                </div>
              ) : (
                <Button variant="default" size="sm" onClick={login} className="gap-1.5">
                  <LogIn className="h-4 w-4" />
                  Sign In
                </Button>
              )}
            </>
          )}
        </div>
      </div>
    </header>
  );
}
