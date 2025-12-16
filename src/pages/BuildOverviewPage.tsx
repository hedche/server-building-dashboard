import React, { useState, useEffect } from 'react';
import { BarChart3, RefreshCw, AlertCircle } from 'lucide-react';
import { useBuildStatus } from '../hooks/useBuildStatus';
import { useRegionsConfig } from '../hooks/useRegionsConfig';
import RackVisualization from '../components/RackVisualization';

const BuildOverviewPage: React.FC = () => {
  const { regions, isLoading: regionsLoading, error: regionsError } = useRegionsConfig();
  const [selectedRegion, setSelectedRegion] = useState<string>('');
  const { buildStatus, isLoading, error, refetch } = useBuildStatus();

  // Set default region once regions are loaded
  useEffect(() => {
    if (regions.length > 0 && !selectedRegion) {
      setSelectedRegion(regions[0].code);
    }
  }, [regions, selectedRegion]);

  const currentRegionData = buildStatus ? buildStatus[selectedRegion.toLowerCase() as keyof typeof buildStatus] : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <BarChart3 size={24} className="text-green-400" />
          <h1 className="text-2xl font-bold text-white font-mono">Build Overview</h1>
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
                {region.code}
              </option>
            ))}
          </select>
        </div>
      </div>
      
      {(isLoading || regionsLoading) && (
        <div className="flex items-center justify-center py-12">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-400"></div>
            <span className="text-gray-300 font-mono">Loading build status...</span>
          </div>
        </div>
      )}

      {(error || regionsError) && (
        <div className="bg-red-900/20 border border-red-700 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertCircle size={16} className="text-red-400" />
            <span className="text-red-400 font-mono text-sm">Error: {error || regionsError}</span>
          </div>
        </div>
      )}

      {buildStatus && !isLoading && !regionsLoading && selectedRegion && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white font-mono">
              Region: {selectedRegion}
            </h2>
            <div className="text-sm text-gray-400 font-mono">
              {currentRegionData.length} servers installing
            </div>
          </div>
          
          <RackVisualization servers={currentRegionData} />
        </div>
      )}
      
      {buildStatus && !isLoading && !regionsLoading && selectedRegion && currentRegionData.length === 0 && (
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
          <p className="text-gray-400 font-mono">No servers currently installing in {selectedRegion}</p>
        </div>
      )}
    </div>
  );
};

export default BuildOverviewPage;