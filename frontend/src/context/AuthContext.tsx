import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { AuthState, User } from '../types';
import { apiService } from '../services/api';

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<boolean>;
  register: (email: string, password: string, name: string) => Promise<[boolean, string?]>;
  logout: () => void;
  checkAuthStatus: () => Promise<void>;
  completeOnboarding: () => void;
  isNewUser: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false
  });
  const [isNewUser, setIsNewUser] = useState(false);

  // Check if user is already authenticated on app load
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async (): Promise<void> => {
    const token = localStorage.getItem('authToken');
    if (token) {
      const result = await apiService.verifyToken(token);
      if (result.success && result.user) {
        // For token verification, if user has a valid token, they're an existing user
        const hasCompletedOnboarding = localStorage.getItem('onboardingCompleted') === 'true';
        const user: User = {
          id: result.user.id,
          email: result.user.email,
          name: result.user.display_name || result.user.email.split('@')[0],
          hasCompletedOnboarding: hasCompletedOnboarding // Use localStorage value for token verification
        };
        setAuthState({
          user,
          isAuthenticated: true
        });
        
        // Don't trigger onboarding for existing authenticated users
        setIsNewUser(false);
      } else {
        // Token is invalid, clear it
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        localStorage.removeItem('onboardingCompleted');
        localStorage.removeItem('userPreferences');
      }
    }
  };

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const result = await apiService.login({ email, password });
      
      if (result.success && result.user && result.access_token) {
        // For login, we assume the user is an existing user who has completed onboarding
        const user: User = {
          id: result.user.id,
          email: result.user.email,
          name: result.user.display_name || email.split('@')[0],
          hasCompletedOnboarding: true // Existing users have completed onboarding
        };
        
        // Store auth data
        localStorage.setItem('authToken', result.access_token);
        localStorage.setItem('currentUser', JSON.stringify(user));
        // Ensure onboarding is marked as completed for existing users
        localStorage.setItem('onboardingCompleted', 'true');
        
        setAuthState({
          user,
          isAuthenticated: true
        });
        
        // Existing users should not go through onboarding
        setIsNewUser(false);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };

  const register = async (email: string, password: string, name: string): Promise<[boolean, string?]> => {
    try {
      const result = await apiService.register({ 
        email, 
        password, 
        display_name: name 
      });
      
      if (result.success && result.user) {
        // After successful registration, login to get access token
        const loginResult = await apiService.login({ email, password });
        
        if (loginResult.success && loginResult.access_token) {
          const user: User = {
            id: result.user.id,
            email: result.user.email,
            name: result.user.display_name || name,
            hasCompletedOnboarding: false // New users haven't completed onboarding
          };
          
          // Store auth data for new user
          localStorage.setItem('authToken', loginResult.access_token);
          localStorage.setItem('currentUser', JSON.stringify(user));
          
          setAuthState({
            user,
            isAuthenticated: true
          });
          
          // Set as new user for onboarding flow
          setIsNewUser(true);
          return [true, undefined];
        }
      }
      return [false, result.message || 'Registration failed'];
    } catch (error: any) {
      console.error('Registration error:', error);
      return [false, error.message || 'An error occurred during registration'];
    }
  };

  const completeOnboarding = () => {
    if (authState.user) {
      const updatedUser: User = {
        ...authState.user,
        hasCompletedOnboarding: true
      };
      
      setAuthState({
        user: updatedUser,
        isAuthenticated: true
      });
      
      setIsNewUser(false);
      localStorage.setItem('currentUser', JSON.stringify(updatedUser));
      localStorage.setItem('onboardingCompleted', 'true');
    }
  };
  const logout = () => {
    // Call backend logout to clear refresh token cookie
    apiService.logout().catch(error => {
      console.warn('Backend logout failed:', error);
    });
    
    // Clear stored auth data
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    localStorage.removeItem('onboardingCompleted');
    localStorage.removeItem('userPreferences');
    
    setAuthState({
      user: null,
      isAuthenticated: false
    });
    
    setIsNewUser(false);
  };

  return (
    <AuthContext.Provider value={{
      ...authState,
      login,
      register,
      logout,
      checkAuthStatus,
      completeOnboarding,
      isNewUser
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
