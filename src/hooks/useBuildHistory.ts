import { useState, useEffect } from 'react';
import { Server, Region } from '../types/build';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'https://test-backend.suntrap.workers.dev';
const DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true';

// Mock data for dev mode - mix of assigned and unassigned servers
const mockBuildHistory: Record<string, Server[]> = {
  cbg: [
    {"rackID":"1-E","hostname":"iernfgwkf","dbid":"305589","serial_number":"483446357","percent_built":100,"assigned_status":"not assigned"},
    {"rackID":"6-E","hostname":"fnahcyoier","dbid":"231401","serial_number":"544877182","percent_built":100,"assigned_status":"assigned"},
    {"rackID":"3-6","hostname":"hjnte","dbid":"52834","serial_number":"177514038","percent_built":100,"assigned_status":"not assigned"},
    {"rackID":"3-G","hostname":"xtvbuvx","dbid":"873243","serial_number":"530328492","percent_built":100,"assigned_status":"assigned"},
    {"rackID":"8-5","hostname":"cjvemhku","dbid":"441381","serial_number":"134822229","percent_built":100,"assigned_status":"not assigned"},
  ],
  dub: [
    {"rackID":"6-C","hostname":"jeqzdjeqp","dbid":"996783","serial_number":"841472939","percent_built":100,"assigned_status":"not assigned"},
    {"rackID":"3-1","hostname":"myvwteavhg","dbid":"801045","serial_number":"632685004","percent_built":100,"assigned_status":"assigned"},
    {"rackID":"5-E","hostname":"eporghuwq","dbid":"759751","serial_number":"832651260","percent_built":100,"assigned_status":"not assigned"},
  ],
  dal: [
    {"rackID":"1-F","hostname":"genops","dbid":"912039","serial_number":"802113764","percent_built":100,"assigned_status":"not assigned"},
    {"rackID":"5-A","hostname":"lhtts","dbid":"665243","serial_number":"253232262","percent_built":100,"assigned_status":"assigned"},
    {"rackID":"3-E","hostname":"kexnupldux","dbid":"639296","serial_number":"467416621","percent_built":100,"assigned_status":"not assigned"},
  ]
};

export const useBuildHistory = (date: string) => {
  const [buildHistory, setBuildHistory] = useState<Record<string, Server[]> | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBuildHistory = async () => {
    if (DEV_MODE) {
      setIsLoading(true);
      // Simulate API delay
      setTimeout(() => {
        setBuildHistory(mockBuildHistory);
        setIsLoading(false);
      }, 1000);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch(`${BACKEND_URL}/api/build-history/${date}`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setBuildHistory(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch build history');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (date) {
      fetchBuildHistory();
    }
  }, [date]);

  return {
    buildHistory,
    isLoading,
    error,
    refetch: fetchBuildHistory,
  };
};