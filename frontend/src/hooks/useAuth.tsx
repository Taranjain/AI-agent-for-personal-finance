import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, authApi } from '../lib/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  login: (data: { email: string; password: string }) => Promise<void>;
  register: (data: { email: string; password: string; full_name: string }) => Promise<void>;
  logout: () => void;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    try {
      const savedUser = localStorage.getItem('finwise_user');
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('finwise_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize auth state on mount
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem('finwise_token');
      if (storedToken) {
        try {
          const res = await authApi.getCurrentUser();
          setUser(res.user);
          localStorage.setItem('finwise_user', JSON.stringify(res.user));
        } catch (err: any) {
          console.warn('Failed to restore session from token:', err);
          // Only clear if 401 unauthorized
          if (err?.response?.status === 401) {
            localStorage.removeItem('finwise_token');
            localStorage.removeItem('finwise_user');
            setToken(null);
            setUser(null);
          }
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (credentials: { email: string; password: string }) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await authApi.login(credentials);
      localStorage.setItem('finwise_token', response.access_token);
      localStorage.setItem('finwise_user', JSON.stringify(response.user));
      setToken(response.access_token);
      setUser(response.user);
    } catch (err: any) {
      const message =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        'Login failed. Please check your credentials and try again.';
      setError(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: { email: string; password: string; full_name: string }) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await authApi.register(data);
      localStorage.setItem('finwise_token', response.access_token);
      localStorage.setItem('finwise_user', JSON.stringify(response.user));
      setToken(response.access_token);
      setUser(response.user);
    } catch (err: any) {
      const message =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        'Registration failed. Please check your input and try again.';
      setError(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('finwise_token');
    localStorage.removeItem('finwise_user');
    setToken(null);
    setUser(null);
    setError(null);
  };

  const clearError = () => setError(null);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        error,
        login,
        register,
        logout,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
