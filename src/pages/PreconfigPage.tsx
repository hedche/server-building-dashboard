import React, { useState, useMemo, useEffect } from 'react';
import { Settings, RefreshCw, AlertCircle, CheckCircle, Upload } from 'lucide-react';
import { usePreconfigs, Preconfig } from '../hooks/usePreconfigs';
import { usePushPreconfig } from '../hooks/usePushPreconfig';
import { usePushedPreconfigs } from '../hooks/usePushedPreconfigs';
import { usePreconfigConfig } from '../hooks/usePreconfigConfig';
import { useRegionsConfig } from '../hooks/useRegionsConfig';
import PreconfigModal from '../components/PreconfigModal';

const PreconfigPage: React.FC = () => {
  const { regions, getDepotForRegion, getRegionLabelForDepot, isLoading: regionsLoading, error: regionsError } = useRegionsConfig();
  const [selectedRegion, setSelectedRegion] = useState<string>('');
  const [selectedPreconfig, setSelectedPreconfig] = useState<Preconfig | null>(null);

  const { preconfigs, isLoading, error, refetch } = usePreconfigs(selectedRegion);
  const { pushStatus, error: pushError, pushPreconfig } = usePushPreconfig();
  const { pushedPreconfigs, isLoading: pushedLoading, error: pushedError, refetch: refetchPushed } = usePushedPreconfigs();
  const { applianceSizes, isLoading: configLoading, error: configError } = usePreconfigConfig();

  // Set default region once regions are loaded
  useEffect(() => {
    if (regions.length > 0 && !selectedRegion) {
      setSelectedRegion(regions[0].code);
    }
  }, [regions, selectedRegion]);

  // Calculate appliance size counts
  const applianceSizeCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    applianceSizes.forEach(size => {
      counts[size] = preconfigs.filter(p => p.appliance_size === size).length;
    });
    return counts;
  }, [preconfigs, applianceSizes]);

  const currentRegion = regions.find(r => r.code === selectedRegion);

  const handlePushPreconfig = () => {
    const depot = getDepotForRegion(selectedRegion);
    if (depot !== undefined) {
      pushPreconfig(depot);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Settings size={24} className="text-green-400" />
          <h1 className="text-2xl font-bold text-white font-mono">Preconfig</h1>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={refetch}
            disabled={isLoading}
            className="flex items-center space-x-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 text-white rounded-lg transition-colors text-sm"
          >
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>

          <select
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.target.value)}
            className="bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            {regions.map((region) => (
              <option key={region.code} value={region.code}>
                {region.code} - {region.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {(isLoading || configLoading || regionsLoading) && (
        <div className="flex items-center justify-center py-12">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-400"></div>
            <span className="text-gray-300 font-mono">Refreshing Preconfigs...</span>
          </div>
        </div>
      )}

      {(error || pushError || pushedError || configError || regionsError) && (
        <div className="bg-red-900/20 border border-red-700 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertCircle size={16} className="text-red-400" />
            <span className="text-red-400 font-mono text-sm">Error: {error || pushError || pushedError || configError || regionsError}</span>
          </div>
        </div>
      )}

      {!isLoading && !configLoading && !regionsLoading && selectedRegion && (
        <div className="space-y-6">
          {/* Appliance Size Overview */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">

            <div className={`grid gap-4 mb-6 ${
              applianceSizes.length <= 3 ? 'grid-cols-3' :
              applianceSizes.length === 4 ? 'grid-cols-4' :
              'grid-cols-5'
            }`}>
              {applianceSizes.map(size => (
                <div key={size} className="bg-gray-700 rounded-lg p-4 text-center">
                  <div className="text-gray-400 font-mono text-sm capitalize">{size}</div>
                  <div className="text-2xl font-bold text-white font-mono mt-1">
                    {applianceSizeCounts[size]}
                  </div>
                </div>
              ))}
            </div>

            {/* Push Preconfig Button */}
            {pushStatus === 'pushing' ? (
              <div className="flex items-center justify-center py-4">
                <div className="flex items-center space-x-3">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-green-400"></div>
                  <span className="text-gray-300 font-mono">
                    Pushing Preconfigs to {currentRegion?.label}...
                  </span>
                </div>
              </div>
            ) : (
              <div className="flex justify-center">
                <button
                  onClick={handlePushPreconfig}
                  disabled={pushStatus !== 'idle' || preconfigs.length === 0}
                  className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-800 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-mono"
                >
                  <Upload size={18} />
                  <span>Push Preconfig to {selectedRegion}</span>
                </button>
              </div>
            )}
          </div>

          {/* Preconfigs List */}
          <div className="bg-gray-800 rounded-lg border border-gray-700">
            <div className="p-4 border-b border-gray-700">
              <h2 className="text-lg font-semibold text-white font-mono">
                Current Preconfigs ({preconfigs.length})
              </h2>
            </div>

            {preconfigs.length === 0 ? (
              <div className="p-8 text-center">
                <p className="text-gray-400 font-mono">No preconfigs available for {selectedRegion}</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-700">
                    <tr>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">DBID</th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">Size</th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">Config</th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {preconfigs.map((preconfig) => (
                      <tr
                        key={preconfig.dbid}
                        className="border-t border-gray-700 hover:bg-gray-750 cursor-pointer transition-colors"
                        onClick={() => setSelectedPreconfig(preconfig)}
                      >
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm">{preconfig.dbid}</td>
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm capitalize">
                          {preconfig.appliance_size || '-'}
                        </td>
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
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">DBID</th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">Region</th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">Size</th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">Config</th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">Pushed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pushedPreconfigs.map((preconfig) => (
                      <tr key={preconfig.dbid} className="border-t border-gray-700 hover:bg-gray-750">
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm">{preconfig.dbid}</td>
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm">
                          {getRegionLabelForDepot(preconfig.depot)}
                        </td>
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm capitalize">
                          {preconfig.appliance_size || '-'}
                        </td>
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm">
                          <code className="bg-gray-600 px-2 py-1 rounded text-xs">
                            {JSON.stringify(preconfig.config)}
                          </code>
                        </td>
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm">
                          {preconfig.pushed_at ? new Date(preconfig.pushed_at).toLocaleString() : '-'}
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

      <PreconfigModal
        preconfig={selectedPreconfig}
        isOpen={!!selectedPreconfig}
        onClose={() => setSelectedPreconfig(null)}
      />
      </div>
  );
};

export default PreconfigPage;
