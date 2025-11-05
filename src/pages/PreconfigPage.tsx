import React from 'react';
import { Settings, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react';
import { usePreconfigs } from '../hooks/usePreconfigs';
import { usePushPreconfig } from '../hooks/usePushPreconfig';
import { usePushedPreconfigs } from '../hooks/usePushedPreconfigs';

const regions = [
  { name: 'CBG', depot: 1, label: 'Cambridge' },
  { name: 'DUB', depot: 2, label: 'Dublin' },
  { name: 'DAL', depot: 4, label: 'Dallas' },
];

const PreconfigPage: React.FC = () => {
  const { preconfigs, isLoading, error, refetch } = usePreconfigs();
  const { pushStatus, error: pushError, pushPreconfig } = usePushPreconfig();
  const { pushedPreconfigs, isLoading: pushedLoading, error: pushedError, refetch: refetchPushed } = usePushedPreconfigs();

  // Calculate statistics
  const totalPreconfigs = preconfigs.length;
  const regionStats = regions.map(region => ({
    ...region,
    count: preconfigs.filter(p => p.depot === region.depot).length
  }));

  const getRegionNameByDepot = (depot: number) => {
    const region = regions.find(r => r.depot === depot);
    return region ? region.label : 'Unknown';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Settings size={24} className="text-green-400" />
          <h1 className="text-2xl font-bold text-white font-mono">Preconfig</h1>
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
            <span className="text-gray-300 font-mono">Refreshing Preconfigs...</span>
          </div>
        </div>
      )}
      
      {(error || pushError || pushedError) && (
        <div className="bg-red-900/20 border border-red-700 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertCircle size={16} className="text-red-400" />
            <span className="text-red-400 font-mono text-sm">Error: {error || pushError || pushedError}</span>
          </div>
        </div>
      )}
      
      {!isLoading && (
        <div className="space-y-6">
          {/* Push Preconfig Section */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-white font-mono mb-4">Push Preconfig</h2>
            
            {/* Statistics */}
            <div className="mb-6 p-4 bg-gray-700 rounded-lg">
              <div className="text-sm text-gray-300 font-mono space-y-2">
                <div>Total preconfigs today: <span className="text-white font-semibold">{totalPreconfigs}</span></div>
                <div className="grid grid-cols-3 gap-4 mt-3">
                  {regionStats.map(region => (
                    <div key={region.name} className="text-center">
                      <div className="text-gray-400">{region.name} ({region.label})</div>
                      <div className="text-white font-semibold">{region.count}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            {/* Push Buttons or Loading */}
            {pushStatus === 'pushing' ? (
              <div className="flex items-center justify-center py-8">
                <div className="flex items-center space-x-3">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-green-400"></div>
                  <span className="text-gray-300 font-mono">
                    Pushing Preconfigs to {getRegionNameByDepot(
                      regions.find(r => pushStatus === 'pushing')?.depot || 1
                    )}
                  </span>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {regions.map(region => (
                  <button
                    key={region.name}
                    onClick={() => pushPreconfig(region.depot)}
                    disabled={pushStatus !== 'idle'}
                    className="flex flex-col items-center p-3 bg-green-600 hover:bg-green-700 disabled:bg-green-800 text-white rounded-lg transition-colors"
                  >
                    <span className="font-mono font-semibold text-sm">{region.name}</span>
                    <span className="text-xs opacity-90">{region.label}</span>
                    <span className="text-xs mt-0.5">Push Preconfig</span>
                  </button>
                ))}
              </div>
            )}
          </div>
          
          {/* Preconfigs List */}
          <div className="bg-gray-800 rounded-lg border border-gray-700">
            <div className="p-4 border-b border-gray-700">
              <h2 className="text-lg font-semibold text-white font-mono">Current Preconfigs</h2>
            </div>

            {preconfigs.length === 0 ? (
              <div className="p-8 text-center">
                <p className="text-gray-400 font-mono">No preconfigs available</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-700">
                    <tr>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">ID</th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">Region</th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">Depot</th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">Config</th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {preconfigs.map((preconfig) => (
                      <tr key={preconfig.id} className="border-t border-gray-700 hover:bg-gray-750">
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm">{preconfig.id}</td>
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm">
                          {getRegionNameByDepot(preconfig.depot)}
                        </td>
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm">{preconfig.depot}</td>
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm">
                          <code className="bg-gray-600 px-2 py-1 rounded text-xs">
                            {JSON.stringify(preconfig.config)}
                          </code>
                        </td>
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm">
                          {new Date(preconfig.created_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Pushed Preconfigs List */}
          <div className="bg-gray-800 rounded-lg border border-gray-700">
            <div className="p-4 border-b border-gray-700 flex items-center space-x-2">
              <CheckCircle size={18} className="text-green-400" />
              <h2 className="text-lg font-semibold text-white font-mono">Pushed Preconfigs</h2>
              <button
                onClick={() => refetchPushed()}
                disabled={pushedLoading}
                className="ml-auto px-2 py-1 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 text-white rounded transition-colors text-xs"
              >
                <RefreshCw size={12} className={`inline ${pushedLoading ? 'animate-spin' : ''}`} />
              </button>
            </div>

            {pushedLoading ? (
              <div className="p-8 flex items-center justify-center">
                <div className="flex items-center space-x-3">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-green-400"></div>
                  <span className="text-gray-300 font-mono text-sm">Loading pushed preconfigs...</span>
                </div>
              </div>
            ) : pushedPreconfigs.length === 0 ? (
              <div className="p-8 text-center">
                <p className="text-gray-400 font-mono">No pushed preconfigs</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-700">
                    <tr>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">ID</th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">Region</th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">Depot</th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">Config</th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">Pushed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pushedPreconfigs.map((preconfig) => (
                      <tr key={preconfig.id} className="border-t border-gray-700 hover:bg-gray-750">
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm">{preconfig.id}</td>
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm">
                          {getRegionNameByDepot(preconfig.depot)}
                        </td>
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm">{preconfig.depot}</td>
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm">
                          <code className="bg-gray-600 px-2 py-1 rounded text-xs">
                            {JSON.stringify(preconfig.config)}
                          </code>
                        </td>
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm">
                          {new Date(preconfig.pushed_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
      </div>
  );
};

export default PreconfigPage;