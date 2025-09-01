import React, { useState } from 'react';
import { WelcomePage } from './WelcomePage';
import { PreferencesPage } from './PreferencesPage';
import type { UserPreferences } from './PreferencesPage';

interface OnboardingFlowProps {
  onComplete: (preferences: UserPreferences) => void;
}

type OnboardingStep = 'welcome' | 'preferences';

export const OnboardingFlow: React.FC<OnboardingFlowProps> = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState<OnboardingStep>('welcome');

  const handleWelcomeContinue = () => {
    setCurrentStep('preferences');
  };

  const handlePreferencesBack = () => {
    setCurrentStep('welcome');
  };

  const handlePreferencesComplete = (preferences: UserPreferences) => {
    // Store preferences in localStorage for now (since backend logic will be implemented later)
    localStorage.setItem('userPreferences', JSON.stringify(preferences));
    localStorage.setItem('onboardingCompleted', 'true');
    onComplete(preferences);
  };

  switch (currentStep) {
    case 'welcome':
      return <WelcomePage onContinue={handleWelcomeContinue} />;
    case 'preferences':
      return (
        <PreferencesPage 
          onComplete={handlePreferencesComplete}
          onBack={handlePreferencesBack}
        />
      );
    default:
      return <WelcomePage onContinue={handleWelcomeContinue} />;
  }
};

export type { UserPreferences };
