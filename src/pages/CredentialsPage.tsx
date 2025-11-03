import React from 'react';
import { Key } from 'lucide-react';

const CredentialsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-3">
        <Key size={24} className="text-green-400" />
        <h1 className="text-2xl font-bold text-white font-mono">Credentials</h1>
      </div>
      
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
        <p className="text-gray-400 font-mono text-lg">Coming soon...</p>
      </div>
    </div>
  );
};

export default CredentialsPage;