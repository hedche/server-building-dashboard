import { useState, useEffect, useCallback } from 'react';
import { fetchWithFallback } from '../utils/api';

export interface Preconfig {
  dbid: string;
  depot: number;
  appliance_size: string | null;
  config: Record<string, any>;
  created_at: string;
  last_pushed_at?: string | null;
  pushed_to?: string[];
}

// Mock data for dev mode - organized by region
const mockPreconfigsByRegion: Record<string, Preconfig[]> = {
  cbg: [
    {
      dbid: 'dbid-001',
      depot: 1,
      appliance_size: 'small',
      config: { os: 'ubuntu-22.04', ram: '128GB', storage: '4x1TB NVMe' },
      created_at: '2025-01-15T10:00:00Z'
    },
    {
      dbid: 'dbid-002',
      depot: 1,
      appliance_size: 'medium',
      config: { os: 'centos-8', ram: '256GB', storage: '8x2TB NVMe' },
      created_at: '2025-01-15T11:00:00Z'
    },
    {
      dbid: 'dbid-003',
      depot: 1,
      appliance_size: 'large',
      config: { os: 'rocky-9', ram: '512GB', storage: '12x4TB NVMe' },
      created_at: '2025-01-15T12:00:00Z'
    }
  ],
  dub: [
    {
      dbid: 'dbid-004',
      depot: 2,
      appliance_size: 'small',
      config: { os: 'ubuntu-22.04', ram: '128GB', storage: '4x1TB NVMe' },
      created_at: '2025-01-15T12:00:00Z'
    },
    {
      dbid: 'dbid-005',
      depot: 2,
      appliance_size: 'medium',
      config: { os: 'ubuntu-22.04', ram: '256GB', storage: '8x2TB NVMe' },
      created_at: '2025-01-15T13:00:00Z'
    }
  ],
  dal: [
    {
      dbid: 'dbid-006',
      depot: 4,
      appliance_size: 'small',
      config: { os: 'rocky-9', ram: '128GB', storage: '4x1TB NVMe' },
      created_at: '2025-01-15T13:00:00Z'
    },
    {
      dbid: 'dbid-007',
      depot: 4,
      appliance_size: 'large',
      config: { os: 'rocky-9', ram: '1TB', storage: '16x8TB NVMe' },
      created_at: '2025-01-15T14:00:00Z'
    }
  ]
};

export const usePreconfigs = (region: string) => {
  const [preconfigs, setPreconfigs] = useState<Preconfig[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPreconfigs = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const regionLower = region.toLowerCase();
      const mockData = mockPreconfigsByRegion[regionLower] || [];

      // Try backend first, fall back to mock data in dev mode if unreachable
      const data = await fetchWithFallback<Preconfig[]>(
        `/api/preconfig/${regionLower}`,
        { credentials: 'include' },
        mockData
      );

      setPreconfigs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch preconfigs');
    } finally {
      setIsLoading(false);
    }
  }, [region]);

  useEffect(() => {
    fetchPreconfigs();
  }, [fetchPreconfigs]);

  return {
    preconfigs,
    isLoading,
    error,
    refetch: fetchPreconfigs,
  };
};
