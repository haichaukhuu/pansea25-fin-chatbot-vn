import React, { useState, useEffect } from 'react';
import { useLanguage } from '../../context/LanguageContext';
import { CheckIcon, ExclamationTriangleIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import { apiService } from '../../services/api';
import type { UserPreferences } from '../../services/api';

interface UserPreferencePageProps {
  onPreferencesUpdated?: () => void;
}

export const UserPreferencePage: React.FC<UserPreferencePageProps> = ({ onPreferencesUpdated }) => {
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

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [originalPreferences, setOriginalPreferences] = useState<UserPreferences | null>(null);

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

  // Data arrays - keep original Vietnamese for database consistency
  const agriculturalActivitiesData = [
    'Trồng trọt',
    'Chăn nuôi', 
    'Thủy sản',
    'Lâm nghiệp',
    'Nông nghiệp hữu cơ',
    'Chế biến nông sản'
  ];

  const farmScalesData = [
    '0 đến 10 hecta',
    '10 đến 25 hecta', 
    '25 đến 50 hecta',
    '50 đến 100 hecta',
    '>100 hecta'
  ];

  const supportNeedsData = [
    'Lời khuyên về kế hoạch phát triển cho canh tác',
    'Lời khuyên về chọn khoản vay vốn',
    'Học kiến thức tài chính chung',
    'Lời khuyên về quản lí tài chính',
    'Cập nhật xu hướng thị trường và định hướng bán ra'
  ];

  const financialKnowledgeData = [
    'Tôi hoàn toàn không biết',
    'Tôi biết một số dịch vụ tài chính nhưng chưa sử dụng bao giờ',
    'Tôi biết và đã sử dụng dịch vụ tài chính',
    'Tôi biết sâu và đã sử dụng các dịch vụ tài chính thường xuyên'
  ];

  // Translation mappings for display
  const getAgriculturalActivityDisplay = (activity: string) => {
    const mapping: Record<string, string> = {
      'Trồng trọt': t('agricultural.crop_cultivation'),
      'Chăn nuôi': t('agricultural.livestock'),
      'Thủy sản': t('agricultural.aquaculture'),
      'Lâm nghiệp': t('agricultural.forestry'),
      'Nông nghiệp hữu cơ': t('agricultural.organic_farming'),
      'Chế biến nông sản': t('agricultural.food_processing')
    };
    return mapping[activity] || activity;
  };

  const getFarmScaleDisplay = (scale: string) => {
    const mapping: Record<string, string> = {
      '0 đến 10 hecta': t('farm_scale.0_10_hectares'),
      '10 đến 25 hecta': t('farm_scale.10_25_hectares'),
      '25 đến 50 hecta': t('farm_scale.25_50_hectares'),
      '50 đến 100 hecta': t('farm_scale.50_100_hectares'),
      '>100 hecta': t('farm_scale.over_100_hectares')
    };
    return mapping[scale] || scale;
  };

  const getSupportNeedDisplay = (need: string) => {
    const mapping: Record<string, string> = {
      'Lời khuyên về kế hoạch phát triển cho canh tác': t('support.development_planning'),
      'Lời khuyên về chọn khoản vay vốn': t('support.loan_advice'),
      'Học kiến thức tài chính chung': t('support.financial_education'),
      'Lời khuyên về quản lí tài chính': t('support.financial_management'),
      'Cập nhật xu hướng thị trường và định hướng bán ra': t('support.market_trends')
    };
    return mapping[need] || need;
  };

  const getFinancialKnowledgeDisplay = (knowledge: string) => {
    const mapping: Record<string, string> = {
      'Tôi hoàn toàn không biết': t('financial_knowledge.none'),
      'Tôi biết một số dịch vụ tài chính nhưng chưa sử dụng bao giờ': t('financial_knowledge.basic'),
      'Tôi biết và đã sử dụng dịch vụ tài chính': t('financial_knowledge.intermediate'),
      'Tôi biết sâu và đã sử dụng các dịch vụ tài chính thường xuyên': t('financial_knowledge.advanced')
    };
    return mapping[knowledge] || knowledge;
  };

  // Load user preferences on component mount
  useEffect(() => {
    loadUserPreferences();
  }, []);

  // Check for changes when preferences state changes
  useEffect(() => {
    if (originalPreferences) {
      const hasChanged = JSON.stringify(preferences) !== JSON.stringify(originalPreferences);
      setHasChanges(hasChanged);
    }
  }, [preferences, originalPreferences]);

  const loadUserPreferences = async () => {
    setIsLoading(true);
    try {
      const result = await apiService.getPreferences();
      if (result.success && result.user?.data) {
        const loadedPreferences = result.user.data.questionnaire_answer;
        setPreferences(loadedPreferences);
        setOriginalPreferences(loadedPreferences);
      } else {
        // If no preferences found, keep the default empty state
        console.log('No preferences found, using defaults');
        setOriginalPreferences(preferences);
      }
    } catch (error) {
      console.error('Error loading preferences:', error);
      setMessage({ type: 'error', text: t('preferences.error_loading') });
      setOriginalPreferences(preferences);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMultiSelect = (field: 'agriculturalActivity' | 'supportNeeds', value: string) => {
    setPreferences(prev => ({
      ...prev,
      [field]: prev[field].includes(value) 
        ? prev[field].filter(item => item !== value)
        : [...prev[field], value]
    }));
  };

  const validatePreferences = (): boolean => {
    const errors: string[] = [];
    
    if (preferences.agriculturalActivity.length === 0) {
      errors.push(t('preferences.validation.agricultural_activity'));
    }
    
    if (!preferences.location) {
      errors.push(t('preferences.validation.location'));
    }
    
    if (!preferences.farmScale) {
      errors.push(t('preferences.validation.farm_scale'));
    }
    
    if (preferences.supportNeeds.length === 0) {
      errors.push(t('preferences.validation.support_needs'));
    }
    
    if (!preferences.financialKnowledge) {
      errors.push(t('preferences.validation.financial_knowledge'));
    }

    if (errors.length > 0) {
      setMessage({ type: 'error', text: errors.join('. ') });
      return false;
    }

    return true;
  };

  const handleSave = async () => {
    if (!validatePreferences()) {
      return;
    }

    setIsSaving(true);
    setMessage(null);

    try {
      const result = await apiService.updatePreferences(preferences);
      
      if (result.success) {
        setMessage({ 
          type: 'success', 
          text: t('preferences.success_updated')
        });
        setOriginalPreferences(preferences);
        setHasChanges(false);
        
        if (onPreferencesUpdated) {
          onPreferencesUpdated();
        }
      } else {
        setMessage({ 
          type: 'error', 
          text: result.message || t('preferences.error_update_failed')
        });
      }
    } catch (error) {
      console.error('Error updating preferences:', error);
      setMessage({ 
        type: 'error', 
        text: t('preferences.error_saving')
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 border" style={{ borderColor: '#21A691' }}>
        <div className="flex items-center justify-center py-12">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2" style={{ borderColor: '#21A691' }}></div>
            <span style={{ color: '#27403E' }}>{t('preferences.loading')}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 border" style={{ borderColor: '#21A691' }}>
      <h2 className="text-lg font-semibold mb-6" style={{ color: '#27403E' }}>
        {t('profile.preferences')}
      </h2>
      
      {/* Message Display */}
      {message && (
        <div className={`mb-6 p-4 rounded-lg flex items-center space-x-3 ${
          message.type === 'success' 
            ? 'bg-green-50 border border-green-200' 
            : 'bg-red-50 border border-red-200'
        }`}>
          {message.type === 'success' ? (
            <CheckCircleIcon className="h-5 w-5 text-green-600" />
          ) : (
            <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />
          )}
          <span className={message.type === 'success' ? 'text-green-700' : 'text-red-700'}>
            {message.text}
          </span>
        </div>
      )}

      <div className="space-y-8">
        {/* Agricultural Activity */}
        <div>
          <label className="block text-sm font-medium mb-3" style={{ color: '#27403E' }}>
            {t('onboarding.preferences.agricultural_activity')} *
          </label>
          <div className="grid grid-cols-2 gap-3">
            {agriculturalActivitiesData.map((activity) => (
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
                <span className="text-sm">{getAgriculturalActivityDisplay(activity)}</span>
                {preferences.agriculturalActivity.includes(activity) && (
                  <CheckIcon className="h-4 w-4 text-green-600" />
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Crop and Livestock Types */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: '#27403E' }}>
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
            <label className="block text-sm font-medium mb-2" style={{ color: '#27403E' }}>
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

        {/* Location */}
        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: '#27403E' }}>
            {t('onboarding.preferences.location')} *
          </label>
          <select
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
            value={preferences.location}
            onChange={(e) => setPreferences(prev => ({ ...prev, location: e.target.value }))}
          >
            <option value="">{t('preferences.location_placeholder')}</option>
            {vietnamLocations.map((location) => (
              <option key={location} value={location}>
                {location}
              </option>
            ))}
          </select>
        </div>

        {/* Farm Scale */}
        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: '#27403E' }}>
            {t('onboarding.preferences.farm_scale')} *
          </label>
          <div className="space-y-3">
            {farmScalesData.map((scale) => (
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
                <span>{getFarmScaleDisplay(scale)}</span>
                {preferences.farmScale === scale && (
                  <CheckIcon className="h-4 w-4 text-green-600" />
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Support Needs */}
        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: '#27403E' }}>
            {t('onboarding.preferences.support_needs')} *
          </label>
          <div className="space-y-3">
            {supportNeedsData.map((need) => (
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
                <span className="text-sm">{getSupportNeedDisplay(need)}</span>
                {preferences.supportNeeds.includes(need) && (
                  <CheckIcon className="h-4 w-4 text-green-600" />
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Financial Knowledge */}
        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: '#27403E' }}>
            {t('onboarding.preferences.financial_knowledge')} *
          </label>
          <div className="space-y-3">
            {financialKnowledgeData.map((knowledge) => (
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
                <span className="text-sm">{getFinancialKnowledgeDisplay(knowledge)}</span>
                {preferences.financialKnowledge === knowledge && (
                  <CheckIcon className="h-4 w-4 text-green-600" />
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end pt-6 border-t border-gray-200">
          <button
            onClick={handleSave}
            disabled={!hasChanges || isSaving}
            className="px-6 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            style={{
              backgroundColor: hasChanges && !isSaving ? '#21A691' : '#9CA3AF',
              color: '#ffffff'
            }}
            onMouseEnter={(e) => {
              if (hasChanges && !isSaving) {
                e.currentTarget.style.backgroundColor = '#87DF2C';
                e.currentTarget.style.color = '#000000';
              }
            }}
            onMouseLeave={(e) => {
              if (hasChanges && !isSaving) {
                e.currentTarget.style.backgroundColor = '#21A691';
                e.currentTarget.style.color = '#ffffff';
              }
            }}
          >
            {isSaving && (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            )}
            <span>
              {isSaving ? t('preferences.saving') : t('preferences.save_changes')}
            </span>
          </button>
        </div>
      </div>
    </div>
  );
};
