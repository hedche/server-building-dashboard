import React, { useState, useMemo, useEffect } from 'react';
import { UserCheck, RefreshCw, AlertCircle, ChevronUp, ChevronDown, Check, X } from 'lucide-react';
import { useBuildHistory } from '../hooks/useBuildHistory';
import { useAssignServers, AssignmentStatus } from '../hooks/useAssignServers';
import { useRegionsConfig } from '../hooks/useRegionsConfig';

type SortField = 'rackID' | 'hostname' | 'dbid' | 'serial_number';
type SortDirection = 'asc' | 'desc';

const AssignPage: React.FC = () => {
  const { regions, isLoading: regionsLoading, error: regionsError } = useRegionsConfig();
  const [selectedRegion, setSelectedRegion] = useState<string>('');
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );
  const [selectedServers, setSelectedServers] = useState<Set<string>>(new Set());
  const [sortField, setSortField] = useState<SortField>('rackID');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  
  const { buildHistory, isLoading, error, refetch } = useBuildHistory(selectedDate);
  const { assignServers, assignmentStates, error: assignError } = useAssignServers();

  // Set default region once regions are loaded
  useEffect(() => {
    if (regions.length > 0 && !selectedRegion) {
      setSelectedRegion(regions[0].code);
    }
  }, [regions, selectedRegion]);

  const currentRegionData = buildHistory ? buildHistory[selectedRegion.toLowerCase() as keyof typeof buildHistory] || [] : [];
  
  const { unassignedServers, assignedServers } = useMemo(() => {
    const unassigned = currentRegionData.filter(server => server.assigned_status !== 'assigned');
    const assigned = currentRegionData.filter(server => server.assigned_status === 'assigned');
    return { unassignedServers: unassigned, assignedServers: assigned };
  }, [currentRegionData]);

  const sortedUnassignedServers = useMemo(() => {
    return [...unassignedServers].sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];

      if (sortField === 'rackID') {
        // Custom sort for rack IDs (e.g., "1-A", "1-B", "2-A")
        const [aRack, aSlot] = aValue.split('-');
        const [bRack, bSlot] = bValue.split('-');
        const rackCompare = parseInt(aRack) - parseInt(bRack);
        if (rackCompare !== 0) {
          return sortDirection === 'asc' ? rackCompare : -rackCompare;
        } else {
          const slotCompare = aSlot.localeCompare(bSlot);
          return sortDirection === 'asc' ? slotCompare : -slotCompare;
        }
      }

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        const comparison = aValue.localeCompare(bValue);
        return sortDirection === 'asc' ? comparison : -comparison;
      }

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
      }

      return 0;
    });
  }, [unassignedServers, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleSelectAll = () => {
    if (selectedServers.size === sortedUnassignedServers.length) {
      setSelectedServers(new Set());
    } else {
      setSelectedServers(new Set(sortedUnassignedServers.map(server => server.dbid)));
    }
  };

  const handleServerSelect = (dbid: string) => {
    const newSelected = new Set(selectedServers);
    if (newSelected.has(dbid)) {
      newSelected.delete(dbid);
    } else {
      newSelected.add(dbid);
    }
    setSelectedServers(newSelected);
  };

  const handleAssign = async () => {
    const serversToAssign = sortedUnassignedServers.filter(server =>
      selectedServers.has(server.dbid)
    );

    await assignServers(serversToAssign);
    setSelectedServers(new Set());
    refetch();
  };

  const getAssignmentIcon = (status: AssignmentStatus) => {
    switch (status) {
      case 'loading':
        return <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-400"></div>;
      case 'success':
        return <Check size={16} className="text-green-400" />;
      case 'failed':
        return <X size={16} className="text-red-400" />;
      default:
        return null;
    }
  };

  const isAssigning = Object.values(assignmentStates).some(status => status === 'loading');

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' ? 
      <ChevronUp size={14} className="inline ml-1" /> : 
      <ChevronDown size={14} className="inline ml-1" />;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <UserCheck size={24} className="text-green-400" />
          <h1 className="text-2xl font-bold text-white font-mono">Assign</h1>
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
          
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          
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
            <span className="text-gray-300 font-mono">Loading build history...</span>
          </div>
        </div>
      )}

      {(error || assignError || regionsError) && (
        <div className="bg-red-900/20 border border-red-700 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertCircle size={16} className="text-red-400" />
            <span className="text-red-400 font-mono text-sm">Error: {error || assignError || regionsError}</span>
          </div>
        </div>
      )}

      {buildHistory && !isLoading && !regionsLoading && selectedRegion && (
        <div className="space-y-6">
          {/* Unassigned Servers Section */}
          <div className="bg-gray-800 rounded-lg border border-gray-700">
            <div className="p-4 border-b border-gray-700">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white font-mono">
                  Available to Assign - {selectedDate}
                </h2>
                <div className="flex items-center space-x-3">
                  {sortedUnassignedServers.length > 0 && (
                    <button
                      onClick={handleSelectAll}
                      className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm transition-colors"
                    >
                      {selectedServers.size === sortedUnassignedServers.length ? 'Deselect All' : 'Select All'}
                    </button>
                  )}
                  {selectedServers.size > 0 && (
                    <button
                      onClick={handleAssign}
                      disabled={isAssigning}
                      className="px-3 py-1.5 bg-green-600 hover:bg-green-700 disabled:bg-green-800 text-white rounded text-sm transition-colors"
                    >
                      {isAssigning ? 'Assigning...' : `Assign ${selectedServers.size} servers`}
                    </button>
                  )}
                </div>
              </div>
            </div>
            
            {sortedUnassignedServers.length === 0 ? (
              <div className="p-8 text-center">
                <p className="text-gray-400 font-mono">Nothing to assign for {selectedDate}</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-700">
                    <tr>
                      <th className="px-4 py-3 text-left">
                        <input
                          type="checkbox"
                          checked={selectedServers.size === sortedUnassignedServers.length && sortedUnassignedServers.length > 0}
                          onChange={handleSelectAll}
                          className="rounded border-gray-600 bg-gray-700 text-green-600 focus:ring-green-500"
                        />
                      </th>
                      <th 
                        className="px-4 py-3 text-left text-white font-mono text-sm cursor-pointer hover:bg-gray-600"
                        onClick={() => handleSort('rackID')}
                      >
                        Rack ID <SortIcon field="rackID" />
                      </th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">Type</th>
                      <th 
                        className="px-4 py-3 text-left text-white font-mono text-sm cursor-pointer hover:bg-gray-600"
                        onClick={() => handleSort('hostname')}
                      >
                        Hostname <SortIcon field="hostname" />
                      </th>
                      <th 
                        className="px-4 py-3 text-left text-white font-mono text-sm cursor-pointer hover:bg-gray-600"
                        onClick={() => handleSort('dbid')}
                      >
                        DBID <SortIcon field="dbid" />
                      </th>
                      <th 
                        className="px-4 py-3 text-left text-white font-mono text-sm cursor-pointer hover:bg-gray-600"
                        onClick={() => handleSort('serial_number')}
                      >
                        S/N <SortIcon field="serial_number" />
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedUnassignedServers.map((server) => (
                      <tr key={server.dbid} className="border-t border-gray-700 hover:bg-gray-750">
                        <td className="px-4 py-3">
                          {assignmentStates[server.dbid] ? (
                            <div className="flex justify-center">
                              {getAssignmentIcon(assignmentStates[server.dbid])}
                            </div>
                          ) : (
                            <input
                              type="checkbox"
                              checked={selectedServers.has(server.dbid)}
                              onChange={() => handleServerSelect(server.dbid)}
                              className="rounded border-gray-600 bg-gray-700 text-green-600 focus:ring-green-500"
                            />
                          )}
                        </td>
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm">{server.rackID}</td>
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm">Server</td>
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm">{server.hostname}</td>
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm">{server.dbid}</td>
                        <td className="px-4 py-3 text-gray-300 font-mono text-sm">{server.serial_number}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
          
          {/* Already Assigned Section */}
          {assignedServers.length > 0 && (
            <div className="bg-gray-800 rounded-lg border border-gray-700">
              <div className="p-4 border-b border-gray-700">
                <h2 className="text-lg font-semibold text-white font-mono">
                  Already Assigned ({assignedServers.length})
                </h2>
              </div>
              
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-700">
                    <tr>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">Rack ID</th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">Type</th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">Hostname</th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">DBID</th>
                      <th className="px-4 py-3 text-left text-white font-mono text-sm">S/N</th>
                    </tr>
                  </thead>
                  <tbody>
                    {assignedServers.map((server) => (
                      <tr key={server.dbid} className="border-t border-gray-700">
                        <td className="px-4 py-3 text-gray-400 font-mono text-sm">{server.rackID}</td>
                        <td className="px-4 py-3 text-gray-400 font-mono text-sm">Server</td>
                        <td className="px-4 py-3 text-gray-400 font-mono text-sm">{server.hostname}</td>
                        <td className="px-4 py-3 text-gray-400 font-mono text-sm">{server.dbid}</td>
                        <td className="px-4 py-3 text-gray-400 font-mono text-sm">{server.serial_number}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AssignPage;