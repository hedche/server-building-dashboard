import { useState, useEffect } from 'react';
import { BuildStatus } from '../types/build';
import { fetchWithFallback } from '../utils/api';

// Mock data for dev mode
const mockBuildStatus: BuildStatus = {
  cbg: [
    {"rackID":"1-E","hostname":"th-12345-45","dbid":"305589","serial_number":"483446357","percent_built":55,"assigned_status":"not assigned","machine_type":"Server","status":"installing"},
    {"rackID":"6-E","hostname":"ab-98765-123","dbid":"231401","serial_number":"544877182","percent_built":65,"assigned_status":"not assigned","machine_type":"Server","status":"installing"},
    {"rackID":"3-6","hostname":"cd-45678-89","dbid":"52834","serial_number":"177514038","percent_built":96,"assigned_status":"not assigned","machine_type":"Server","status":"installing"},
    {"rackID":"3-G","hostname":"ef-11111-1","dbid":"873243","serial_number":"530328492","percent_built":16,"assigned_status":"not assigned","machine_type":"Server","status":"installing"},
    {"rackID":"8-5","hostname":"gh-22222-22","dbid":"441381","serial_number":"134822229","percent_built":66,"assigned_status":"not assigned","machine_type":"Server","status":"installing"},
    {"rackID":"1-C","hostname":"ij-33333-333","dbid":"751289","serial_number":"903133629","percent_built":20,"assigned_status":"not assigned","machine_type":"Server","status":"installing"},
    {"rackID":"4-F","hostname":"kl-44444-44","dbid":"773435","serial_number":"250995085","percent_built":49,"assigned_status":"not assigned","machine_type":"Server","status":"installing"},
    {"rackID":"8-2","hostname":"mn-55555-55","dbid":"616757","serial_number":"645761008","percent_built":21,"assigned_status":"not assigned","machine_type":"Server","status":"installing"},
    {"rackID":"S1-A","hostname":"op-66666-6","dbid":"123456","serial_number":"987654321","percent_built":30,"assigned_status":"not assigned","machine_type":"Small Server","status":"installing"},
    {"rackID":"S2-B","hostname":"qr-77777-77","dbid":"234567","serial_number":"876543210","percent_built":100,"assigned_status":"not assigned","machine_type":"Small Server","status":"complete"},
    {"rackID":"S1-C","hostname":"st-88888-888","dbid":"345678","serial_number":"765432109","percent_built":45,"assigned_status":"not assigned","machine_type":"Small Server","status":"failed"}
  ],
  dub: [
    {"rackID":"6-C","hostname":"uv-99999-99","dbid":"996783","serial_number":"841472939","percent_built":49,"assigned_status":"not assigned","machine_type":"Server","status":"installing"},
    {"rackID":"3-1","hostname":"wx-10101-101","dbid":"801045","serial_number":"632685004","percent_built":6,"assigned_status":"not assigned","machine_type":"Server","status":"installing"},
    {"rackID":"5-E","hostname":"yz-20202-202","dbid":"759751","serial_number":"832651260","percent_built":29,"assigned_status":"not assigned","machine_type":"Server","status":"installing"},
    {"rackID":"5-F","hostname":"ab-30303-3","dbid":"234841","serial_number":"384741486","percent_built":46,"assigned_status":"not assigned","machine_type":"Server","status":"installing"}
  ],
  dal: [
    {"rackID":"1-F","hostname":"cd-40404-404","dbid":"912039","serial_number":"802113764","percent_built":34,"assigned_status":"not assigned","machine_type":"Server","status":"installing"},
    {"rackID":"5-A","hostname":"ef-50505-50","dbid":"665243","serial_number":"253232262","percent_built":43,"assigned_status":"not assigned","machine_type":"Server","status":"installing"},
    {"rackID":"3-E","hostname":"gh-60606-606","dbid":"639296","serial_number":"467416621","percent_built":64,"assigned_status":"not assigned","machine_type":"Server","status":"installing"},
    {"rackID":"5-D","hostname":"ij-70707-7","dbid":"408892","serial_number":"774101658","percent_built":13,"assigned_status":"not assigned","machine_type":"Server","status":"installing"}
  ]
};

export const useBuildStatus = () => {
  const [buildStatus, setBuildStatus] = useState<BuildStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBuildStatus = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Try backend first, fall back to mock data in dev mode if unreachable
      const data = await fetchWithFallback<BuildStatus>(
        '/api/build-status',
        { credentials: 'include' },
        mockBuildStatus
      );

      setBuildStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch build status');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchBuildStatus();
  }, []);

  return {
    buildStatus,
    isLoading,
    error,
    refetch: fetchBuildStatus,
  };
};