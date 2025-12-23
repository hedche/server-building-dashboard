import { useState, useCallback } from 'react';
import { fetchWithFallback } from '../utils/api';
import { Preconfig } from './usePreconfigs';

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

export type PushStatus = 'idle' | 'pushing' | 'complete';

export interface PushState {
  status: PushStatus;
  results: BuildServerPushResult[];
  pushedPreconfigs: Preconfig[];
  error: string | null;
  overallStatus: 'success' | 'partial' | 'failed' | null;
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
  });

  const pushPreconfig = useCallback(async (region: string, buildServers: string[]) => {
    setState({
      status: 'pushing',
      results: [],
      pushedPreconfigs: [],
      error: null,
      overallStatus: null,
    });

    try {
      const mockResponse = generateMockResults(buildServers);

      const response = await fetchWithFallback<PushPreconfigResponse>(
        `/api/preconfig/${region.toLowerCase()}/push`,
        {
          method: 'POST',
          credentials: 'include',
        },
        mockResponse
      );

      setState({
        status: 'complete',
        results: response.results,
        pushedPreconfigs: response.pushed_preconfigs,
        error: response.status === 'failed' ? response.message : null,
        overallStatus: response.status,
      });

      return response;
    } catch (err) {
      setState(prev => ({
        ...prev,
        status: 'complete',
        error: err instanceof Error ? err.message : 'Failed to push preconfig',
        overallStatus: 'failed',
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
    });
  }, []);

  return {
    ...state,
    pushPreconfig,
    reset,
  };
};
