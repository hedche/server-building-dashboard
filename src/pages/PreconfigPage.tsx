import React, { useState, useMemo, useEffect } from 'react';
import { Settings, RefreshCw, AlertCircle, CheckCircle, Upload, ChevronUp, ChevronDown, Search, Check, X } from 'lucide-react';
import { usePreconfigs, Preconfig } from '../hooks/usePreconfigs';
import { usePushPreconfig, BuildServerPushResult } from '../hooks/usePushPreconfig';
import { usePushedPreconfigs } from '../hooks/usePushedPreconfigs';
import { useRegionsConfig } from '../hooks/useRegionsConfig';
import PreconfigModal from '../components/PreconfigModal';

type SortDirection = 'asc' | 'desc';
type CurrentSortKey = 'dbid' | 'appliance_size' | 'created_at';
type PushedSortKey = 'dbid' | 'appliance_size' | 'last_pushed_at';

const PreconfigPage: React.FC = () => {
  const { config, regions, getRegionLabelForDepot, applianceSizes, isLoading: regionsLoading, error: regionsError } = useRegionsConfig();
  const [selectedRegion, setSelectedRegion] = useState<string>('');
  const [selectedPreconfig, setSelectedPreconfig] = useState<Preconfig | null>(null);

  // Sorting state for Current Preconfigs table
  const [currentSortKey, setCurrentSortKey] = useState<CurrentSortKey>('created_at');
  const [currentSortDir, setCurrentSortDir] = useState<SortDirection>('desc');

  // Sorting state for Pushed Preconfigs table
  const [pushedSortKey, setPushedSortKey] = useState<PushedSortKey>('last_pushed_at');
  const [pushedSortDir, setPushedSortDir] = useState<SortDirection>('desc');

  // Search state for both tables
  const [currentSearch, setCurrentSearch] = useState('');
  const [pushedSearch, setPushedSearch] = useState('');

  // State for showing push cards
  const [showPushCards, setShowPushCards] = useState(false);

  const { preconfigs, isLoading, error, refetch } = usePreconfigs(selectedRegion);
  const {
    status: pushStatus,
    results: pushResults,
    error: pushError,
    pushPreconfig,
    reset: resetPush
  } = usePushPreconfig();
  const { pushedPreconfigs, isLoading: pushedLoading, error: pushedError, refetch: refetchPushed } = usePushedPreconfigs();

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

  // Get build servers for selected region from config
  const buildServersForRegion = useMemo(() => {
    if (!config || !selectedRegion) return [];
    const regionLower = selectedRegion.toLowerCase();
    const regionConfig = config.regions[regionLower];
    if (!regionConfig?.build_servers) return [];
    return Object.entries(regionConfig.build_servers).map(([hostname, serverConfig]) => ({
      hostname,
      preconfigs: serverConfig.preconfigs || []
    }));
  }, [config, selectedRegion]);

  // Filter and sort current preconfigs
  const sortedPreconfigs = useMemo(() => {
    const searchLower = currentSearch.toLowerCase();

    // Filter by search term
    const filtered = preconfigs.filter(p => {
      if (!searchLower) return true;
      return (
        p.dbid.toLowerCase().includes(searchLower) ||
        (p.appliance_size || '').toLowerCase().includes(searchLower) ||
        JSON.stringify(p.config).toLowerCase().includes(searchLower)
      );
    });

    // Sort filtered results
    return filtered.sort((a, b) => {
      let aVal: string | number | null = null;
      let bVal: string | number | null = null;

      switch (currentSortKey) {
        case 'dbid':
          aVal = a.dbid;
          bVal = b.dbid;
          break;
        case 'appliance_size':
          aVal = a.appliance_size || '';
          bVal = b.appliance_size || '';
          break;
        case 'created_at':
          aVal = a.created_at;
          bVal = b.created_at;
          break;
      }

      if (aVal === null || bVal === null) return 0;
      if (aVal < bVal) return currentSortDir === 'asc' ? -1 : 1;
      if (aVal > bVal) return currentSortDir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [preconfigs, currentSortKey, currentSortDir, currentSearch]);

  // Filter and sort pushed preconfigs
  const sortedPushedPreconfigs = useMemo(() => {
    const searchLower = pushedSearch.toLowerCase();

    // Filter by search term
    const filtered = pushedPreconfigs.filter(p => {
      if (!searchLower) return true;
      const pushedToStr = (p.pushed_to || []).join(' ');
      return (
        p.dbid.toLowerCase().includes(searchLower) ||
        pushedToStr.toLowerCase().includes(searchLower) ||
        (p.appliance_size || '').toLowerCase().includes(searchLower) ||
        JSON.stringify(p.config).toLowerCase().includes(searchLower)
      );
    });

    // Sort filtered results
    return filtered.sort((a, b) => {
      let aVal: string | number | null = null;
      let bVal: string | number | null = null;

      switch (pushedSortKey) {
        case 'dbid':
          aVal = a.dbid;
          bVal = b.dbid;
          break;
        case 'appliance_size':
          aVal = a.appliance_size || '';
          bVal = b.appliance_size || '';
          break;
        case 'last_pushed_at':
          aVal = a.last_pushed_at || '';
          bVal = b.last_pushed_at || '';
          break;
      }

      if (aVal === null || bVal === null) return 0;
      if (aVal < bVal) return pushedSortDir === 'asc' ? -1 : 1;
      if (aVal > bVal) return pushedSortDir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [pushedPreconfigs, pushedSortKey, pushedSortDir, pushedSearch]);

  // Handle sort for current preconfigs table
  const handleCurrentSort = (key: CurrentSortKey) => {
    if (currentSortKey === key) {
      setCurrentSortDir(currentSortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setCurrentSortKey(key);
      setCurrentSortDir('asc');
    }
  };

  // Handle sort for pushed preconfigs table
  const handlePushedSort = (key: PushedSortKey) => {
    if (pushedSortKey === key) {
      setPushedSortDir(pushedSortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setPushedSortKey(key);
      setPushedSortDir('asc');
    }
  };

  // Render sort indicator
  const SortIndicator = ({ active, direction }: { active: boolean; direction: SortDirection }) => {
    if (!active) return <ChevronUp size={14} className="opacity-0 group-hover:opacity-30" />;
    return direction === 'asc'
      ? <ChevronUp size={14} className="text-green-400" />
      : <ChevronDown size={14} className="text-green-400" />;
  };

  const handlePushPreconfig = async () => {
    if (selectedRegion && buildServersForRegion.length > 0) {
      setShowPushCards(true);
      const buildServerHostnames = buildServersForRegion.map(bs => bs.hostname);
      await pushPreconfig(selectedRegion, buildServerHostnames);
      // Refetch pushed preconfigs after push completes
      refetchPushed();
    }
  };

  const handleResetPush = () => {
    resetPush();
    setShowPushCards(false);
  };

  // Get the result for a specific build server
  const getResultForServer = (hostname: string): BuildServerPushResult | undefined => {
    return pushResults.find(r => r.build_server === hostname);
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

      {(isLoading || regionsLoading) && (
        <div className="flex items-center justify-center py-12">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-400"></div>
            <span className="text-gray-300 font-mono">Refreshing Preconfigs...</span>
          </div>
        </div>
      )}

      {(error || pushError || pushedError || regionsError) && (
        <div className="bg-red-900/20 border border-red-700 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertCircle size={16} className="text-red-400" />
            <span className="text-red-400 font-mono text-sm">Error: {error || pushError || pushedError || regionsError}</span>
          </div>
        </div>
      )}

      {!isLoading && !regionsLoading && selectedRegion && (
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

            {/* Push Preconfig Section */}
            {showPushCards ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-white font-mono text-sm">
                    {pushStatus === 'pushing' ? 'Pushing to' : 'Pushed to'} {buildServersForRegion.length} build server(s)
                  </h3>
                  {pushStatus === 'complete' && (
                    <button
                      onClick={handleResetPush}
                      className="flex items-center space-x-2 px-3 py-1 bg-gray-600 hover:bg-gray-500 text-white rounded transition-colors text-sm"
                    >
                      <RefreshCw size={14} />
                      <span>Reset</span>
                    </button>
                  )}
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {buildServersForRegion.map(bs => {
                    const result = getResultForServer(bs.hostname);
                    const isPushing = pushStatus === 'pushing' && !result;

                    return (
                      <div
                        key={bs.hostname}
                        className={`
                          flex flex-col px-4 py-3 rounded-lg border transition-all duration-300 ease-in-out
                          ${result?.status === 'success'
                            ? 'bg-green-900/20 border-green-700'
                            : result?.status === 'failed'
                              ? 'bg-red-900/20 border-red-700'
                              : result?.status === 'skipped'
                                ? 'bg-yellow-900/20 border-yellow-700'
                                : 'bg-gray-700 border-gray-600'}
                        `}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-sm text-gray-300">{bs.hostname}</span>
                          <div className="w-6 h-6 flex items-center justify-center">
                            {isPushing ? (
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-400" />
                            ) : result?.status === 'success' ? (
                              <Check size={16} className="text-green-400" />
                            ) : result?.status === 'failed' ? (
                              <X size={16} className="text-red-400" />
                            ) : result?.status === 'skipped' ? (
                              <span className="text-yellow-400 text-xs">-</span>
                            ) : null}
                          </div>
                        </div>
                        {bs.preconfigs.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {bs.preconfigs.map(size => (
                              <span key={size} className="bg-gray-600 px-2 py-0.5 rounded text-xs text-gray-300 capitalize">
                                {size}
                              </span>
                            ))}
                          </div>
                        )}
                        {result?.error && (
                          <p className="text-xs text-red-400 mt-2">{result.error}</p>
                        )}
                        {result?.status === 'success' && result.preconfig_count > 0 && (
                          <p className="text-xs text-green-400 mt-2">
                            {result.preconfig_count} preconfig(s) pushed
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="flex justify-center">
                <button
                  onClick={handlePushPreconfig}
                  disabled={preconfigs.length === 0 || buildServersForRegion.length === 0}
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
            <div className="p-4 border-b border-gray-700 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white font-mono">
                Current Preconfigs ({sortedPreconfigs.length}{currentSearch && ` / ${preconfigs.length}`})
              </h2>
              <div className="relative">
                <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  value={currentSearch}
                  onChange={(e) => setCurrentSearch(e.target.value)}
                  placeholder="Search..."
                  className="bg-gray-700 border border-gray-600 text-white rounded px-3 py-1 pl-7 text-sm w-48 focus:outline-none focus:ring-1 focus:ring-green-500 placeholder-gray-500"
                />
              </div>
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
                      <th
                        className="px-4 py-3 text-left text-white font-mono text-sm cursor-pointer hover:bg-gray-600 transition-colors group"
                        onClick={() => handleCurrentSort('dbid')}
                      >
                        <div className="flex items-center gap-1">
                          DBID
                          <SortIndicator active={currentSortKey === 'dbid'} direction={currentSortDir} />
                        </div>
                      </th>
                      <th
                        className="px-4 py-3 text-left text-white font-mono text-sm cursor-pointer hover:bg-gray-600 transition-colors group"
                        onClick={() => handleCurrentSort('appliance_size')}
                      >
                        <div className="flex items-center gap-1">
                          Size
                          <SortIndicator active={currentSortKey === 'appliance_size'} direction={currentSortDir} />
                        </div>
                      </th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">Config</th>
                      <th
                        className="px-4 py-3 text-left text-white font-mono text-sm cursor-pointer hover:bg-gray-600 transition-colors group"
                        onClick={() => handleCurrentSort('created_at')}
                      >
                        <div className="flex items-center gap-1">
                          Created
                          <SortIndicator active={currentSortKey === 'created_at'} direction={currentSortDir} />
                        </div>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedPreconfigs.map((preconfig) => (
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
            <div className="p-4 border-b border-gray-700 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CheckCircle size={18} className="text-green-400" />
                <h2 className="text-lg font-semibold text-white font-mono">
                  Pushed Preconfigs ({sortedPushedPreconfigs.length}{pushedSearch && ` / ${pushedPreconfigs.length}`})
                </h2>
                <button
                  onClick={() => refetchPushed()}
                  disabled={pushedLoading}
                  className="px-2 py-1 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 text-white rounded transition-colors text-xs"
                >
                  <RefreshCw size={12} className={`inline ${pushedLoading ? 'animate-spin' : ''}`} />
                </button>
              </div>
              <div className="relative">
                <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  value={pushedSearch}
                  onChange={(e) => setPushedSearch(e.target.value)}
                  placeholder="Search..."
                  className="bg-gray-700 border border-gray-600 text-white rounded px-3 py-1 pl-7 text-sm w-48 focus:outline-none focus:ring-1 focus:ring-green-500 placeholder-gray-500"
                />
              </div>
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
                      <th
                        className="px-4 py-3 text-left text-white font-mono text-sm cursor-pointer hover:bg-gray-600 transition-colors group"
                        onClick={() => handlePushedSort('dbid')}
                      >
                        <div className="flex items-center gap-1">
                          DBID
                          <SortIndicator active={pushedSortKey === 'dbid'} direction={pushedSortDir} />
                        </div>
                      </th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">
                        Build Servers
                      </th>
                      <th
                        className="px-4 py-3 text-left text-white font-mono text-sm cursor-pointer hover:bg-gray-600 transition-colors group"
                        onClick={() => handlePushedSort('appliance_size')}
                      >
                        <div className="flex items-center gap-1">
                          Size
                          <SortIndicator active={pushedSortKey === 'appliance_size'} direction={pushedSortDir} />
                        </div>
                      </th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">Config</th>
                      <th
                        className="px-4 py-3 text-left text-white font-mono text-sm cursor-pointer hover:bg-gray-600 transition-colors group"
                        onClick={() => handlePushedSort('last_pushed_at')}
                      >
                        <div className="flex items-center gap-1">
                          Pushed
                          <SortIndicator active={pushedSortKey === 'last_pushed_at'} direction={pushedSortDir} />
                        </div>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedPushedPreconfigs.map((preconfig) => (
                      <tr
                        key={preconfig.dbid}
                        className="border-t border-gray-700 hover:bg-gray-750 cursor-pointer transition-colors"
                        onClick={() => setSelectedPreconfig(preconfig)}
                      >
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm">{preconfig.dbid}</td>
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm">
                          <div className="flex flex-wrap gap-1">
                            {(preconfig.pushed_to || []).length > 0 ? (
                              preconfig.pushed_to!.map(bs => (
                                <span key={bs} className="bg-gray-600 px-2 py-0.5 rounded text-xs">
                                  {bs}
                                </span>
                              ))
                            ) : (
                              '-'
                            )}
                          </div>
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
                          {preconfig.last_pushed_at ? new Date(preconfig.last_pushed_at).toLocaleString() : '-'}
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
        regionLabel={selectedPreconfig?.last_pushed_at ? getRegionLabelForDepot(selectedPreconfig.depot) : undefined}
      />
      </div>
  );
};

export default PreconfigPage;
