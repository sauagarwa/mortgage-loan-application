import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import keycloak from './keycloak';

interface AuthUser {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  roles: string[];
}

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: AuthUser | null;
  token: string | null;
  login: () => void;
  logout: () => void;
  hasRole: (role: string) => boolean;
}

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  isLoading: true,
  user: null,
  token: null,
  login: () => {},
  logout: () => {},
  hasRole: () => false,
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);

  const initCalled = useRef(false);

  useEffect(() => {
    if (initCalled.current) return;
    initCalled.current = true;

    keycloak
      .init({
        checkLoginIframe: false,
      })
      .then((authenticated) => {
        setIsAuthenticated(authenticated);
        if (authenticated && keycloak.tokenParsed) {
          setToken(keycloak.token || null);
          const realmRoles =
            keycloak.tokenParsed.realm_access?.roles || [];
          const customRoles =
            (keycloak.tokenParsed as Record<string, unknown>)
              .realm_roles as string[] | undefined;
          const allRoles = [
            ...new Set([...realmRoles, ...(customRoles || [])]),
          ];
          const appRoles = allRoles.filter((r) =>
            ['applicant', 'loan_servicer', 'admin'].includes(r),
          );

          setUser({
            id: keycloak.tokenParsed.sub || '',
            email: keycloak.tokenParsed.email || '',
            firstName: keycloak.tokenParsed.given_name || '',
            lastName: keycloak.tokenParsed.family_name || '',
            roles: appRoles.length > 0 ? appRoles : ['applicant'],
          });
        }
        setIsLoading(false);
      })
      .catch((error) => {
        console.error('Keycloak init failed:', error);
        setIsLoading(false);
      });

    // Token refresh
    keycloak.onTokenExpired = () => {
      keycloak
        .updateToken(30)
        .then((refreshed) => {
          if (refreshed) {
            setToken(keycloak.token || null);
          }
        })
        .catch(() => {
          setIsAuthenticated(false);
          setUser(null);
          setToken(null);
        });
    };
  }, []);

  const login = useCallback(() => {
    keycloak.login();
  }, []);

  const logout = useCallback(() => {
    keycloak.logout({ redirectUri: window.location.origin });
  }, []);

  const hasRole = useCallback(
    (role: string) => {
      return user?.roles.includes(role) || false;
    },
    [user],
  );

  const value = useMemo(
    () => ({
      isAuthenticated,
      isLoading,
      user,
      token,
      login,
      logout,
      hasRole,
    }),
    [isAuthenticated, isLoading, user, token, login, logout, hasRole],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
