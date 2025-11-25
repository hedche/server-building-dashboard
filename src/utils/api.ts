/**
 * API utility for handling backend connections with automatic fallback to mock data
 */

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
const DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true';

/**
 * Apply simulated API delay if configured
 * Simulates slow network or backend response time
 */
export const applySimulatedDelay = async (): Promise<void> => {
  const delaySeconds = parseFloat(import.meta.env.VITE_SIMULATED_API_DELAY_TIME || '0');
  const delayMs = Math.max(0, delaySeconds * 1000); // Convert to ms, ensure non-negative

  if (delayMs > 0) {
    await new Promise(resolve => setTimeout(resolve, delayMs));
  }
};

// Track backend availability
let backendAvailable: boolean | null = null;
let lastHealthCheck = 0;
const HEALTH_CHECK_INTERVAL = 30000; // 30 seconds

/**
 * Check if backend is reachable
 */
export const checkBackendHealth = async (): Promise<boolean> => {
  // In production mode, always try backend
  if (!DEV_MODE) {
    return true;
  }

  const now = Date.now();

  // Use cached result if recent
  if (backendAvailable !== null && now - lastHealthCheck < HEALTH_CHECK_INTERVAL) {
    return backendAvailable;
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 second timeout

    const response = await fetch(`${BACKEND_URL}/health`, {
      method: 'GET',
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    clearTimeout(timeoutId);

    backendAvailable = response.ok;
    lastHealthCheck = now;

    if (backendAvailable) {
      console.log('%c✓ Backend Connected', 'color: #10b981; font-weight: bold;', `(${BACKEND_URL})`);
    } else {
      console.warn('%c⚠ Backend Unreachable - Using Mock Data', 'color: #f59e0b; font-weight: bold;', `(${BACKEND_URL})`);
    }

    return backendAvailable;
  } catch (error) {
    backendAvailable = false;
    lastHealthCheck = now;
    console.warn('%c⚠ Backend Unreachable - Using Mock Data', 'color: #f59e0b; font-weight: bold;', `(${BACKEND_URL})`, error);
    return false;
  }
};

/**
 * Fetch with automatic fallback to mock data in dev mode
 */
export const fetchWithFallback = async <T>(
  endpoint: string,
  options: RequestInit = {},
  mockData: T
): Promise<T> => {
  // In production, always try real backend (no fallback)
  if (!DEV_MODE) {
    const response = await fetch(`${BACKEND_URL}${endpoint}`, {
      ...options,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    await applySimulatedDelay();
    return data;
  }

  // In dev mode, try backend first
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 second timeout

    const response = await fetch(`${BACKEND_URL}${endpoint}`, {
      ...options,
      credentials: 'include',
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      // Backend is available and returned successfully
      if (backendAvailable === false) {
        // First successful connection after failure
        console.log('%c✓ Backend Reconnected', 'color: #10b981; font-weight: bold;', `(${BACKEND_URL})`);
      }
      backendAvailable = true;
      lastHealthCheck = Date.now();
      const data = await response.json();
      await applySimulatedDelay();
      return data;
    } else {
      // Backend returned error, fall back to mock
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  } catch (error) {
    // Backend unreachable, use mock data
    if (backendAvailable !== false) {
      // First failure
      console.warn('%c⚠ Backend Unreachable - Falling Back to Mock Data', 'color: #f59e0b; font-weight: bold;', endpoint);
    }
    backendAvailable = false;
    lastHealthCheck = Date.now();

    // Apply simulated delay
    await applySimulatedDelay();
    return mockData;
  }
};

/**
 * Get the configured backend URL
 */
export const getBackendUrl = (): string => {
  return BACKEND_URL;
};

/**
 * Check if we're in dev mode
 */
export const isDevMode = (): boolean => {
  return DEV_MODE;
};
