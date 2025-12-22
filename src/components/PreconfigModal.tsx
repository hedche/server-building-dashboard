import React from 'react';
import { X, Settings } from 'lucide-react';
import { Preconfig } from '../hooks/usePreconfigs';

interface PreconfigModalProps {
  preconfig: Preconfig | null;
  isOpen: boolean;
  onClose: () => void;
  regionLabel?: string;
}

const PreconfigModal: React.FC<PreconfigModalProps> = ({ preconfig, isOpen, onClose, regionLabel }) => {
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

  if (!isOpen || !preconfig) return null;

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="modal-content bg-gray-800 rounded-lg border border-gray-700 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <div className="flex items-center space-x-2">
            <Settings size={20} className="text-green-400" />
            <h2 className="text-lg font-bold text-white font-mono">Preconfig Details</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-700 rounded transition-colors"
          >
            <X size={20} className="text-gray-400" />
          </button>
        </div>

        <div className="p-4 space-y-6">
          {/* Basic Information */}
          <div className="bg-gray-700 rounded-lg p-4">
            <h3 className="text-white font-mono font-semibold mb-3 flex items-center">
              <Settings size={16} className="mr-2 text-green-400" />
              Basic Information
            </h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-400">DBID:</span>
                <div className="text-white font-mono">{preconfig.dbid}</div>
              </div>
              <div>
                <span className="text-gray-400">Size:</span>
                <div className="text-white font-mono capitalize">{preconfig.appliance_size || '-'}</div>
              </div>
              {regionLabel && (
                <div>
                  <span className="text-gray-400">Region:</span>
                  <div className="text-white font-mono">{regionLabel}</div>
                </div>
              )}
              <div>
                <span className="text-gray-400">Created:</span>
                <div className="text-white font-mono text-sm">{formatDateTime(preconfig.created_at)}</div>
              </div>
              {preconfig.pushed_at && (
                <div className="col-span-2">
                  <span className="text-gray-400">Pushed:</span>
                  <div className="text-white font-mono text-sm">{formatDateTime(preconfig.pushed_at)}</div>
                </div>
              )}
            </div>
          </div>

          {/* Configuration */}
          <div className="bg-gray-700 rounded-lg p-4">
            <h3 className="text-white font-mono font-semibold mb-3">Configuration</h3>
            <div className="bg-gray-600 rounded p-3 overflow-x-auto">
              <pre className="text-gray-200 font-mono text-xs whitespace-pre-wrap break-words">
                {JSON.stringify(preconfig.config, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PreconfigModal;
