import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Shield, ArrowRight, Code } from 'lucide-react';

const DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true';

const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleDevModeClick = () => {
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="max-w-md w-full space-y-8 p-8">
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div className="p-4 bg-green-600 rounded-full">
              <Shield size={40} className="text-white" />
            </div>
          </div>
          <h2 className="text-3xl font-bold text-white font-mono">SAML Portal</h2>
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
          
          <div className="mt-4 text-center text-xs text-gray-500 font-mono">
            This application uses SAML2 authentication.<br />
            You will be redirected to your identity provider.
          </div>
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