import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { LogOut, User } from 'lucide-react';

const TopBar: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <header className="bg-gray-800 border-b border-gray-700 px-4 py-3">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-green-400 font-mono">{import.meta.env.VITE_APP_NAME || 'Server Dashboard'}</h1>
        <div>
          {isAuthenticated && user ? (
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-1.5 text-gray-300">
                <User size={14} />
                <span className="font-mono text-xs">{user.email}</span>
              </div>
              <button
                onClick={logout}
                className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-white transition-colors font-medium text-xs"
              >
                <LogOut size={14} />
                <span>Logout</span>
              </button>
            </div>
          ) : (
            <div className="text-gray-400 font-mono text-xs">Not authenticated</div>
          )}
        </div>
      </div>
    </header>
  );
};

export default TopBar;