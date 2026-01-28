import { useState, useEffect, useCallback, useRef } from 'react';
import { fetchWithFallback } from '../utils/api';
import { RegionLockInfo, RegionLockResponse } from '../types/lock';

// Default polling interval (5 seconds)
const DEFAULT_POLL_INTERVAL = 5000;

interface UseRegionLocksOptions {
  pollInterval?: number;
  enabled?: boolean;
}

interface UseRegionLocksResult {
  locks: Record<string, RegionLockInfo>;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  getLockForRegion: (region: string) => RegionLockInfo | null;
}

export const useRegionLocks = (options: UseRegionLocksOptions = {}): UseRegionLocksResult => {
  const {
    pollInterval = DEFAULT_POLL_INTERVAL,
    enabled = true,
  } = options;

  const [locks, setLocks] = useState<Record<string, RegionLockInfo>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<number | null>(null);

  const fetchLocks = useCallback(async () => {
    if (!enabled) return;

    setIsLoading(true);
    setError(null);

    try {
      const mockResponse: RegionLockResponse = { locks: {} };

      const response = await fetchWithFallback<RegionLockResponse>(
        '/api/preconfig/locks',
        {
          method: 'GET',
          credentials: 'include',
        },
        mockResponse
      );

      setLocks(response.locks || {});
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch lock status';
      setError(errorMessage);
      console.error('Error fetching region locks:', err);
    } finally {
      setIsLoading(false);
    }
  }, [enabled]);

  // Initial fetch and polling
  useEffect(() => {
    if (!enabled) {
      // Clear locks when disabled
      setLocks({});
      return;
    }

    // Initial fetch
    fetchLocks();

    // Set up polling
    if (pollInterval > 0) {
      intervalRef.current = window.setInterval(fetchLocks, pollInterval);
    }

    return () => {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [fetchLocks, pollInterval, enabled]);

  const getLockForRegion = useCallback((region: string): RegionLockInfo | null => {
    const regionLower = region.toLowerCase();
    const lock = locks[regionLower];

    if (lock && lock.is_locked) {
      return lock;
    }

    return null;
  }, [locks]);

  const refetch = useCallback(async () => {
    await fetchLocks();
  }, [fetchLocks]);

  return {
    locks,
    isLoading,
    error,
    refetch,
    getLockForRegion,
  };
};
