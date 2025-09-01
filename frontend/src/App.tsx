import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ChatProvider } from './context/ChatContext';
import { LanguageProvider } from './context/LanguageContext';
import { LoginForm } from './components/auth/LoginForm';
import { RegisterForm } from './components/auth/RegisterForm';
import { ChatInterface } from './components/chat/ChatInterface';
import { ChatInitializer } from './components/chat/ChatInitializer';
import { ProfilePage } from './components/profile/ProfilePage';
import { OnboardingFlow } from './components/onboarding/OnboardingFlow';
import type { UserPreferences } from './components/onboarding/OnboardingFlow';
import './App.css';

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

// Main App Component
const AppContent: React.FC = () => {
  const { isAuthenticated, user, isNewUser, completeOnboarding } = useAuth();
  const [currentView, setCurrentView] = useState<'chat' | 'profile'>('chat');

  // Handle onboarding completion
  const handleOnboardingComplete = (preferences: UserPreferences) => {
    console.log('Onboarding completed with preferences:', preferences);
    completeOnboarding();
  };

  // Not authenticated - show login/register pages
  if (!isAuthenticated) {
    return (
      <Routes>
        <Route 
          path="/login" 
          element={<LoginForm onSuccess={() => {}} />} 
        />
        <Route 
          path="/register" 
          element={<RegisterForm onSuccess={() => {}} />} 
        />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  // Authenticated but needs onboarding (only for new users from registration)
  // Note: Login users and returning users should never hit this condition
  if (isNewUser || (user && !user.hasCompletedOnboarding)) {
    return (
      <Routes>
        <Route 
          path="/onboarding" 
          element={<OnboardingFlow onComplete={handleOnboardingComplete} />} 
        />
        <Route path="*" element={<Navigate to="/onboarding" replace />} />
      </Routes>
    );
  }

  // Authenticated and completed onboarding - show main app

  return (
    <ChatProvider>
      <ChatInitializer>
        <Routes>
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                {currentView === 'chat' ? (
                  <ChatInterface 
                    onNavigateToProfile={() => setCurrentView('profile')} 
                  />
                ) : (
                  <ProfilePage 
                    onBack={() => setCurrentView('chat')} 
                  />
                )}
              </ProtectedRoute>
            } 
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </ChatInitializer>
    </ChatProvider>
  );
};

function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <Router>
          <div className="App">
            <AppContent />
          </div>
        </Router>
      </AuthProvider>
    </LanguageProvider>
  );
}

export default App;
