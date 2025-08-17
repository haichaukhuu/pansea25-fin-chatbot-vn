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
import './App.css';

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

// Main App Component
const AppContent: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [currentView, setCurrentView] = useState<'chat' | 'profile'>('chat');

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
