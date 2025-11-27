import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, AuthState } from '../types/auth';
import { fetchWithFallback, getBackendUrl, isDevMode } from '../utils/api';

interface AuthContextType extends AuthState {
  login: () => void;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const BACKEND_URL = getBackendUrl();
const DEV_MODE = isDevMode();

// Mock user for dev mode fallback
const mockUser: User = {
  id: 'dev-user',
  email: 'dev@example.com',
  name: 'Dev User',
  role: 'developer'
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const checkAuth = async () => {
    try {
      setIsLoading(true);

      // Try backend first, fall back to mock user in dev mode if unreachable
      const userData = await fetchWithFallback<User>(
        '/api/me',
        {
          credentials: 'include',
        },
        mockUser
      );

      setUser(userData);
    } catch (error) {
      console.error('Auth check failed:', error);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = () => {
    window.location.href = `${BACKEND_URL}/api/saml/login`;
  };

  const logout = async () => {
    try {
      await fetch(`${BACKEND_URL}/api/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setUser(null);
      window.location.href = '/';
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};