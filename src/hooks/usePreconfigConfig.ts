import { useState, useEffect, useCallback } from 'react';
import { fetchWithFallback } from '../utils/api';

export interface PreconfigConfig {
  appliance_sizes: string[];
}

// Mock data for dev mode fallback
const mockPreconfigConfig: PreconfigConfig = {
  appliance_sizes: ['small', 'medium', 'large'],
};

export const usePreconfigConfig = () => {
  const [config, setConfig] = useState<PreconfigConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConfig = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const data = await fetchWithFallback<PreconfigConfig>(
        '/api/config/preconfig',
        { credentials: 'include' },
        mockPreconfigConfig
      );

      setConfig(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch preconfig config');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  return {
    config,
    applianceSizes: config?.appliance_sizes ?? [],
    isLoading,
    error,
    refetch: fetchConfig,
  };
};
