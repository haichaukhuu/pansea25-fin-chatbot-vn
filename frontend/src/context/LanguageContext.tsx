import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';
import { format, formatDistanceToNow } from 'date-fns';
import { vi, enUS } from 'date-fns/locale';

export type Language = 'vi' | 'en';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string, params?: Record<string, string>) => string;
  formatDate: (date: Date, formatType?: 'short' | 'long' | 'relative') => string;
  formatTime: (date: Date) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

// Vietnamese translations
const translations = {
  vi: {
    'welcome.title': 'Chào mừng đến với Chatbot Tài chính',
    'welcome.subtitle': 'Bắt đầu cuộc trò chuyện hoặc chọn chat từ thanh bên',
    'welcome.new_conversation': 'Bắt đầu cuộc trò chuyện mới',
    'welcome.description': 'Hỏi tôi bất cứ điều gì về lập kế hoạch tài chính, đầu tư hoặc thị trường ASEAN',
    'welcome.bullet1': '• Nhận lời khuyên tài chính cá nhân hóa',
    'welcome.bullet2': '• Tìm hiểu về chiến lược đầu tư',
    'welcome.bullet3': '• Khám phá thị trường tài chính Việt Nam',
    'header.title': 'Chatbot Tài chính',
    'header.subtitle': 'Trợ lý AI tài chính cho nông dân',
    'chat.new_chat_title': 'Cuộc trò chuyện mới',
    'profile.title': 'Hồ sơ người dùng',
    'login.title': 'Đăng nhập',
    'register.title': 'Đăng ký',
    'language.vietnamese': 'Tiếng Việt',
    'language.english': 'English',
    'sidebar.generated_files': 'Tệp đã tạo',
    'sidebar.chat_history': 'Lịch sử trò chuyện',
    'profile.profile': 'Hồ sơ',
    'profile.account': 'Tài khoản',
    'profile.preferences': 'Tùy chọn',
    'profile.profile_info': 'Thông tin hồ sơ',
    'profile.full_name': 'Họ và tên',
    'profile.email_address': 'Địa chỉ E-mail',
    'profile.change_avatar': 'Thay đổi ảnh đại diện',
    'profile.save_changes': 'Lưu thay đổi',
    'profile.change_password': 'Thay đổi mật khẩu',
    'profile.current_password': 'Mật khẩu hiện tại',
    'profile.new_password': 'Mật khẩu mới',
    'profile.confirm_password': 'Xác nhận mật khẩu',
    'profile.update_password': 'Cập nhật mật khẩu',
    'profile.notifications': 'Thông báo',
    'profile.email_notifications': 'Nhận thông báo qua E-mail',
    'profile.notifications_desc': 'Nhận cập nhật về chat và tài khoản của bạn',
    'profile.sign_out': 'Đăng xuất',
    'profile.save_preferences': 'Lưu tùy chọn',
    'profile.dont_have_account': 'Chưa có tài khoản? Đăng ký',
    'profile.already_have_account': 'Đã có tài khoản? Đăng nhập',
    'profile.creating_account': 'Đang tạo tài khoản...',
    'profile.sign_up': 'Đăng ký',
    'profile.signing_in': 'Đang đăng nhập...',
    'profile.sign_in': 'Đăng nhập',
    'common.or': 'hoặc',
    'profile.account_settings': 'Cài đặt tài khoản',
    'profile.change_password_section': 'Thay đổi mật khẩu',
    'profile.account_deletion': 'Xóa tài khoản',
    'profile.delete_account': 'Xóa tài khoản',
    'profile.delete_account_desc': 'Xóa vĩnh viễn tài khoản và toàn bộ dữ liệu liên quan.',
    'profile.avatar_hint': 'JPG, GIF hoặc PNG. Kích thước tối đa 1MB.',
    'date.today': 'Hôm nay',
    'date.yesterday': 'Hôm qua',
    'api.error': 'Đã xảy ra lỗi, vui lòng thử lại sau.',
    'api.streaming_error': 'Xin lỗi, tôi đã gặp lỗi. Vui lòng thử lại.',
    'api.connection_error': 'Xin lỗi, tôi đã gặp lỗi khi xử lý tin nhắn của bạn. Vui lòng thử nhập lại tin nhắn.',
    'api.mock_error': 'Đã xảy ra lỗi',
    'input.placeholder_normal': 'Nhập tin nhắn của bạn...',
    'input.placeholder_generating': 'AI đang tạo phản hồi...',
    'input.speech_not_supported': 'Trình duyệt của bạn không hỗ trợ nhận dạng giọng nói.',
    'input.send_message': 'Gửi tin nhắn',
    'input.stop_generation': 'Dừng tạo nội dung',
    'input.recording': 'Đang ghi âm...',
    'chat.typing': 'AI đang trả lời...',
    'chat.ai_responding': 'AI đang trả lời...',
    'history.loading': 'Đang tải lịch sử trò chuyện...',
    'history.no_chats': 'Chưa có cuộc trò chuyện nào. Bắt đầu cuộc trò chuyện mới!',
    'history.all_chats_loaded': 'Đã tải tất cả cuộc trò chuyện',
    // Transcription translations
    'transcription.result_title': 'Kết quả phiên âm',
    'transcription.confidence': 'Độ tin cậy:',
    'transcription.transcribed_text': 'Văn bản đã phiên âm:',
    'transcription.click_to_edit': 'Nhấp để chỉnh sửa',
    'transcription.no_text': 'Không có phiên âm nào',
    'transcription.cancel': 'Hủy',
    'transcription.confirm_send': 'Xác nhận & Gửi',
    'transcription.edit_help': 'Bạn có thể chỉnh sửa văn bản đã phiên âm trước khi gửi tới chatbot',
    'transcription.processing': 'Đang xử lý',
    'transcription.listening': 'Đang nghe...',
    'transcription.tap_to_stop': 'Nhấn để dừng ghi âm',
    'transcription.processing_audio': 'Đang xử lý âm thanh',
    'transcription.stop': 'Dừng',
    // Onboarding translations
    'onboarding.welcome.title': 'Chào mừng đến với Chatbot Tài chính PANSEA',
    'onboarding.welcome.subtitle': 'Trợ lý AI tài chính dành cho nông dân Việt Nam',
    'onboarding.welcome.feature1_title': 'Lời khuyên tài chính cá nhân hóa',
    'onboarding.welcome.feature1_desc': 'Nhận hướng dẫn tài chính phù hợp với tình hình nông nghiệp của bạn',
    'onboarding.welcome.feature2_title': 'Hỗ trợ kế hoạch phát triển',
    'onboarding.welcome.feature2_desc': 'Tư vấn về kế hoạch canh tác và phát triển bền vững',
    'onboarding.welcome.feature3_title': 'Quản lý tài chính hiệu quả',
    'onboarding.welcome.feature3_desc': 'Học cách quản lý tài chính và chọn lựa khoản vay phù hợp',
    'onboarding.welcome.feature4_title': 'Cập nhật thị trường',
    'onboarding.welcome.feature4_desc': 'Theo dõi xu hướng thị trường và định hướng bán ra',
    'onboarding.welcome.get_started': 'Bắt đầu',
    'onboarding.welcome.language_selection': 'Chọn ngôn ngữ',
    'onboarding.preferences.title': 'Thiết lập thông tin cá nhân',
    'onboarding.preferences.subtitle': 'Hãy cho chúng tôi biết về tình hình nông nghiệp của bạn để có thể hỗ trợ tốt nhất',
    'onboarding.preferences.agricultural_activity': 'Loại hoạt động nông nghiệp',
    'onboarding.preferences.crop_type': 'Loại cây trồng',
    'onboarding.preferences.crop_type_placeholder': 'Ví dụ: Lúa, ngô, cà phê...',
    'onboarding.preferences.livestock_type': 'Loại vật nuôi',
    'onboarding.preferences.livestock_type_placeholder': 'Ví dụ: Heo, gà, bò...',
    'onboarding.preferences.location': 'Bạn sống ở khu vực nào?',
    'onboarding.preferences.farm_scale': 'Quy mô canh tác',
    'onboarding.preferences.support_needs': 'Bạn muốn được hỗ trợ về mặt gì?',
    'onboarding.preferences.financial_knowledge': 'Mức độ hiểu biết về tài chính của bạn là gì?',
    'onboarding.preferences.continue': 'Tiếp tục',
    'onboarding.preferences.back': 'Quay lại',
    'onboarding.preferences.complete': 'Hoàn thành thiết lập',
    // Agricultural activities
    'preferences.agricultural_activities.crop_cultivation': 'Trồng trọt',
    'preferences.agricultural_activities.livestock': 'Chăn nuôi',
    'preferences.agricultural_activities.aquaculture': 'Thủy sản',
    'preferences.agricultural_activities.forestry': 'Lâm nghiệp',
    'preferences.agricultural_activities.organic_farming': 'Nông nghiệp hữu cơ',
    'preferences.agricultural_activities.food_processing': 'Chế biến nông sản',
    // Farm scales
    'preferences.farm_scales.small': '0 đến 10 hecta',
    'preferences.farm_scales.medium_small': '10 đến 25 hecta',
    'preferences.farm_scales.medium': '25 đến 50 hecta',
    'preferences.farm_scales.large': '50 đến 100 hecta',
    'preferences.farm_scales.very_large': '>100 hecta',
    // Support needs
    'preferences.support_needs.development_advice': 'Lời khuyên về kế hoạch phát triển cho canh tác',
    'preferences.support_needs.loan_advice': 'Lời khuyên về chọn khoản vay vốn',
    'preferences.support_needs.financial_education': 'Học kiến thức tài chính chung',
    'preferences.support_needs.financial_management': 'Lời khuyên về quản lí tài chính',
    'preferences.support_needs.market_trends': 'Cập nhật xu hướng thị trường và định hướng bán ra',
    // Financial knowledge levels
    'preferences.financial_knowledge.none': 'Tôi hoàn toàn không biết',
    'preferences.financial_knowledge.basic': 'Tôi biết một số dịch vụ tài chính nhưng chưa sử dụng bao giờ',
    'preferences.financial_knowledge.intermediate': 'Tôi biết và đã sử dụng dịch vụ tài chính',
    'preferences.financial_knowledge.advanced': 'Tôi biết sâu và đã sử dụng các dịch vụ tài chính thường xuyên',
    // User Preferences page specific translations
    'preferences.loading': 'Đang tải tùy chọn...',
    'preferences.error_loading': 'Không thể tải thông tin tùy chọn',
    'preferences.error_saving': 'Đã xảy ra lỗi khi cập nhật tùy chọn. Vui lòng thử lại.',
    'preferences.error_update_failed': 'Không thể cập nhật tùy chọn. Vui lòng thử lại.',
    'preferences.success_updated': 'Tùy chọn của bạn đã được cập nhật thành công!',
    'preferences.validation.agricultural_activity': 'Vui lòng chọn ít nhất một loại hoạt động nông nghiệp',
    'preferences.validation.location': 'Vui lòng chọn khu vực bạn đang sinh sống',
    'preferences.validation.farm_scale': 'Vui lòng chọn quy mô canh tác',
    'preferences.validation.support_needs': 'Vui lòng chọn ít nhất một loại hỗ trợ',
    'preferences.validation.financial_knowledge': 'Vui lòng chọn mức độ hiểu biết về tài chính',
    'preferences.location_placeholder': 'Chọn tỉnh/thành phố',
    'preferences.save_changes': 'Lưu thay đổi',
    'preferences.saving': 'Đang lưu...',
    // Agricultural activities
    'agricultural.crop_cultivation': 'Trồng trọt',
    'agricultural.livestock': 'Chăn nuôi',
    'agricultural.aquaculture': 'Thủy sản',
    'agricultural.forestry': 'Lâm nghiệp',
    'agricultural.organic_farming': 'Nông nghiệp hữu cơ',
    'agricultural.food_processing': 'Chế biến nông sản',
    // Farm scales
    'farm_scale.0_10_hectares': '0 đến 10 hecta',
    'farm_scale.10_25_hectares': '10 đến 25 hecta',
    'farm_scale.25_50_hectares': '25 đến 50 hecta',
    'farm_scale.50_100_hectares': '50 đến 100 hecta',
    'farm_scale.over_100_hectares': '>100 hecta',
    // Support needs
    'support.development_planning': 'Lời khuyên về kế hoạch phát triển cho canh tác',
    'support.loan_advice': 'Lời khuyên về chọn khoản vay vốn',
    'support.financial_education': 'Học kiến thức tài chính chung',
    'support.financial_management': 'Lời khuyên về quản lí tài chính',
    'support.market_trends': 'Cập nhật xu hướng thị trường và định hướng bán ra',
    // Financial knowledge levels
    'financial_knowledge.none': 'Tôi hoàn toàn không biết',
    'financial_knowledge.basic': 'Tôi biết một số dịch vụ tài chính nhưng chưa sử dụng bao giờ',
    'financial_knowledge.intermediate': 'Tôi biết và đã sử dụng dịch vụ tài chính',
    'financial_knowledge.advanced': 'Tôi biết sâu và đã sử dụng các dịch vụ tài chính thường xuyên'
  },
  en: {
    'welcome.title': 'Welcome to Financial Chatbot',
    'welcome.subtitle': 'Start a conversation or select a chat from the sidebar',
    'welcome.new_conversation': 'Start a New Conversation',
    'welcome.description': 'Ask me anything about financial planning, investments, or smallholders',
    'welcome.bullet1': '• Get personalized financial advice',
    'welcome.bullet2': '• Learn about investment strategies',
    'welcome.bullet3': '• Explore ASEAN financial markets',
    'header.title': 'Financial Chatbot',
    'header.subtitle': 'AI-powered financial assistant for smallholders',
    'chat.new_chat_title': 'New conversation',
    'profile.title': 'User Profile',
    'login.title': 'Login',
    'register.title': 'Register',
    'language.vietnamese': 'Tiếng Việt',
    'language.english': 'English',
    'sidebar.generated_files': 'Generated Files',
    'sidebar.chat_history': 'Chat History',
    'profile.profile': 'Profile',
    'profile.account': 'Account',
    'profile.preferences': 'Preferences',
    'profile.profile_info': 'Profile Information',
    'profile.full_name': 'Full Name',
    'profile.email_address': 'E-mail Address',
    'profile.change_avatar': 'Change Avatar',
    'profile.save_changes': 'Save Changes',
    'profile.change_password': 'Change Password',
    'profile.current_password': 'Current Password',
    'profile.new_password': 'New Password',
    'profile.confirm_password': 'Confirm Password',
    'profile.update_password': 'Update Password',
    'profile.notifications': 'Notifications',
    'profile.email_notifications': 'E-mail Notifications',
    'profile.notifications_desc': 'Receive updates about your chats and account',
    'profile.sign_out': 'Sign Out',
    'profile.save_preferences': 'Save Preferences',
    'profile.dont_have_account': 'Don\'t have an account? Sign up',
    'profile.already_have_account': 'Already have an account? Sign in',
    'profile.creating_account': 'Creating account...',
    'profile.sign_up': 'Sign up',
    'profile.signing_in': 'Signing in...',
    'profile.sign_in': 'Sign in',
    'common.or': 'or',
    'profile.account_settings': 'Account Settings',
    'profile.change_password_section': 'Change Password',
    'profile.account_deletion': 'Account Deletion',
    'profile.delete_account': 'Delete Account',
    'profile.delete_account_desc': 'Permanently delete your account and all associated data.',
    'profile.avatar_hint': 'JPG, GIF or PNG. Max size 1MB.',
    'date.today': 'Today',
    'date.yesterday': 'Yesterday',
    'api.error': 'An error occurred, please try again later.',
    'api.streaming_error': 'Sorry, I encountered an error. Please try again.',
    'api.connection_error': 'Sorry, I encountered an error while processing your message. Please try again.',
    'api.mock_error': 'An error occurred',
    'input.placeholder_normal': 'Type your message...',
    'input.placeholder_generating': 'AI is generating response...',
    'input.speech_not_supported': 'Speech recognition is not supported in your browser.',
    'input.send_message': 'Send message',
    'input.stop_generation': 'Stop generation',
    'input.recording': 'Recording...',
    'chat.typing': 'AI is responding...',
    'chat.ai_responding': 'AI is responding...',
    'history.loading': 'Loading conversation history...',
    'history.no_chats': 'No chats yet. Start a new conversation!',
    'history.all_chats_loaded': 'All conversations loaded',
    // Transcription translations
    'transcription.result_title': 'Transcription Result',
    'transcription.confidence': 'Confidence:',
    'transcription.transcribed_text': 'Transcribed Text:',
    'transcription.click_to_edit': 'Click to edit',
    'transcription.no_text': 'No transcription available',
    'transcription.cancel': 'Cancel',
    'transcription.confirm_send': 'Confirm & Send',
    'transcription.edit_help': 'You can edit the transcribed text before sending it to the chatbot',
    'transcription.processing': 'Processing',
    'transcription.listening': 'Listening...',
    'transcription.tap_to_stop': 'Tap to stop recording',
    'transcription.processing_audio': 'Processing audio',
    'transcription.stop': 'Stop',
    // Onboarding translations
    'onboarding.welcome.title': 'Welcome to PANSEA Financial Chatbot',
    'onboarding.welcome.subtitle': 'AI-powered financial assistant for Vietnamese farmers',
    'onboarding.welcome.feature1_title': 'Personalized Financial Advice',
    'onboarding.welcome.feature1_desc': 'Get financial guidance tailored to your agricultural situation',
    'onboarding.welcome.feature2_title': 'Development Planning Support',
    'onboarding.welcome.feature2_desc': 'Consulting on farming plans and sustainable development',
    'onboarding.welcome.feature3_title': 'Effective Financial Management',
    'onboarding.welcome.feature3_desc': 'Learn to manage finances and choose suitable loans',
    'onboarding.welcome.feature4_title': 'Market Updates',
    'onboarding.welcome.feature4_desc': 'Track market trends and sales guidance',
    'onboarding.welcome.get_started': 'Get Started',
    'onboarding.welcome.language_selection': 'Select Language',
    'onboarding.preferences.title': 'Personal Information Setup',
    'onboarding.preferences.subtitle': 'Tell us about your agricultural situation so we can provide the best support',
    'onboarding.preferences.agricultural_activity': 'Type of Agricultural Activity',
    'onboarding.preferences.crop_type': 'Crop Type',
    'onboarding.preferences.crop_type_placeholder': 'e.g., Rice, corn, coffee...',
    'onboarding.preferences.livestock_type': 'Livestock Type',
    'onboarding.preferences.livestock_type_placeholder': 'e.g., Pigs, chickens, cattle...',
    'onboarding.preferences.location': 'What region do you live in?',
    'onboarding.preferences.farm_scale': 'Farming Scale',
    'onboarding.preferences.support_needs': 'What kind of support do you need?',
    'onboarding.preferences.financial_knowledge': 'What is your level of financial knowledge?',
    'onboarding.preferences.continue': 'Continue',
    'onboarding.preferences.back': 'Back',
    'onboarding.preferences.complete': 'Complete Setup',
    // Agricultural activities
    'preferences.agricultural_activities.crop_cultivation': 'Crop Cultivation',
    'preferences.agricultural_activities.livestock': 'Livestock',
    'preferences.agricultural_activities.aquaculture': 'Aquaculture',
    'preferences.agricultural_activities.forestry': 'Forestry',
    'preferences.agricultural_activities.organic_farming': 'Organic Farming',
    'preferences.agricultural_activities.food_processing': 'Food Processing',
    // Farm scales
    'preferences.farm_scales.small': '0 to 10 hectares',
    'preferences.farm_scales.medium_small': '10 to 25 hectares',
    'preferences.farm_scales.medium': '25 to 50 hectares',
    'preferences.farm_scales.large': '50 to 100 hectares',
    'preferences.farm_scales.very_large': '>100 hectares',
    // Support needs
    'preferences.support_needs.development_advice': 'Advice on farming development plans',
    'preferences.support_needs.loan_advice': 'Advice on choosing loans',
    'preferences.support_needs.financial_education': 'Learn general financial knowledge',
    'preferences.support_needs.financial_management': 'Advice on financial management',
    'preferences.support_needs.market_trends': 'Market trend updates and sales guidance',
    // Financial knowledge levels
    'preferences.financial_knowledge.none': 'I know nothing at all',
    'preferences.financial_knowledge.basic': 'I know some financial services but have never used them',
    'preferences.financial_knowledge.intermediate': 'I know and have used financial services',
    'preferences.financial_knowledge.advanced': 'I know deeply and have used financial services regularly',
    // User Preferences page specific translations
    'preferences.loading': 'Loading preferences...',
    'preferences.error_loading': 'Unable to load preference information',
    'preferences.error_saving': 'An error occurred while updating preferences. Please try again.',
    'preferences.error_update_failed': 'Unable to update preferences. Please try again.',
    'preferences.success_updated': 'Your preferences have been updated successfully!',
    'preferences.validation.agricultural_activity': 'Please select at least one type of agricultural activity',
    'preferences.validation.location': 'Please select the region where you live',
    'preferences.validation.farm_scale': 'Please select your farming scale',
    'preferences.validation.support_needs': 'Please select at least one type of support',
    'preferences.validation.financial_knowledge': 'Please select your level of financial knowledge',
    'preferences.location_placeholder': 'Select province/city',
    'preferences.save_changes': 'Save Changes',
    'preferences.saving': 'Saving...',
    // Agricultural activities
    'agricultural.crop_cultivation': 'Crop Cultivation',
    'agricultural.livestock': 'Livestock',
    'agricultural.aquaculture': 'Aquaculture',
    'agricultural.forestry': 'Forestry',
    'agricultural.organic_farming': 'Organic Farming',
    'agricultural.food_processing': 'Food Processing',
    // Farm scales
    'farm_scale.0_10_hectares': '0 to 10 hectares',
    'farm_scale.10_25_hectares': '10 to 25 hectares',
    'farm_scale.25_50_hectares': '25 to 50 hectares',
    'farm_scale.50_100_hectares': '50 to 100 hectares',
    'farm_scale.over_100_hectares': '>100 hectares',
    // Support needs
    'support.development_planning': 'Advice on farming development planning',
    'support.loan_advice': 'Advice on choosing loans',
    'support.financial_education': 'General financial education',
    'support.financial_management': 'Financial management advice',
    'support.market_trends': 'Market trend updates and sales guidance',
    // Financial knowledge levels
    'financial_knowledge.none': 'I know nothing at all',
    'financial_knowledge.basic': 'I know some financial services but have never used them',
    'financial_knowledge.intermediate': 'I know and have used financial services',
    'financial_knowledge.advanced': 'I have deep knowledge and regularly use financial services'
  }
};

export const LanguageProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [language, setLanguage] = useState<Language>('vi');

  const t = (key: string, params?: Record<string, string>): string => {
    let message = translations[language][key as keyof typeof translations[typeof language]] || key;
    
    // Replace parameters in the message
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        message = message.replace(`{${key}}`, value);
      });
    }
    
    return message;
  };

  const formatDate = (date: Date, formatType: 'short' | 'long' | 'relative' = 'short'): string => {
    const locale = language === 'vi' ? vi : enUS;
    
    switch (formatType) {
      case 'long':
        return format(date, language === 'vi' ? 'EEEE, dd/MM/yyyy' : 'EEEE, MMMM d, yyyy', { locale });
      case 'relative':
        return formatDistanceToNow(date, { locale, addSuffix: true });
      default:
        return format(date, language === 'vi' ? 'dd/MM/yyyy' : 'MMMM d, yyyy', { locale });
    }
  };

  const formatTime = (date: Date): string => {
    const locale = language === 'vi' ? vi : enUS;
    return format(date, 'HH:mm', { locale });
  };

  return (
    <LanguageContext.Provider value={{
      language,
      setLanguage,
      t,
      formatDate,
      formatTime
    }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
