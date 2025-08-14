import React, { useState } from 'react';
import { 
  ArrowLeftIcon,
  UserCircleIcon,
  EnvelopeIcon,
  KeyIcon,
  BellIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../../context/AuthContext';

interface ProfilePageProps {
  onBack: () => void;
}

export const ProfilePage: React.FC<ProfilePageProps> = ({ onBack }) => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [notifications, setNotifications] = useState(true);
  const [language, setLanguage] = useState('en');

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to log out?')) {
      logout();
    }
  };

  return (
    <div className="min-h-screen" 
    style={{
        background: `linear-gradient(135deg, #B4B4B2 0%, #FFFFFF 100%)`, // Fallback gradient
        // backgroundImage: `url('/login-background.svg')`,
        backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), url('/background3.jpg')`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundAttachment: 'fixed'
      }}>

      {/* Header - Floating on background */}
      <div className="relative">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center space-x-3">
              <button
                onClick={onBack}
                className="p-2 rounded-lg transition-colors backdrop-blur-sm"
                style={{ 
                  color: '#FFFFFF',
                  backgroundColor: 'rgba(33, 166, 145, 0.8)',
                  border: '1px solid rgba(135, 223, 44, 0.5)'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(33, 166, 145, 1)';
                  e.currentTarget.style.borderColor = '#87DF2C';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(33, 166, 145, 0.8)';
                  e.currentTarget.style.borderColor = 'rgba(135, 223, 44, 0.5)';
                }}
              >
                <ArrowLeftIcon className="h-5 w-5" />
              </button>
              <h1 className="text-2xl font-bold text-white drop-shadow-lg">Profile & Settings</h1>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar Navigation */}
          <div className="lg:w-64">
            <nav className="space-y-1">
              <button
                onClick={() => {
                  setActiveTab('profile')
                }}
                className="w-full flex items-center space-x-3 px-4 py-2 text-left rounded-lg transition-colors"
                style={{
                  backgroundColor: activeTab === 'profile' ? '#21A691' : 'transparent',
                  color: '#FFFFFF',
                }}
                onMouseEnter={(e) => {
                  if (activeTab !== 'profile') { 
                    e.currentTarget.style.backgroundColor = '#87DF2C';
                    e.currentTarget.style.color = '#000000';
                  }
                }}
                onMouseLeave={(e) => {
                  if (activeTab !== 'profile') {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = '#FFFFFF';
                  } else {
                    e.currentTarget.style.backgroundColor = '#21A691';
                    e.currentTarget.style.color = '#FFFFFF';
                  }
                }}
              >
                <UserCircleIcon className="h-5 w-5" />
                <span>Profile</span>
              </button>
              <button
                onClick={() => setActiveTab('account')}
                className="w-full flex items-center space-x-3 px-4 py-2 text-left rounded-lg transition-colors"
                style={{
                  backgroundColor: activeTab === 'account' ? '#21A691' : 'transparent',
                  color: '#FFFFFF',
                }}
                onMouseEnter={(e) => {
                  if (activeTab !== 'account') {
                    e.currentTarget.style.backgroundColor = '#87DF2C';
                    e.currentTarget.style.color = '#000000';
                  }
                }}
                onMouseLeave={(e) => {
                  if (activeTab !== 'account') {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = '#FFFFFF';
                  } else {
                    e.currentTarget.style.backgroundColor = '#21A691';
                    e.currentTarget.style.color = '#FFFFFF';
                  }
                }}
              >
                <KeyIcon className="h-5 w-5" />
                <span>Account</span>
              </button>
              <button
                onClick={() => setActiveTab('preferences')}
                className="w-full flex items-center space-x-3 px-4 py-2 text-left rounded-lg transition-colors"
                style={{
                  backgroundColor: activeTab === 'preferences' ? '#21A691' : 'transparent',
                  color: '#FFFFFF'
                }}
                onMouseEnter={(e) => {
                  if (activeTab !== 'preferences') {
                    e.currentTarget.style.backgroundColor = '#87DF2C';
                    e.currentTarget.style.color = '#000000';  
                  }
                }}
                onMouseLeave={(e) => {
                  if (activeTab !== 'preferences') {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = '#FFFFFF';
                  } else {
                    e.currentTarget.style.backgroundColor = '#21A691';
                    e.currentTarget.style.color = '#FFFFFF';
                  }
                }}
              >
                <BellIcon className="h-5 w-5" />
                <span>Preferences</span>
              </button>
            </nav>
          </div>

          {/* Main Content */}
          <div className="flex-1">
            {activeTab === 'profile' && (
              <div className="rounded-lg shadow p-6 border" style={{ backgroundColor: '#FFFFFF', borderColor: '#21A691' }}>
                <h2 className="text-lg font-semibold mb-6" style={{ color: '#27403E' }}>Profile Information</h2>
                
                <div className="space-y-6">
                  {/* Avatar */}
                  <div className="flex items-center space-x-6">
                    <div className="w-20 h-20 rounded-full flex items-center justify-center" 
                      style={{ backgroundColor: '#21A691' }}
                    >
                      <UserCircleIcon className="h-12 w-12" style={{ color: '#FFFFFF' }} />
                    </div>
                    <div>
                      <button className="px-4 py-2 text-sm rounded-lg transition-colors"
                      style={{ backgroundColor: '#21A691', color: '#ffffff' }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = '#87DF2C';
                        e.currentTarget.style.color = '#000000';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = '#21A691';
                        e.currentTarget.style.color = '#ffffff';
                      }}
                      >
                        Change Avatar
                      </button>
                      <p className="text-sm mt-1" style={{ color: '#B4B4B2' }}>JPG, GIF or PNG. Max size 1MB.</p>
                    </div>
                  </div>

                  {/* Name */}
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#27403E' }}>
                      Full Name
                    </label>
                    <input
                      type="text"
                      defaultValue={user?.name}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none transition-colors"
                      style={{
                        borderColor: '#21A691',
                        backgroundColor: '#FFFFFF',
                        color: '#27403E'
                      }}
                      onFocus={(e) => {
                        e.currentTarget.style.borderColor = '#87DF2C';
                        e.currentTarget.style.boxShadow = '0 0 0 2px rgba(135, 223, 44, 0.2)';
                      }}
                      onBlur={(e) => {
                        e.currentTarget.style.borderColor = '#21A691';
                        e.currentTarget.style.boxShadow = 'none';
                      }}
                    />
                  </div>

                  {/* Email */}
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#27403E' }}>
                      Email Address
                    </label>
                    <div className="relative">
                      <EnvelopeIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5" style={{ color: '#B4B4B2' }} />
                      <input
                        type="email"
                        defaultValue={user?.email}
                        className="w-full pl-10 pr-3 py-2 border rounded-lg focus:outline-none transition-colors"
                        style={{
                          borderColor: '#21A691',
                          backgroundColor: '#FFFFFF',
                          color: '#27403E'
                        }}
                        onFocus={(e) => {
                          e.currentTarget.style.borderColor = '#87DF2C';
                          e.currentTarget.style.boxShadow = '0 0 0 2px rgba(135, 223, 44, 0.2)';
                        }}
                        onBlur={(e) => {
                          e.currentTarget.style.borderColor = '#21A691';
                          e.currentTarget.style.boxShadow = 'none';
                        }}
                      />
                    </div>
                  </div>

                  <div className="flex justify-end">
                    <button className="px-4 py-2 rounded-lg transition-colors"
                      style={{ backgroundColor: '#21A691', color: '#ffffff' }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = '#87DF2C';
                        e.currentTarget.style.color = '#000000';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = '#21A691';
                        e.currentTarget.style.color = '#ffffff';
                      }}
                    >
                      Save Changes
                    </button>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'account' && (
              <div className="bg-white rounded-lg shadow p-6 border border-neutral-200">
                <h2 className="text-lg font-semibold text-dark-900 mb-6">Account Settings</h2>
                
                <div className="space-y-6">
                  {/* Change Password */}
                  <div>
                    <h3 className="text-md font-medium text-dark-900 mb-4">Change Password</h3>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-dark-700 mb-2">
                          Current Password
                        </label>
                        <input
                          type="password"
                          className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-dark-700 mb-2">
                          New Password
                        </label>
                        <input
                          type="password"
                          className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-dark-700 mb-2">
                          Confirm New Password
                        </label>
                        <input
                          type="password"
                          className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                        />
                      </div>
                      <button className="px-4 py-2 rounded-lg transition-colors"
                        style={{ backgroundColor: '#21A691', color: '#ffffff' }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = '#87DF2C';
                          e.currentTarget.style.color = '#000000';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = '#21A691';
                          e.currentTarget.style.color = '#ffffff';
                        }}
                      >
                        Update Password
                      </button>
                    </div>
                  </div>

                  <hr />

                  {/* Danger Zone */}
                  <div>
                    <h3 className="text-md font-medium text-red-600 mb-4">Account Deletion</h3>
                    <div className="border border-red-200 rounded-lg p-6 bg-red-50">
                      <div className="flex items-center justify-between gap-8">
                        <div className="flex-1 max-w-md">
                          <h4 className="text-sm font-medium text-dark-900">Delete Account</h4>
                          <p className="text-sm text-neutral-700 mt-1">Permanently delete your account and all associated data.</p>
                        </div>
                        <div className="flex-shrink-0">
                          <button className="px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 transition-colors whitespace-nowrap">
                            Delete Account
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'preferences' && (
              <div className="bg-white rounded-lg shadow p-6 border border-neutral-200">
                <h2 className="text-lg font-semibold text-dark-900 mb-6">Preferences</h2>
                
                <div className="space-y-6">
                  {/* Theme */}
                  {/* <div>
                    <label className="block text-sm font-medium text-dark-700 mb-3">
                      Theme
                    </label>
                    <div className="flex items-center space-x-4">
                      <button
                        onClick={() => setIsDarkMode(false)}
                        className={`flex items-center space-x-2 px-4 py-2 rounded-lg border transition-colors ${
                          !isDarkMode
                            ? 'border-primary-500 bg-primary-50 text-primary-700'
                            : 'border-neutral-300 hover:bg-neutral-50'
                        }`}
                      >
                        <SunIcon className="h-4 w-4" />
                        <span>Light</span>
                      </button>
                      <button
                        onClick={() => setIsDarkMode(true)}
                        className={`flex items-center space-x-2 px-4 py-2 rounded-lg border transition-colors ${
                          isDarkMode
                            ? 'border-primary-500 bg-primary-50 text-primary-700'
                            : 'border-neutral-300 hover:bg-neutral-50'
                        }`}
                      >
                        <MoonIcon className="h-4 w-4" />
                        <span>Dark</span>
                      </button>
                    </div>
                  </div> */}

                  {/* Language */}
                  <div>
                    <label className="block text-sm font-medium text-dark-700 mb-2">
                      Language
                    </label>
                    <div className="relative">
                      <GlobeAltIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-neutral-400" />
                      <select
                        value={language}
                        onChange={(e) => setLanguage(e.target.value)}
                        className="w-full pl-10 pr-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                      >
                        <option value="en">English</option>
                        <option value="id">Bahasa Indonesia</option>
                        <option value="ms">Bahasa Malaysia</option>
                        <option value="th">Thai</option>
                        <option value="vi">Vietnamese</option>
                        <option value="tl">Filipino</option>
                      </select>
                    </div>
                  </div>

                  {/* Notifications */}
                  <div>
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-dark-700">
                          Email Notifications
                        </label>
                        <p className="text-sm text-neutral-600">Receive updates about your chats and account</p>
                      </div>
                      <button
                        onClick={() => setNotifications(!notifications)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          notifications ? 'bg-primary-600' : 'bg-neutral-200'
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            notifications ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>
                  </div>

                  <div className="flex justify-between">
                    <button
                      onClick={handleLogout}
                      className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                    >
                      Sign Out
                    </button>
                    <button className="px-4 py-2 rounded-lg transition-colors"
                      style={{ backgroundColor: '#21A691', color: '#ffffff' }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = '#87DF2C';
                        e.currentTarget.style.color = '#000000';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = '#21A691';
                        e.currentTarget.style.color = '#ffffff';
                      }}
                    >
                      Save Preferences
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
