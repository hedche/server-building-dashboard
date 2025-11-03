import { useState, useEffect } from 'react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'https://test-backend.suntrap.workers.dev';
const DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true';

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
    if (DEV_MODE) {
      setIsLoading(true);
      // Simulate API delay
      setTimeout(() => {
        setHostnames(generateMockHostnames());
        setIsLoading(false);
      }, 1500);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch(`${BACKEND_URL}/api/hostnames`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setHostnames(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch hostnames');
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