import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import LanguageSelector from '../common/LanguageSelector';

interface LoginFormProps {
  onSuccess: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const { t } = useLanguage();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const success = await login(email, password);
      if (success) {
        onSuccess();
      } else {
        setError('Invalid email or password. Try admin123@gmail.com / admin123');
      }
    } catch (err) {
      setError('An error occurred during login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative"
      style={{
        background: `linear-gradient(135deg, #B4B4B2 0%, #FFFFFF 100%)`, // Fallback gradient
        // backgroundImage: `url('/login-background.svg')`,
        backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), url('/background3.jpg')`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundAttachment: 'fixed'
      }}
    >
      <div className="max-w-md w-full space-y-8">
        {/* Language Selector */}
        <div className="flex justify-end">
          <LanguageSelector />
        </div>
        
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold" style={{ color: '#ffffff' }}>
            {t('login.title')}
          </h2>
          <p className="mt-2 text-center text-sm" style={{ color: '#ffffff' }}>
            {t('header.subtitle')}
          </p>
          {/* <div className="mt-4 p-4 rounded-md" 
            style={{ 
              backgroundColor: '#21A691'
            }}
          >
            <p className="text-sm" style={{ color: '#FFFFFF' }}>
              <strong>Demo Account:</strong><br />
              Email: admin123@gmail.com<br />
              Password: admin123
            </p>
          </div> */}
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email-address" className="sr-only">
                Email address
              </label>
              <input
                id="email-address"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border rounded-t-md focus:outline-none focus:z-10 sm:text-sm"
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
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border rounded-b-md focus:outline-none focus:z-10 sm:text-sm"
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
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          {error && (
            <div className="rounded-md p-4 border" 
              style={{
                backgroundColor: '#FFE5E5',
                borderColor: '#FF0000'
              }}
            >
              <div className="text-sm" style={{ color: '#FF0000' }}>{error}</div>
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 transition-colors"
              style={{
                backgroundColor: '#21A691',
                color: '#ffffff'
              }}
              onMouseEnter={(e) => {
                if (!e.currentTarget.disabled) {
                  e.currentTarget.style.backgroundColor = '#7BC628';
                  e.currentTarget.style.color = '#000000';
                }
              }}
              onMouseLeave={(e) => {
                if (!e.currentTarget.disabled) {
                  e.currentTarget.style.backgroundColor = '#21A691';
                  e.currentTarget.style.color = '#ffffff';
                }
              }}
              onFocus={(e) => {
                e.currentTarget.style.boxShadow = '0 0 0 2px rgba(135, 223, 44, 0.3)';
              }}
              onBlur={(e) => {
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              {loading ? t('profile.signing_in') : t('profile.sign_in')}
            </button>
          </div>

          <div className="text-center">
            <Link
              to="/register"
              className="font-medium transition-colors"
              style={{ color: '#ffffff' }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = '#87DF2C';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = '#ffffff';
              }}
            >
              {t('profile.dont_have_account')}
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};
