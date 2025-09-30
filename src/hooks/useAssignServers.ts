import { useState } from 'react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'https://test-backend.suntrap.workers.dev';
const DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true';

interface AssignPayload {
  serial_numbers: string[];
  hostnames: string[];
  dbids: string[];
}

export const useAssignServers = () => {
  const [isAssigning, setIsAssigning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const assignServers = async (payload: AssignPayload) => {
    if (DEV_MODE) {
      setIsAssigning(true);
      // Simulate API delay
      setTimeout(() => {
        setIsAssigning(false);
        console.log('Dev mode: Would assign servers:', payload);
      }, 1000);
      return true;
    }

    try {
      setIsAssigning(true);
      setError(null);
      
      const response = await fetch(`${BACKEND_URL}/api/assign`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to assign servers');
      return false;
    } finally {
      setIsAssigning(false);
    }
  };

  return {
    assignServers,
    isAssigning,
    error,
  };
};