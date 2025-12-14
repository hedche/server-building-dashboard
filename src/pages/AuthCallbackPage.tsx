import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const AuthCallbackPage: React.FC = () => {
  const navigate = useNavigate();
  const { checkAuth } = useAuth();

  useEffect(() => {
    let isMounted = true;

    const handleCallback = async () => {
      await checkAuth();
      if (isMounted) {
        navigate('/dashboard', { replace: true });
      }
    };

    handleCallback();

    return () => {
      isMounted = false;
    };
  }, [checkAuth, navigate]);

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="text-center space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-400 mx-auto"></div>
        <p className="text-white font-mono">Processing authentication...</p>
      </div>
    </div>
  );
};

export default AuthCallbackPage;