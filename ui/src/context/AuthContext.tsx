import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';
import type { AuthState, User } from '../types';

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<boolean>;
  register: (email: string, password: string, name: string) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const DEMO_USER: User = {
  id: '1',
  email: 'admin123@gmail.com',
  name: 'Admin User'
};

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false
  });

  const login = async (email: string, password: string): Promise<boolean> => {
    // Demo authentication - only accepts the specified credentials
    if (email === 'admin123@gmail.com' && password === 'admin123') {
      setAuthState({
        user: DEMO_USER,
        isAuthenticated: true
      });
      return true;
    }
    return false;
  };

  const register = async (email: string, password: string, name: string): Promise<boolean> => {
    // Demo registration - just return true for any valid input
    if (email && password && name) {
      const newUser: User = {
        id: Math.random().toString(36).substr(2, 9),
        email,
        name
      };
      setAuthState({
        user: newUser,
        isAuthenticated: true
      });
      return true;
    }
    return false;
  };

  const logout = () => {
    setAuthState({
      user: null,
      isAuthenticated: false
    });
  };

  return (
    <AuthContext.Provider value={{
      ...authState,
      login,
      register,
      logout
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
