import React from 'react';
import { X, Server, HardDrive, Cpu, MemoryStick, Network, Clock, AlertCircle } from 'lucide-react';
import { useServerDetails } from '../hooks/useServerDetails';

interface ServerModalProps {
  hostname: string;
  isOpen: boolean;
  onClose: () => void;
}

const ServerModal: React.FC<ServerModalProps> = ({ hostname, isOpen, onClose }) => {
  const { serverDetails, isLoading, error, fetchServerDetails } = useServerDetails();

  React.useEffect(() => {
    if (isOpen && hostname) {
      fetchServerDetails(hostname);
    }
  }, [isOpen, hostname, fetchServerDetails]);

  // Handle click outside to close
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (isOpen && target.closest('.modal-content') === null) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'complete':
        return 'text-green-400';
      case 'failed':
        return 'text-red-400';
      case 'installing':
        return 'text-blue-400';
      default:
        return 'text-gray-400';
    }
  };

  const getProgressColor = (server: any) => {
    if (server?.status === 'failed') return 'bg-red-500';
    if (server?.percent_built === 100) return 'bg-green-500';
    return 'bg-blue-500';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="modal-content bg-gray-800 rounded-lg border border-gray-700 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <div className="flex items-center space-x-2">
            <Server size={20} className="text-green-400" />
            <h2 className="text-lg font-bold text-white font-mono">Server Details</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-700 rounded transition-colors"
          >
            <X size={20} className="text-gray-400" />
          </button>
        </div>

        <div className="p-4">
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <div className="flex items-center space-x-3">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-green-400"></div>
                <span className="text-gray-300 font-mono text-sm">Loading server details...</span>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-900/20 border border-red-700 rounded-lg p-4 mb-4">
              <div className="flex items-center space-x-2">
                <AlertCircle size={16} className="text-red-400" />
                <span className="text-red-400 font-mono text-sm">Error: {error}</span>
              </div>
            </div>
          )}

          {serverDetails && !isLoading && (
            <div className="space-y-6">
              {/* Basic Information */}
              <div className="bg-gray-700 rounded-lg p-4">
                <h3 className="text-white font-mono font-semibold mb-3 flex items-center">
                  <Server size={16} className="mr-2 text-green-400" />
                  Basic Information
                </h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-400">Hostname:</span>
                    <div className="text-white font-mono">{serverDetails.hostname}</div>
                  </div>
                  <div>
                    <span className="text-gray-400">DBID:</span>
                    <div className="text-white font-mono">{serverDetails.dbid}</div>
                  </div>
                  <div>
                    <span className="text-gray-400">S/N:</span>
                    <div className="text-white font-mono">{serverDetails.serial_number}</div>
                  </div>
                  <div>
                    <span className="text-gray-400">Rack ID:</span>
                    <div className="text-white font-mono">{serverDetails.rackID}</div>
                  </div>
                  <div>
                    <span className="text-gray-400">Type:</span>
                    <div className="text-white font-mono">{serverDetails.machine_type}</div>
                  </div>
                  <div>
                    <span className="text-gray-400">Status:</span>
                    <div className={`font-mono font-semibold ${getStatusColor(serverDetails.status)}`}>
                      {serverDetails.status}
                    </div>
                  </div>
                </div>
              </div>

              {/* Installation Progress */}
              <div className="bg-gray-700 rounded-lg p-4">
                <h3 className="text-white font-mono font-semibold mb-3">Installation Progress</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400 text-sm">Progress:</span>
                    <span className="text-white font-mono text-sm">{serverDetails.percent_built}%</span>
                  </div>
                  <div className="w-full bg-gray-600 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-300 ${getProgressColor(serverDetails)}`}
                      style={{ width: `${serverDetails.percent_built}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Hardware Specifications */}
              {(serverDetails.cpu_model || serverDetails.ram_gb || serverDetails.storage_gb) && (
                <div className="bg-gray-700 rounded-lg p-4">
                  <h3 className="text-white font-mono font-semibold mb-3 flex items-center">
                    <Cpu size={16} className="mr-2 text-green-400" />
                    Hardware Specifications
                  </h3>
                  <div className="grid grid-cols-1 gap-3 text-sm">
                    {serverDetails.cpu_model && (
                      <div className="flex items-center">
                        <Cpu size={14} className="mr-2 text-gray-400" />
                        <span className="text-gray-400 mr-2">CPU:</span>
                        <span className="text-white font-mono">{serverDetails.cpu_model}</span>
                      </div>
                    )}
                    {serverDetails.ram_gb && (
                      <div className="flex items-center">
                        <MemoryStick size={14} className="mr-2 text-gray-400" />
                        <span className="text-gray-400 mr-2">RAM:</span>
                        <span className="text-white font-mono">{serverDetails.ram_gb} GB</span>
                      </div>
                    )}
                    {serverDetails.storage_gb && (
                      <div className="flex items-center">
                        <HardDrive size={14} className="mr-2 text-gray-400" />
                        <span className="text-gray-400 mr-2">Storage:</span>
                        <span className="text-white font-mono">{serverDetails.storage_gb} GB</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Network Information */}
              {(serverDetails.ip_address || serverDetails.mac_address) && (
                <div className="bg-gray-700 rounded-lg p-4">
                  <h3 className="text-white font-mono font-semibold mb-3 flex items-center">
                    <Network size={16} className="mr-2 text-green-400" />
                    Network Information
                  </h3>
                  <div className="grid grid-cols-1 gap-3 text-sm">
                    {serverDetails.ip_address && (
                      <div>
                        <span className="text-gray-400">IP Address:</span>
                        <div className="text-white font-mono">{serverDetails.ip_address}</div>
                      </div>
                    )}
                    {serverDetails.mac_address && (
                      <div>
                        <span className="text-gray-400">MAC Address:</span>
                        <div className="text-white font-mono">{serverDetails.mac_address}</div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Timing Information */}
              {(serverDetails.install_start_time || serverDetails.estimated_completion || serverDetails.last_heartbeat) && (
                <div className="bg-gray-700 rounded-lg p-4">
                  <h3 className="text-white font-mono font-semibold mb-3 flex items-center">
                    <Clock size={16} className="mr-2 text-green-400" />
                    Timing Information
                  </h3>
                  <div className="grid grid-cols-1 gap-3 text-sm">
                    {serverDetails.install_start_time && (
                      <div>
                        <span className="text-gray-400">Install Started:</span>
                        <div className="text-white font-mono">{formatDateTime(serverDetails.install_start_time)}</div>
                      </div>
                    )}
                    {serverDetails.estimated_completion && (
                      <div>
                        <span className="text-gray-400">Estimated Completion:</span>
                        <div className="text-white font-mono">{formatDateTime(serverDetails.estimated_completion)}</div>
                      </div>
                    )}
                    {serverDetails.last_heartbeat && (
                      <div>
                        <span className="text-gray-400">Last Heartbeat:</span>
                        <div className="text-white font-mono">{formatDateTime(serverDetails.last_heartbeat)}</div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ServerModal;