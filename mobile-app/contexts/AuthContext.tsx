/**
 * AuthContext — Global authentication state for the app.
 * Wraps the entire app to provide user state and auth methods.
 *
 * Usage in screens:
 *   const { user, isLoggedIn, login, logout } = useAuth();
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import * as authService from '../services/auth';
import { getToken, removeToken, setUnauthorizedHandler } from '../services/api';

// --- Types ---
interface AuthContextType {
  user: authService.User | null;
  isLoggedIn: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => Promise<void>;
  logoutAll: () => Promise<authService.LogoutAllResponse>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isLoggedIn: false,
  isLoading: true,
  login: async () => {},
  register: async () => {},
  logout: async () => {},
  logoutAll: async () => ({ detail: '', revoked_sessions: 0 }),
});

// --- Provider ---
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<authService.User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing token on mount
  useEffect(() => {
    (async () => {
      try {
        const token = await getToken();
        if (token) {
          const profile = await authService.getProfile();
          setUser(profile);
        }
      } catch {
        // Token expired/invalid -> clear stale token and reset session state.
        await removeToken();
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setUser(null);
    });
    return () => setUnauthorizedHandler(null);
  }, []);

  const login = async (email: string, password: string) => {
    const profile = await authService.login(email, password);
    setUser(profile);
  };

  const register = async (email: string, password: string, fullName?: string) => {
    const profile = await authService.register(email, password, fullName);
    setUser(profile);
  };

  const logout = async () => {
    await authService.logout();
    setUser(null);
  };

  const logoutAll = async (): Promise<authService.LogoutAllResponse> => {
    const result = await authService.logoutAll();
    setUser(null);
    return result;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoggedIn: !!user,
        isLoading,
        login,
        register,
        logout,
        logoutAll,
      }}>
      {children}
    </AuthContext.Provider>
  );
}

// --- Hook ---
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
