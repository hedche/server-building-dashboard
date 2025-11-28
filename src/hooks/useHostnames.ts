import { useState, useEffect } from 'react';
import { fetchWithFallback } from '../utils/api';

// Mock data for dev mode - simulate 40,000 hostnames
const generateMockHostnames = (): string[] => {
  const hostnames: string[] = [];
  const prefixes = ['web', 'db', 'api', 'cache', 'worker', 'mail', 'cdn', 'proxy', 'app', 'srv'];
  const suffixes = ['prod', 'dev', 'test', 'staging', 'backup', 'primary', 'secondary', 'master', 'slave'];
  const regions = ['us-east', 'us-west', 'eu-west', 'eu-central', 'ap-south', 'ap-north'];
  
  // Generate realistic hostnames
  for (let i = 1; i <= 40000; i++) {
    const prefix = prefixes[Math.floor(Math.random() * prefixes.length)];
    const suffix = suffixes[Math.floor(Math.random() * suffixes.length)];
    const region = regions[Math.floor(Math.random() * regions.length)];
    const number = String(i).padStart(3, '0');
    
    hostnames.push(`${prefix}-${suffix}-${region}-${number}`);
  }
  
  // Add some specific test hostnames for easier testing
  hostnames.push('test-server-001', 'prod-web-server', 'staging-db-primary', 'dev-api-gateway');
  
  return hostnames.sort();
};

export const useHostnames = () => {
  const [hostnames, setHostnames] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHostnames = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Try backend first, fall back to mock data in dev mode if unreachable
      const data = await fetchWithFallback<string[]>(
        '/api/hostnames',
        { credentials: 'include' },
        generateMockHostnames()
      );

      setHostnames(data);
    } catch (err) {
      // Log the detailed error to console for debugging
      console.error('Failed to fetch hostnames:', err);
      setError('Unable to fetch hostname list from backend');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHostnames();
  }, []);

  return {
    hostnames,
    isLoading,
    error,
    refetch: fetchHostnames,
  };
};