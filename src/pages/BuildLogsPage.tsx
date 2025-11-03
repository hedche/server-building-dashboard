import React from 'react';
import { FileText, RefreshCw, AlertCircle } from 'lucide-react';
import { useHostnames } from '../hooks/useHostnames';
import HostnameSearch from '../components/HostnameSearch';

const BuildLogsPage: React.FC = () => {
  const { hostnames, isLoading, error, refetch } = useHostnames();

  const handleHostnameSelect = (hostname: string) => {
    console.log('Selected hostname:', hostname);
    // TODO: Implement log fetching for selected hostname
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <FileText size={24} className="text-green-400" />
          <h1 className="text-2xl font-bold text-white font-mono">Build Logs</h1>
        </div>
        
        <button
          onClick={refetch}
          disabled={isLoading}
          className="flex items-center space-x-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 text-white rounded-lg transition-colors text-sm"
        >
          <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>
      
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-400"></div>
            <span className="text-gray-300 font-mono">Loading hostnames...</span>
          </div>
        </div>
      )}
      
      {error && (
        <div className="bg-red-900/20 border border-red-700 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertCircle size={16} className="text-red-400" />
            <span className="text-red-400 font-mono text-sm">Error: {error}</span>
          </div>
        </div>
      )}
      
      {!isLoading && !error && hostnames.length > 0 && (
        <div className="space-y-6">
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-white font-mono mb-4">Search Build Logs</h2>
            <div className="max-w-md">
              <HostnameSearch 
                hostnames={hostnames} 
                onHostnameSelect={handleHostnameSelect}
              />
            </div>
            <p className="text-gray-400 text-sm font-mono mt-2">
              Search from {hostnames.length.toLocaleString()} available hostnames
            </p>
          </div>
          
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
            <p className="text-gray-400 font-mono">Select a hostname to view build logs</p>
          </div>
        </div>
      )}
      </div>
    </div>
  );
};

export default BuildLogsPage;