import React, { useState, useRef, useEffect } from 'react';
import { FileText, RefreshCw, AlertCircle } from 'lucide-react';
import { useHostnames } from '../hooks/useHostnames';
import HostnameSearch from '../components/HostnameSearch';

const BuildLogsPage: React.FC = () => {
  const { hostnames, isLoading: hostnamesLoading, error: hostnamesError, refetch } = useHostnames();
  const [selectedHostname, setSelectedHostname] = useState<string | null>(null);
  const [logContent, setLogContent] = useState<string>('');
  const [logLoading, setLogLoading] = useState(false);
  const [logError, setLogError] = useState<string | null>(null);
  const logContainerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!hostnamesLoading && hostnames.length > 0 && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [hostnamesLoading, hostnames.length]);

  const generateMockLog = (): string => {
    const lines: string[] = [];
    const now = new Date();

    for (let i = 0; i < 200; i++) {
      const timestamp = new Date(now.getTime() - (200 - i) * 1000).toISOString();
      const logTypes = ['INFO', 'DEBUG', 'WARN', 'ERROR', 'SUCCESS'];
      const logType = logTypes[Math.floor(Math.random() * logTypes.length)];
      const messages = [
        'Compiling source files',
        'Running tests',
        'Building artifacts',
        'Deploying to servers',
        'Health check passed',
        'Optimization complete',
        'Cache invalidated',
        'Dependencies resolved',
        'Docker image built',
        'Pushing to registry',
      ];
      const message = messages[Math.floor(Math.random() * messages.length)];

      lines.push(`[${timestamp}] [${logType}] ${message}`);
    }

    return lines.join('\n');
  };

  const fetchBuildLog = async (hostname: string) => {
    setLogLoading(true);
    setLogError(null);
    setLogContent('');

    try {
      let log: string;

      if (import.meta.env.DEV) {
        log = generateMockLog();
      } else {
        const response = await fetch(`/build-log/${hostname}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch log: ${response.statusText}`);
        }
        log = await response.text();
      }

      setLogContent(log);
      setTimeout(() => {
        if (logContainerRef.current) {
          logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
        }
      }, 0);
    } catch (err) {
      setLogError(err instanceof Error ? err.message : 'Failed to fetch log');
    } finally {
      setLogLoading(false);
    }
  };

  const handleHostnameSelect = (hostname: string) => {
    setSelectedHostname(hostname);
    fetchBuildLog(hostname);
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
        <div className="bg-red-900/20 border border-red-700 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertCircle size={16} className="text-red-400" />
            <span className="text-red-400 font-mono text-sm">Error: {hostnamesError}</span>
          </div>
        </div>
      )}

      {!hostnamesLoading && !hostnamesError && hostnames.length > 0 && (
        <div className="space-y-6">
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-white font-mono mb-4">Search Build Logs</h2>
            <div className="max-w-md">
              <HostnameSearch
                ref={searchInputRef}
                hostnames={hostnames}
                onHostnameSelect={handleHostnameSelect}
              />
            </div>
            <p className="text-gray-400 text-sm font-mono mt-2">
              Search from {hostnames.length.toLocaleString()} available hostnames
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
            <div className="bg-red-900/20 border border-red-700 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <AlertCircle size={16} className="text-red-400" />
                <span className="text-red-400 font-mono text-sm">Error: {logError}</span>
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