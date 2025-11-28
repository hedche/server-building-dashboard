import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Shield, ArrowRight, Code } from 'lucide-react';

const DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true';

const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [imageError, setImageError] = useState(false);

  // Logo customization via environment variables
  const LOGO_PATH = import.meta.env.VITE_LOGIN_LOGO_PATH?.trim();
  const LOGO_BG_COLOR = import.meta.env.VITE_LOGIN_LOGO_BG_COLOR || 'bg-green-600';

  const handleImageError = () => {
    console.error('Failed to load custom logo from public directory:', LOGO_PATH);
    setImageError(true);
  };

  const handleDevModeClick = () => {
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="max-w-md w-full space-y-8 p-8">
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div className={`w-20 h-20 ${LOGO_BG_COLOR} rounded-full flex items-center justify-center overflow-hidden`}>
              {LOGO_PATH && !imageError ? (
                <img
                  src={`/${LOGO_PATH}`}
                  alt="Logo"
                  onError={handleImageError}
                  className="w-full h-full object-cover"
                  loading="eager"
                />
              ) : (
                <Shield size={40} className="text-white" />
              )}
            </div>
          </div>
          <h2 className="text-3xl font-bold text-white font-mono">{import.meta.env.VITE_APP_NAME || 'Server Dashboard'}</h2>
          <p className="mt-2 text-gray-400 font-mono">
            Secure authentication required
          </p>
        </div>
        
        <div className="space-y-6">
          <button
            onClick={login}
            className="group relative w-full flex justify-center py-3 px-4 border border-transparent rounded-lg text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors font-medium text-sm"
          >
            <span className="absolute left-0 inset-y-0 flex items-center pl-3">
              <Shield size={16} />
            </span>
            <span className="flex items-center">
              Login with SAML
              <ArrowRight size={14} className="ml-2 group-hover:translate-x-1 transition-transform" />
            </span>
          </button>
        </div>
        
        {DEV_MODE && (
          <button
            onClick={handleDevModeClick}
            className="fixed bottom-4 right-4 flex items-center space-x-2 px-3 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg shadow-lg transition-colors font-mono text-sm"
            title="Development Mode Active - Skip Authentication"
          >
            <Code size={16} />
            <span>Dev Mode</span>
          </button>
        )}
      </div>
    </div>
  );
};

export default LoginPage;
