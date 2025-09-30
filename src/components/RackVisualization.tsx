import React from 'react';
import { Server } from '../types/build';

interface RackVisualizationProps {
  servers: Server[];
}

const RackVisualization: React.FC<RackVisualizationProps> = ({ servers }) => {
  // Group servers by rack number (1-8)
  const rackGroups = servers.reduce((acc, server) => {
    const rackNumber = server.rackID.split('-')[0];
    if (!acc[rackNumber]) {
      acc[rackNumber] = [];
    }
    acc[rackNumber].push(server);
    return acc;
  }, {} as Record<string, Server[]>);

  // Sort rack positions: 1-8, then A-G
  const sortRackPosition = (a: string, b: string) => {
    const getPositionValue = (pos: string) => {
      if (/^\d+$/.test(pos)) return parseInt(pos);
      return pos.charCodeAt(0) - 'A'.charCodeAt(0) + 9;
    };
    return getPositionValue(a) - getPositionValue(b);
  };

  const getProgressColor = (percent: number) => {
    if (percent >= 90) return 'bg-green-500';
    if (percent >= 70) return 'bg-blue-500';
    if (percent >= 50) return 'bg-yellow-500';
    if (percent >= 25) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: 8 }, (_, i) => i + 1).map(rackNumber => {
        const rackServers = rackGroups[rackNumber.toString()] || [];
        
        // Group by slot position
        const slotGroups = rackServers.reduce((acc, server) => {
          const slot = server.rackID.split('-')[1];
          if (!acc[slot]) {
            acc[slot] = [];
          }
          acc[slot].push(server);
          return acc;
        }, {} as Record<string, Server[]>);

        const sortedSlots = Object.keys(slotGroups).sort(sortRackPosition);

        return (
          <div key={rackNumber} className="bg-gray-800 rounded-lg border border-gray-700 p-3">
            <h3 className="text-green-400 font-mono font-bold mb-3 text-center">
              Rack {rackNumber}
            </h3>
            
            {rackServers.length === 0 ? (
              <div className="text-gray-500 text-center py-4 text-xs">
                No servers installing
              </div>
            ) : (
              <div className="space-y-2">
                {sortedSlots.map(slot => (
                  <div key={slot} className="space-y-1">
                    <div className="text-xs text-gray-400 font-mono">
                      Slot {slot}
                    </div>
                    {slotGroups[slot].map(server => (
                      <div
                        key={server.dbid}
                        className="bg-gray-700 rounded p-2 border-l-4 border-gray-600"
                        style={{
                          borderLeftColor: `var(--progress-color-${Math.floor(server.percent_built / 10)})`
                        }}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-mono text-xs text-white font-medium">
                            {server.hostname}
                          </span>
                          <span className="text-xs text-gray-300">
                            {server.percent_built}%
                          </span>
                        </div>
                        
                        <div className="w-full bg-gray-600 rounded-full h-1.5 mb-2">
                          <div
                            className={`h-1.5 rounded-full transition-all duration-300 ${getProgressColor(server.percent_built)}`}
                            style={{ width: `${server.percent_built}%` }}
                          />
                        </div>
                        
                        <div className="text-xs text-gray-400 space-y-0.5">
                          <div>DB: {server.dbid}</div>
                          <div>SN: {server.serial_number}</div>
                          <div className="capitalize">{server.assigned_status}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default RackVisualization;