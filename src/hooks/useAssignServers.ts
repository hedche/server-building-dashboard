import { useState } from 'react';
import { Server } from '../types/build';
import { fetchWithFallback } from '../utils/api';

interface AssignPayload {
  serial_number: string;
  hostname: string;
  dbid: string;
}

export type AssignmentStatus = 'idle' | 'loading' | 'success' | 'failed';

interface AssignmentState {
  [dbid: string]: AssignmentStatus;
}

export const useAssignServers = () => {
  const [assignmentStates, setAssignmentStates] = useState<AssignmentState>({});
  const [error, setError] = useState<string | null>(null);

  const assignSingleServer = async (payload: AssignPayload): Promise<boolean> => {
    try {
      setError(null);

      // Mock response for fallback in dev mode
      const mockResponse = {
        status: Math.random() > 0.3 ? 'success' : 'error', // 70% success rate
        message: 'Mock assignment (backend unreachable)'
      };

      // Try backend first, fall back to mock in dev mode if unreachable
      const result = await fetchWithFallback<{ status: string; message: string }>(
        '/api/assign',
        {
          method: 'POST',
          credentials: 'include',
          body: JSON.stringify(payload),
        },
        mockResponse
      );

      return result.status === 'success';
    } catch (err) {
      console.error('Assignment failed:', err);
      return false;
    }
  };

  const assignServers = async (servers: Server[]) => {
    setError(null);
    
    // Initialize all servers to loading state
    const initialStates: AssignmentState = {};
    servers.forEach(server => {
      initialStates[server.dbid] = 'loading';
    });
    setAssignmentStates(initialStates);

    // Process each server sequentially
    for (const server of servers) {
      try {
        const payload = {
          serial_number: server.serial_number,
          hostname: server.hostname,
          dbid: server.dbid,
        };

        const success = await assignSingleServer(payload);
        
        setAssignmentStates(prev => ({
          ...prev,
          [server.dbid]: success ? 'success' : 'failed'
        }));
      } catch (err) {
        setAssignmentStates(prev => ({
          ...prev,
          [server.dbid]: 'failed'
        }));
      }
    }

    // Clear states after a brief delay to allow user to see results
    setTimeout(() => {
      setAssignmentStates({});
    }, 500);
  };

  return {
    assignServers,
    assignmentStates,
    error,
  };
};