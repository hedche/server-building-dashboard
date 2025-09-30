import React from 'react';
import { Settings } from 'lucide-react';

const PreconfigPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-2.5">
        <Settings size={24} className="text-green-400" />
        <h1 className="text-2xl font-bold text-white font-mono">Preconfig</h1>
      </div>
      
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
        <p className="text-gray-300 font-mono text-sm">Preconfig content will be implemented here.</p>
      </div>
    </div>
  );
};

export default PreconfigPage;