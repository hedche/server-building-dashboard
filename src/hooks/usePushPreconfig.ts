import { useState, useCallback } from 'react';
import { Preconfig } from './usePreconfigs';
import { RegionLockInfo, LockConflictDetail } from '../types/lock';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
const DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true';

export interface BuildServerPushResult {
  build_server: string;
  status: 'success' | 'failed' | 'skipped';
  error?: string;
  preconfig_count: number;
}

export interface PushPreconfigResponse {
  status: 'success' | 'partial' | 'failed';
  message: string;
  results: BuildServerPushResult[];
  pushed_preconfigs: Preconfig[];
}

export type PushStatus = 'idle' | 'pushing' | 'complete' | 'locked';

export interface PushState {
  status: PushStatus;
  results: BuildServerPushResult[];
  pushedPreconfigs: Preconfig[];
  error: string | null;
  overallStatus: 'success' | 'partial' | 'failed' | null;
  lockInfo: RegionLockInfo | null;
}

// Generate mock results for dev mode fallback
const generateMockResults = (buildServers: string[]): PushPreconfigResponse => {
  const results: BuildServerPushResult[] = buildServers.map(bs => {
    const rand = Math.random();
    if (rand > 0.3) {
      return {
        build_server: bs,
        status: 'success' as const,
        preconfig_count: Math.floor(Math.random() * 3) + 1
      };
    } else if (rand > 0.1) {
      return {
        build_server: bs,
        status: 'failed' as const,
        error: 'Mock connection error',
        preconfig_count: 0
      };
    } else {
      return {
        build_server: bs,
        status: 'skipped' as const,
        error: 'No matching preconfigs',
        preconfig_count: 0
      };
    }
  });

  const successCount = results.filter(r => r.status === 'success').length;
  const failedCount = results.filter(r => r.status === 'failed').length;

  let status: 'success' | 'partial' | 'failed';
  if (failedCount === 0 && successCount > 0) {
    status = 'success';
  } else if (successCount > 0) {
    status = 'partial';
  } else {
    status = 'failed';
  }

  return {
    status,
    message: 'Mock push (backend unreachable)',
    results,
    pushed_preconfigs: []
  };
};

export const usePushPreconfig = () => {
  const [state, setState] = useState<PushState>({
    status: 'idle',
    results: [],
    pushedPreconfigs: [],
    error: null,
    overallStatus: null,
    lockInfo: null,
  });

  const pushPreconfig = useCallback(async (region: string, buildServers: string[]) => {
    setState({
      status: 'pushing',
      results: [],
      pushedPreconfigs: [],
      error: null,
      overallStatus: null,
      lockInfo: null,
    });

    try {
      // In dev mode with backend unreachable, use mock
      if (DEV_MODE) {
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 3000);

          const response = await fetch(`${BACKEND_URL}/api/preconfig/${region.toLowerCase()}/push`, {
            method: 'POST',
            credentials: 'include',
            signal: controller.signal,
            headers: {
              'Content-Type': 'application/json',
            },
          });

          clearTimeout(timeoutId);

          // Handle 409 Conflict (region locked)
          if (response.status === 409) {
            const conflictData: LockConflictDetail = await response.json();
            setState({
              status: 'locked',
              results: [],
              pushedPreconfigs: [],
              error: conflictData.message,
              overallStatus: 'failed',
              lockInfo: conflictData.lock_info,
            });
            return null;
          }

          if (response.ok) {
            const data: PushPreconfigResponse = await response.json();
            setState({
              status: 'complete',
              results: data.results,
              pushedPreconfigs: data.pushed_preconfigs,
              error: data.status === 'failed' ? data.message : null,
              overallStatus: data.status,
              lockInfo: null,
            });
            return data;
          } else {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
        } catch (err) {
          // Backend unreachable in dev mode, use mock
          if (err instanceof Error && err.name === 'AbortError') {
            console.warn('Backend timeout, using mock data');
          }
          const mockResponse = generateMockResults(buildServers);
          setState({
            status: 'complete',
            results: mockResponse.results,
            pushedPreconfigs: mockResponse.pushed_preconfigs,
            error: mockResponse.status === 'failed' ? mockResponse.message : null,
            overallStatus: mockResponse.status,
            lockInfo: null,
          });
          return mockResponse;
        }
      }

      // Production mode - no mock fallback
      const response = await fetch(`${BACKEND_URL}/api/preconfig/${region.toLowerCase()}/push`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      // Handle 409 Conflict (region locked)
      if (response.status === 409) {
        const conflictData: LockConflictDetail = await response.json();
        setState({
          status: 'locked',
          results: [],
          pushedPreconfigs: [],
          error: conflictData.message,
          overallStatus: 'failed',
          lockInfo: conflictData.lock_info,
        });
        return null;
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: PushPreconfigResponse = await response.json();
      setState({
        status: 'complete',
        results: data.results,
        pushedPreconfigs: data.pushed_preconfigs,
        error: data.status === 'failed' ? data.message : null,
        overallStatus: data.status,
        lockInfo: null,
      });

      return data;
    } catch (err) {
      setState(prev => ({
        ...prev,
        status: 'complete',
        error: err instanceof Error ? err.message : 'Failed to push preconfig',
        overallStatus: 'failed',
        lockInfo: null,
      }));
      return null;
    }
  }, []);

  const reset = useCallback(() => {
    setState({
      status: 'idle',
      results: [],
      pushedPreconfigs: [],
      error: null,
      overallStatus: null,
      lockInfo: null,
    });
  }, []);

  return {
    ...state,
    pushPreconfig,
    reset,
  };
};
