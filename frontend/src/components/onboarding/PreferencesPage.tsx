import React, { useState } from 'react';
import { useLanguage } from '../../context/LanguageContext';
import { ArrowLeftIcon, CheckIcon } from '@heroicons/react/24/outline';

interface PreferencesPageProps {
  onComplete: (preferences: UserPreferences) => void;
  onBack: () => void;
  isLoading?: boolean;
}

export interface UserPreferences {
  agriculturalActivity: string[];
  cropType: string;
  livestockType: string;
  location: string;
  farmScale: string;
  supportNeeds: string[];
  financialKnowledge: string;
}

export const PreferencesPage: React.FC<PreferencesPageProps> = ({ onComplete, onBack, isLoading = false }) => {
  const { t } = useLanguage();
  
  const [preferences, setPreferences] = useState<UserPreferences>({
    agriculturalActivity: [],
    cropType: '',
    livestockType: '',
    location: '',
    farmScale: '',
    supportNeeds: [],
    financialKnowledge: ''
  });

  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = 3;

  // Vietnamese provinces and cities (all 63)
  const vietnamLocations = [
    'An Giang', 'Bà Rịa - Vũng Tàu', 'Bắc Giang', 'Bắc Kạn', 'Bạc Liêu', 'Bắc Ninh',
    'Bến Tre', 'Bình Định', 'Bình Dương', 'Bình Phước', 'Bình Thuận', 'Cà Mau',
    'Cao Bằng', 'Đắk Lắk', 'Đắk Nông', 'Điện Biên', 'Đồng Nai', 'Đồng Tháp',
    'Gia Lai', 'Hà Giang', 'Hà Nam', 'Hà Tĩnh', 'Hải Dương', 'Hậu Giang',
    'Hòa Bình', 'Hưng Yên', 'Khánh Hòa', 'Kiên Giang', 'Kon Tum', 'Lai Châu',
    'Lâm Đồng', 'Lạng Sơn', 'Lào Cai', 'Long An', 'Nam Định', 'Nghệ An',
    'Ninh Bình', 'Ninh Thuận', 'Phú Thọ', 'Quảng Bình', 'Quảng Nam', 'Quảng Ngãi',
    'Quảng Ninh', 'Quảng Trị', 'Sóc Trăng', 'Sơn La', 'Tây Ninh', 'Thái Bình',
    'Thái Nguyên', 'Thanh Hóa', 'Thừa Thiên Huế', 'Tiền Giang', 'Trà Vinh',
    'Tuyên Quang', 'Vĩnh Long', 'Vĩnh Phúc', 'Yên Bái', 'Phú Yên', 'Cần Thơ',
    'Đà Nẵng', 'Hải Phòng', 'Hà Nội', 'TP. Hồ Chí Minh'
  ].sort();

  const agriculturalActivities = [
    'Trồng trọt',
    'Chăn nuôi', 
    'Thủy sản',
    'Lâm nghiệp',
    'Nông nghiệp hữu cơ',
    'Chế biến nông sản'
  ];

  const farmScales = [
    '0 đến 10 hecta',
    '10 đến 25 hecta', 
    '25 đến 50 hecta',
    '50 đến 100 hecta',
    '>100 hecta'
  ];

  const supportNeedsOptions = [
    'Lời khuyên về kế hoạch phát triển cho canh tác',
    'Lời khuyên về chọn khoản vay vốn',
    'Học kiến thức tài chính chung',
    'Lời khuyên về quản lí tài chính',
    'Cập nhật xu hướng thị trường và định hướng bán ra'
  ];

  const financialKnowledgeOptions = [
    'Tôi hoàn toàn không biết',
    'Tôi biết một số dịch vụ tài chính nhưng chưa sử dụng bao giờ',
    'Tôi biết và đã sử dụng dịch vụ tài chính',
    'Tôi biết sâu và đã sử dụng các dịch vụ tài chính thường xuyên'
  ];

  const handleMultiSelect = (field: 'agriculturalActivity' | 'supportNeeds', value: string) => {
    setPreferences(prev => ({
      ...prev,
      [field]: prev[field].includes(value) 
        ? prev[field].filter(item => item !== value)
        : [...prev[field], value]
    }));
  };

  const isStepValid = () => {
    switch (currentStep) {
      case 1:
        return preferences.agriculturalActivity.length > 0;
      case 2:
        return preferences.location && preferences.farmScale;
      case 3:
        return preferences.supportNeeds.length > 0 && preferences.financialKnowledge;
      default:
        return false;
    }
  };

  const nextStep = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
    } else {
      onComplete(preferences);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    } else {
      onBack();
    }
  };

  return (
    <div className="min-h-screen py-12 px-4 sm:px-6 lg:px-8"
      style={{
        background: `linear-gradient(135deg, #B4B4B2 0%, #FFFFFF 100%)`,
        backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), url('/background3.jpg')`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundAttachment: 'fixed'
      }}
    >
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={prevStep}
              className="flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors"
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                color: '#ffffff',
                backdropFilter: 'blur(10px)'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = 'rgba(33, 166, 145, 0.8)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
              }}
            >
              <ArrowLeftIcon className="h-5 w-5" />
              <span>{t('onboarding.preferences.back')}</span>
            </button>
            
            <div className="text-white">
              {currentStep} / {totalSteps}
            </div>
          </div>
          
          <h1 className="text-3xl font-bold text-white mb-2">
            {t('onboarding.preferences.title')}
          </h1>
          <p className="text-lg text-white opacity-90">
            {t('onboarding.preferences.subtitle')}
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="w-full bg-white bg-opacity-30 rounded-full h-2">
            <div 
              className="h-2 rounded-full transition-all duration-300"
              style={{
                backgroundColor: '#21A691',
                width: `${(currentStep / totalSteps) * 100}%`
              }}
            />
          </div>
        </div>

        {/* Form Content */}
        <div className="bg-white bg-opacity-95 backdrop-blur-sm rounded-lg p-8 shadow-xl">
          {/* Step 1: Basic Information */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('onboarding.preferences.agricultural_activity')} *
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {agriculturalActivities.map((activity) => (
                    <button
                      key={activity}
                      type="button"
                      onClick={() => handleMultiSelect('agriculturalActivity', activity)}
                      className={`flex items-center justify-between p-3 border rounded-lg transition-all ${
                        preferences.agriculturalActivity.includes(activity)
                          ? 'border-green-500 bg-green-50 text-green-700'
                          : 'border-gray-300 hover:border-green-300'
                      }`}
                    >
                      <span className="text-sm">{activity}</span>
                      {preferences.agriculturalActivity.includes(activity) && (
                        <CheckIcon className="h-4 w-4 text-green-600" />
                      )}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('onboarding.preferences.crop_type')}
                  </label>
                  <input
                    type="text"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
                    placeholder={t('onboarding.preferences.crop_type_placeholder')}
                    value={preferences.cropType}
                    onChange={(e) => setPreferences(prev => ({ ...prev, cropType: e.target.value }))}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('onboarding.preferences.livestock_type')}
                  </label>
                  <input
                    type="text"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
                    placeholder={t('onboarding.preferences.livestock_type_placeholder')}
                    value={preferences.livestockType}
                    onChange={(e) => setPreferences(prev => ({ ...prev, livestockType: e.target.value }))}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Location and Scale */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('onboarding.preferences.location')} *
                </label>
                <select
                  required
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
                  value={preferences.location}
                  onChange={(e) => setPreferences(prev => ({ ...prev, location: e.target.value }))}
                >
                  <option value="">Chọn tỉnh/thành phố</option>
                  {vietnamLocations.map((location) => (
                    <option key={location} value={location}>
                      {location}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('onboarding.preferences.farm_scale')} *
                </label>
                <div className="space-y-3">
                  {farmScales.map((scale) => (
                    <button
                      key={scale}
                      type="button"
                      onClick={() => setPreferences(prev => ({ ...prev, farmScale: scale }))}
                      className={`w-full flex items-center justify-between p-3 border rounded-lg transition-all text-left ${
                        preferences.farmScale === scale
                          ? 'border-green-500 bg-green-50 text-green-700'
                          : 'border-gray-300 hover:border-green-300'
                      }`}
                    >
                      <span>{scale}</span>
                      {preferences.farmScale === scale && (
                        <CheckIcon className="h-4 w-4 text-green-600" />
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Support Needs and Financial Knowledge */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('onboarding.preferences.support_needs')} *
                </label>
                <div className="space-y-3">
                  {supportNeedsOptions.map((need) => (
                    <button
                      key={need}
                      type="button"
                      onClick={() => handleMultiSelect('supportNeeds', need)}
                      className={`w-full flex items-center justify-between p-3 border rounded-lg transition-all text-left ${
                        preferences.supportNeeds.includes(need)
                          ? 'border-green-500 bg-green-50 text-green-700'
                          : 'border-gray-300 hover:border-green-300'
                      }`}
                    >
                      <span className="text-sm">{need}</span>
                      {preferences.supportNeeds.includes(need) && (
                        <CheckIcon className="h-4 w-4 text-green-600" />
                      )}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('onboarding.preferences.financial_knowledge')} *
                </label>
                <div className="space-y-3">
                  {financialKnowledgeOptions.map((knowledge) => (
                    <button
                      key={knowledge}
                      type="button"
                      onClick={() => setPreferences(prev => ({ ...prev, financialKnowledge: knowledge }))}
                      className={`w-full flex items-center justify-between p-3 border rounded-lg transition-all text-left ${
                        preferences.financialKnowledge === knowledge
                          ? 'border-green-500 bg-green-50 text-green-700'
                          : 'border-gray-300 hover:border-green-300'
                      }`}
                    >
                      <span className="text-sm">{knowledge}</span>
                      {preferences.financialKnowledge === knowledge && (
                        <CheckIcon className="h-4 w-4 text-green-600" />
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="mt-8 flex justify-end">
            <button
              onClick={nextStep}
              disabled={!isStepValid() || isLoading}
              className="px-6 py-3 font-medium rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              style={{
                backgroundColor: (isStepValid() && !isLoading) ? '#21A691' : '#9CA3AF',
                color: '#ffffff'
              }}
              onMouseEnter={(e) => {
                if (isStepValid() && !isLoading) {
                  e.currentTarget.style.backgroundColor = '#87DF2C';
                  e.currentTarget.style.color = '#000000';
                }
              }}
              onMouseLeave={(e) => {
                if (isStepValid() && !isLoading) {
                  e.currentTarget.style.backgroundColor = '#21A691';
                  e.currentTarget.style.color = '#ffffff';
                }
              }}
            >
              {isLoading && (
                <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              )}
              <span>
                {isLoading ? 
                  'Saving...' : 
                  (currentStep === totalSteps 
                    ? t('onboarding.preferences.complete')
                    : t('onboarding.preferences.continue')
                  )
                }
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
