import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';
import { format, formatDistanceToNow } from 'date-fns';
import { vi, enUS } from 'date-fns/locale';

export type Language = 'vi' | 'en';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
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
    'profile.title': 'Hồ sơ người dùng',
    'login.title': 'Đăng nhập',
    'register.title': 'Đăng ký',
    'language.vietnamese': 'Tiếng Việt',
    'language.english': 'English',
    'profile.profile': 'Hồ sơ',
    'profile.account': 'Tài khoản',
    'profile.preferences': 'Tùy chọn',
    'profile.profile_info': 'Thông tin hồ sơ',
    'profile.full_name': 'Họ và tên',
    'profile.email_address': 'Địa chỉ email',
    'profile.change_avatar': 'Thay đổi ảnh đại diện',
    'profile.save_changes': 'Lưu thay đổi',
    'profile.change_password': 'Thay đổi mật khẩu',
    'profile.current_password': 'Mật khẩu hiện tại',
    'profile.new_password': 'Mật khẩu mới',
    'profile.confirm_password': 'Xác nhận mật khẩu',
    'profile.update_password': 'Cập nhật mật khẩu',
    'profile.notifications': 'Thông báo',
    'profile.email_notifications': 'Thông báo email',
    'profile.notifications_desc': 'Nhận cập nhật về chat và tài khoản của bạn',
    'profile.sign_out': 'Đăng xuất',
    'profile.save_preferences': 'Lưu tùy chọn',
    'profile.dont_have_account': 'Chưa có tài khoản? Đăng ký',
    'profile.already_have_account': 'Đã có tài khoản? Đăng nhập',
    'profile.creating_account': 'Đang tạo tài khoản...',
    'profile.sign_up': 'Đăng ký',
    'profile.signing_in': 'Đang đăng nhập...',
    'profile.sign_in': 'Đăng nhập',
  },
  en: {
    'welcome.title': 'Welcome to Financial Chatbot',
    'welcome.subtitle': 'Start a conversation or select a chat from the sidebar',
    'welcome.new_conversation': 'Start a New Conversation',
    'welcome.description': 'Ask me anything about financial planning, investments, or ASEAN markets',
    'welcome.bullet1': '• Get personalized financial advice',
    'welcome.bullet2': '• Learn about investment strategies',
    'welcome.bullet3': '• Explore ASEAN financial markets',
    'header.title': 'Financial Chatbot',
    'header.subtitle': 'AI-powered financial assistant for ASEAN markets',
    'profile.title': 'User Profile',
    'login.title': 'Login',
    'register.title': 'Register',
    'language.vietnamese': 'Tiếng Việt',
    'language.english': 'English',
    'profile.profile': 'Profile',
    'profile.account': 'Account',
    'profile.preferences': 'Preferences',
    'profile.profile_info': 'Profile Information',
    'profile.full_name': 'Full Name',
    'profile.email_address': 'Email Address',
    'profile.change_avatar': 'Change Avatar',
    'profile.save_changes': 'Save Changes',
    'profile.change_password': 'Change Password',
    'profile.current_password': 'Current Password',
    'profile.new_password': 'New Password',
    'profile.confirm_password': 'Confirm Password',
    'profile.update_password': 'Update Password',
    'profile.notifications': 'Notifications',
    'profile.email_notifications': 'Email Notifications',
    'profile.notifications_desc': 'Receive updates about your chats and account',
    'profile.sign_out': 'Sign Out',
    'profile.save_preferences': 'Save Preferences',
    'profile.dont_have_account': 'Don\'t have an account? Sign up',
    'profile.already_have_account': 'Already have an account? Sign in',
    'profile.creating_account': 'Creating account...',
    'profile.sign_up': 'Sign up',
    'profile.signing_in': 'Signing in...',
    'profile.sign_in': 'Sign in',
  }
};

export const LanguageProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [language, setLanguage] = useState<Language>('vi');

  const t = (key: string): string => {
    return translations[language][key as keyof typeof translations[typeof language]] || key;
  };

  const formatDate = (date: Date, formatType: 'short' | 'long' | 'relative' = 'short'): string => {
    const locale = language === 'vi' ? vi : enUS;
    
    switch (formatType) {
      case 'long':
        return format(date, 'EEEE, dd/MM/yyyy', { locale });
      case 'relative':
        return formatDistanceToNow(date, { locale, addSuffix: true });
      default:
        return format(date, 'dd/MM/yyyy', { locale });
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
