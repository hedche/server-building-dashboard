import { useState } from 'react';
import { fetchTextWithFallback } from '../utils/api';

/**
 * Generate mock build log for development/testing
 */
const generateMockLog = (): string => {
  const lines: string[] = [];
  const now = new Date();

  for (let i = 0; i < 200; i++) {
    const timestamp = new Date(now.getTime() - (200 - i) * 1000).toISOString();
    const logTypes = ['INFO', 'DEBUG', 'WARN', 'ERROR', 'SUCCESS'];
    const logType = logTypes[Math.floor(Math.random() * logTypes.length)];
    const messages = [
      'Compiling source files',
      'Running tests',
      'Building artifacts',
      'Deploying to servers',
      'Health check passed',
      'Optimization complete',
      'Cache invalidated',
      'Dependencies resolved',
      'Docker image built',
      'Pushing to registry',
    ];
    const message = messages[Math.floor(Math.random() * messages.length)];

    lines.push(`[${timestamp}] [${logType}] ${message}`);
  }

  return lines.join('\n');
};

const mockBuildLog = generateMockLog();

export const useBuildLog = () => {
  const [log, setLog] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLog = async (hostname: string) => {
    setIsLoading(true);
    setError(null);
    setLog('');

    try {
      const logData = await fetchTextWithFallback(
        `/api/build-logs/${hostname}`,
        {},
        mockBuildLog
      );
      setLog(logData);
    } catch (err) {
      if (err instanceof Response) {
        if (err.status === 404) {
          setError('Build log not found for this hostname');
        } else if (err.status >= 500) {
          setError('Server error loading build log');
        } else {
          setError('Failed to fetch log');
        }
      } else {
        setError(err instanceof Error ? err.message : 'Failed to fetch log');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return { log, isLoading, error, fetchLog };
};
