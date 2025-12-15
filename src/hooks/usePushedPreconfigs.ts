import { useState, useEffect } from 'react';
import { fetchWithFallback } from '../utils/api';
import { Preconfig } from './usePreconfigs';

const mockPushedPreconfigs: Preconfig[] = [
  {
    dbid: 'pushed-001',
    depot: 1,
    appliance_size: 'small',
    config: { os: 'ubuntu-20.04', ram: '128GB', storage: '4x1TB NVMe' },
    created_at: '2025-01-14T15:30:00Z',
    pushed_at: '2025-01-14T15:30:00Z'
  },
  {
    dbid: 'pushed-002',
    depot: 2,
    appliance_size: 'medium',
    config: { os: 'ubuntu-22.04', ram: '512GB', storage: '12x4TB NVMe' },
    created_at: '2025-01-13T09:15:00Z',
    pushed_at: '2025-01-13T09:15:00Z'
  },
];

export const usePushedPreconfigs = () => {
  const [pushedPreconfigs, setPushedPreconfigs] = useState<Preconfig[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPushedPreconfigs = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Try backend first, fall back to mock data in dev mode if unreachable
      const data = await fetchWithFallback<Preconfig[]>(
        '/api/preconfigs/pushed',
        { credentials: 'include' },
        mockPushedPreconfigs
      );

      setPushedPreconfigs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch pushed preconfigs');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPushedPreconfigs();
  }, []);

  return {
    pushedPreconfigs,
    isLoading,
    error,
    refetch: fetchPushedPreconfigs,
  };
};
