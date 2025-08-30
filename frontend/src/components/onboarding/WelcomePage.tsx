import React, { useState, useRef, useEffect } from 'react';
import { useLanguage } from '../../context/LanguageContext';
import { ChevronDownIcon } from '@heroicons/react/24/outline';
import type { Language } from '../../context/LanguageContext';
import { 
  CheckBadgeIcon,
  ChartBarIcon,
  BanknotesIcon,
  ArrowTrendingUpIcon
} from '@heroicons/react/24/outline';

interface WelcomePageProps {
  onContinue: () => void;
}

export const WelcomePage: React.FC<WelcomePageProps> = ({ onContinue }) => {
  const { t, language, setLanguage } = useLanguage();
  const [isLanguageOpen, setIsLanguageOpen] = useState(false);
  const languageRef = useRef<HTMLDivElement>(null);

  const languages: { code: Language; name: string; flag: string }[] = [
    {
      code: 'vi',
      name: t('language.vietnamese'),
      flag: '🇻🇳'
    },
    {
      code: 'en',
      name: t('language.english'),
      flag: '🇺🇸'
    }
  ];

  const currentLanguage = languages.find(lang => lang.code === language);

  const handleLanguageChange = (newLanguage: Language) => {
    setLanguage(newLanguage);
    setIsLanguageOpen(false);
  };

  // Close language selector when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (languageRef.current && !languageRef.current.contains(event.target as Node)) {
        setIsLanguageOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const features = [
    {
      icon: CheckBadgeIcon,
      title: t('onboarding.welcome.feature1_title'),
      description: t('onboarding.welcome.feature1_desc')
    },
    {
      icon: ChartBarIcon,
      title: t('onboarding.welcome.feature2_title'),
      description: t('onboarding.welcome.feature2_desc')
    },
    {
      icon: BanknotesIcon,
      title: t('onboarding.welcome.feature3_title'),
      description: t('onboarding.welcome.feature3_desc')
    },
    {
      icon: ArrowTrendingUpIcon,
      title: t('onboarding.welcome.feature4_title'),
      description: t('onboarding.welcome.feature4_desc')
    }
  ];

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative"
      style={{
        background: `linear-gradient(135deg, #B4B4B2 0%, #FFFFFF 100%)`,
        backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), url('/background3.jpg')`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundAttachment: 'fixed'
      }}
    >
      <div className="max-w-4xl w-full space-y-8">
        {/* Language Selector */}
        <div className="flex justify-end">
          <div ref={languageRef} className="bg-white bg-opacity-90 backdrop-blur-sm rounded-lg p-2 border border-gray-200 relative">
            <button
              onClick={() => setIsLanguageOpen(!isLanguageOpen)}
              className="flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors hover:bg-gray-100 text-gray-700"
            >
              <span className="text-lg">{currentLanguage?.flag}</span>
              <span className="text-sm font-medium hidden sm:block">
                {currentLanguage?.code.toUpperCase()}
              </span>
              <ChevronDownIcon 
                className={`h-4 w-4 transition-transform ${isLanguageOpen ? 'rotate-180' : ''}`} 
              />
            </button>

            {isLanguageOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
                <div className="py-1">
                  {languages.map((lang) => (
                    <button
                      key={lang.code}
                      onClick={() => handleLanguageChange(lang.code)}
                      className={`w-full flex items-center space-x-3 px-4 py-2 text-left hover:bg-gray-50 transition-colors ${
                        language === lang.code ? 'bg-blue-50 text-blue-600' : 'text-gray-700'
                      }`}
                    >
                      <span className="text-lg">{lang.flag}</span>
                      <span className="text-sm font-medium">{lang.name}</span>
                      {language === lang.code && (
                        <div className="ml-auto w-2 h-2 bg-blue-600 rounded-full"></div>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
        
        {/* Main Content */}
        <div className="text-center">
          <h1 className="text-4xl font-bold text-white mb-4">
            {t('onboarding.welcome.title')}
          </h1>
          <p className="text-xl text-white mb-12">
            {t('onboarding.welcome.subtitle')}
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          {features.map((feature, index) => (
            <div 
              key={index}
              className="bg-white bg-opacity-95 backdrop-blur-sm rounded-lg p-6 border border-opacity-20"
              style={{ borderColor: '#21A691' }}
            >
              <div className="flex items-start space-x-4">
                <div 
                  className="flex-shrink-0 w-12 h-12 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: '#21A691' }}
                >
                  <feature.icon className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600">
                    {feature.description}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Get Started Button */}
        <div className="text-center">
          <button
            onClick={onContinue}
            className="px-8 py-4 text-lg font-medium rounded-lg transition-all transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-opacity-50"
            style={{
              backgroundColor: '#21A691',
              color: '#ffffff',
              boxShadow: '0 4px 14px 0 rgba(33, 166, 145, 0.39)'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#87DF2C';
              e.currentTarget.style.color = '#000000';
              e.currentTarget.style.boxShadow = '0 6px 20px 0 rgba(135, 223, 44, 0.4)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = '#21A691';
              e.currentTarget.style.color = '#ffffff';
              e.currentTarget.style.boxShadow = '0 4px 14px 0 rgba(33, 166, 145, 0.39)';
            }}
            onFocus={(e) => {
              e.currentTarget.style.boxShadow = '0 0 0 4px rgba(135, 223, 44, 0.5)';
            }}
          >
            {t('onboarding.welcome.get_started')}
          </button>
        </div>
      </div>
    </div>
  );
};
