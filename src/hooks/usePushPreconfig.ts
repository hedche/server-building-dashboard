import { useState } from 'react';
import { fetchWithFallback } from '../utils/api';

export type PushStatus = 'idle' | 'pushing' | 'success' | 'failed';

export const usePushPreconfig = () => {
  const [pushStatus, setPushStatus] = useState<PushStatus>('idle');
  const [error, setError] = useState<string | null>(null);

  const pushPreconfig = async (depot: number): Promise<boolean> => {
    try {
      setError(null);

      // Mock response for fallback in dev mode
      const mockResponse = {
        status: Math.random() > 0.2 ? 'success' : 'error', // 80% success rate
        message: 'Mock push (backend unreachable)'
      };

      // Try backend first, fall back to mock in dev mode if unreachable
      const result = await fetchWithFallback<{ status: string; message: string }>(
        '/api/push-preconfig',
        {
          method: 'POST',
          credentials: 'include',
          body: JSON.stringify({ depot }),
        },
        mockResponse
      );

      return result.status === 'success';
    } catch (err) {
      console.error('Push preconfig failed:', err);
      return false;
    }
  };

  const handlePushPreconfig = async (depot: number) => {
    setPushStatus('pushing');
    setError(null);

    try {
      const success = await pushPreconfig(depot);
      setPushStatus(success ? 'success' : 'failed');
      
      if (!success) {
        setError('Failed to push preconfig');
      }
    } catch (err) {
      setPushStatus('failed');
      setError(err instanceof Error ? err.message : 'Failed to push preconfig');
    }

    // Reset status after brief delay
    setTimeout(() => {
      setPushStatus('idle');
      setError(null);
    }, 500);
  };

  return {
    pushStatus,
    error,
    pushPreconfig: handlePushPreconfig,
  };
};