import React, { useState, useRef, useEffect } from 'react';
import { FileText, RefreshCw, AlertCircle } from 'lucide-react';
import { useHostnames } from '../hooks/useHostnames';
import { useBuildLog } from '../hooks/useBuildLog';
import HostnameSearch from '../components/HostnameSearch';

const BuildLogsPage: React.FC = () => {
  const { hostnames, isLoading: hostnamesLoading, error: hostnamesError, refetch } = useHostnames();
  const { log: logContent, isLoading: logLoading, error: logError, fetchLog } = useBuildLog();
  const [selectedHostname, setSelectedHostname] = useState<string | null>(null);
  const logContainerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!hostnamesLoading && hostnames.length > 0 && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [hostnamesLoading, hostnames.length]);

  // Auto-scroll to bottom when log content loads
  useEffect(() => {
    if (logContent && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logContent]);

  const handleHostnameSelect = (hostname: string) => {
    setSelectedHostname(hostname);
    fetchLog(hostname);
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
          disabled={hostnamesLoading}
          className="flex items-center space-x-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 text-white rounded-lg transition-colors text-sm"
        >
          <RefreshCw size={14} className={hostnamesLoading ? 'animate-spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {hostnamesLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-400"></div>
            <span className="text-gray-300 font-mono">Loading hostnames...</span>
          </div>
        </div>
      )}

      {hostnamesError && (
        <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertCircle size={16} className="text-yellow-400" />
            <div>
              <span className="text-yellow-400 font-mono text-sm font-semibold">
                Could not load hostname suggestions
              </span>
              <p className="text-yellow-300 text-xs mt-1">
                {hostnamesError}
              </p>
              <p className="text-gray-400 text-xs mt-2">
                You can still search by typing a hostname and clicking Search.
              </p>
            </div>
          </div>
        </div>
      )}

      {!hostnamesLoading && (
        <div className="space-y-6">
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-white font-mono mb-4">Search Build Logs</h2>
            <div className="max-w-md">
              <HostnameSearch
                ref={searchInputRef}
                hostnames={hostnames}
                onHostnameSelect={handleHostnameSelect}
                onManualSearch={handleHostnameSelect}
                isSearching={logLoading}
              />
            </div>
            <p className="text-gray-400 text-sm font-mono mt-2">
              {hostnames.length > 0
                ? `Search from ${hostnames.length.toLocaleString()} available hostnames`
                : 'Enter a hostname to search for build logs'}
            </p>
          </div>

          {logLoading && (
            <div className="flex items-center justify-center py-12">
              <div className="flex items-center space-x-3">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-400"></div>
                <span className="text-gray-300 font-mono">Loading log for {selectedHostname}...</span>
              </div>
            </div>
          )}

          {logError && (
            <div className="bg-orange-900/20 border border-orange-700 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <AlertCircle size={16} className="text-orange-400" />
                <div>
                  <span className="text-orange-400 font-mono text-sm font-semibold">
                    {logError.includes('not found') ? 'Build log not found' : 'Error loading build log'}
                  </span>
                  <p className="text-orange-300 text-sm mt-1">{logError}</p>
                  {logError.includes('not found') && (
                    <p className="text-gray-400 text-xs mt-2">
                      Make sure the hostname is correct and the build log exists.
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {logContent && !logLoading && (
            <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden flex flex-col">
              <div className="px-4 py-3 border-b border-gray-700 bg-gray-900">
                <p className="text-sm text-gray-400 font-mono">Log for: {selectedHostname}</p>
              </div>
              <div
                ref={logContainerRef}
                className="flex-1 overflow-y-auto max-h-96 p-4 bg-gray-900 font-mono text-sm"
              >
                <pre className="text-gray-300 whitespace-pre-wrap break-words">
                  {logContent}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default BuildLogsPage;