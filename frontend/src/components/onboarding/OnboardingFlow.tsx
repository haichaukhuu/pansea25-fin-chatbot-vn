import React, { useState } from 'react';
import { WelcomePage } from './WelcomePage';
import { PreferencesPage } from './PreferencesPage';
import { apiService } from '../../services/api';
import type { UserPreferences } from './PreferencesPage';

interface OnboardingFlowProps {
  onComplete: (preferences: UserPreferences) => void;
  onError?: (error: string) => void;
}

type OnboardingStep = 'welcome' | 'preferences';

export const OnboardingFlow: React.FC<OnboardingFlowProps> = ({ onComplete, onError }) => {
  const [currentStep, setCurrentStep] = useState<OnboardingStep>('welcome');
  const [isLoading, setIsLoading] = useState(false);

  const handleWelcomeContinue = () => {
    setCurrentStep('preferences');
  };

  const handlePreferencesBack = () => {
    setCurrentStep('welcome');
  };

  const handlePreferencesComplete = async (preferences: UserPreferences) => {
    setIsLoading(true);
    
    try {
      // Use upsert to handle both new and existing users
      const result = await apiService.upsertPreferences(preferences);
      
      if (result.success) {
        // Store preferences locally as backup and for immediate use
        localStorage.setItem('userPreferences', JSON.stringify(preferences));
        localStorage.setItem('onboardingCompleted', 'true');
        
        console.log('Preferences saved successfully:', result.user?.data);
        onComplete(preferences);
      } else {
        // Handle API failure
        const errorMessage = result.message || 'Failed to save preferences';
        console.error('Failed to save preferences:', errorMessage);
        
        // Still save locally as fallback
        localStorage.setItem('userPreferences', JSON.stringify(preferences));
        localStorage.setItem('onboardingCompleted', 'true');
        
        if (onError) {
          onError(`Preferences saved locally but failed to sync with server: ${errorMessage}`);
        }
        
        // Continue with onboarding even if server save failed
        onComplete(preferences);
      }
    } catch (error) {
      console.error('Error saving preferences:', error);
      
      // Save locally as fallback
      localStorage.setItem('userPreferences', JSON.stringify(preferences));
      localStorage.setItem('onboardingCompleted', 'true');
      
      const errorMessage = error instanceof Error ? error.message : 'An unexpected error occurred';
      
      if (onError) {
        onError(`Preferences saved locally but failed to sync with server: ${errorMessage}`);
      }
      
      // Continue with onboarding even if server save failed
      onComplete(preferences);
    } finally {
      setIsLoading(false);
    }
  };

  switch (currentStep) {
    case 'welcome':
      return <WelcomePage onContinue={handleWelcomeContinue} />;
    case 'preferences':
      return (
        <PreferencesPage 
          onComplete={handlePreferencesComplete}
          onBack={handlePreferencesBack}
          isLoading={isLoading}
        />
      );
    default:
      return <WelcomePage onContinue={handleWelcomeContinue} />;
  }
};

export type { UserPreferences };
