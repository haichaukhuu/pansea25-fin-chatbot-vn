import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { AuthState, User } from '../types';
import { apiService } from '../services/api';

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<boolean>;
  loginWithGoogle: (googleUser: any) => Promise<boolean>;
  register: (email: string, password: string, name: string) => Promise<boolean>;
  logout: () => void;
  checkAuthStatus: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false
  });

  // Check if user is already authenticated on app load
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async (): Promise<void> => {
    const token = localStorage.getItem('authToken');
    if (token) {
      const result = await apiService.verifyToken(token);
      if (result.success && result.user) {
        const user: User = {
          id: result.user.uid,
          email: result.user.email,
          name: result.user.display_name || result.user.email.split('@')[0],
          avatar: result.user.photo_url,
          provider: result.user.provider || 'email'
        };
        setAuthState({
          user,
          isAuthenticated: true
        });
      } else {
        // Token is invalid, clear it
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
      }
    }
  };

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const result = await apiService.login({ email, password });
      
      if (result.success && result.user && result.access_token) {
        const user: User = {
          id: result.user.uid,
          email: result.user.email,
          name: result.user.display_name || email.split('@')[0],
          avatar: result.user.photo_url,
          provider: 'email'
        };
        
        // Store auth data
        localStorage.setItem('authToken', result.access_token);
        localStorage.setItem('currentUser', JSON.stringify(user));
        
        setAuthState({
          user,
          isAuthenticated: true
        });
        return true;
      }
      return false;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };

  const loginWithGoogle = async (googleUser: any): Promise<boolean> => {
    try {
      const result = await apiService.loginWithGoogle({ 
        id_token: googleUser.credential,
        email: googleUser.email,
        name: googleUser.name,
        avatar: googleUser.picture
      });
      
      if (result.success && result.user && result.access_token) {
        const user: User = {
          id: result.user.uid,
          email: result.user.email,
          name: result.user.display_name || googleUser.name,
          avatar: result.user.photo_url || googleUser.picture,
          provider: 'google'
        };
        
        // Store auth data
        localStorage.setItem('authToken', result.access_token);
        localStorage.setItem('currentUser', JSON.stringify(user));
        
        setAuthState({
          user,
          isAuthenticated: true
        });
        return true;
      }
      return false;
    } catch (error) {
      console.error('Google login error:', error);
      return false;
    }
  };

  const register = async (email: string, password: string, name: string): Promise<boolean> => {
    try {
      const result = await apiService.register({ 
        email, 
        password, 
        display_name: name 
      });
      
      if (result.success && result.user) {
        const user: User = {
          id: result.user.uid,
          email: result.user.email,
          name: result.user.display_name || name,
          provider: 'email'
        };
        
        setAuthState({
          user,
          isAuthenticated: true
        });
        return true;
      }
      return false;
    } catch (error) {
      console.error('Registration error:', error);
      return false;
    }
  };
  
  const logout = () => {
    // Clear stored auth data
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    
    setAuthState({
      user: null,
      isAuthenticated: false
    });
  };

  return (
    <AuthContext.Provider value={{
      ...authState,
      login,
      loginWithGoogle,
      register,
      logout,
      checkAuthStatus
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
