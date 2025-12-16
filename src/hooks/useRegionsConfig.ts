import { useState, useEffect, useCallback } from 'react';
import { getBackendUrl } from '../utils/api';

export interface BuildServer {
  location: string;
  build_racks: string[];
  preconfigs: string[];
}

export interface RegionConfig {
  depot_id: number;
  name: string;
  build_servers: Record<string, BuildServer>;
  racks: {
    normal: string[];
    small: string[];
  };
}

export interface RegionsConfig {
  permissions: {
    admins: string[];
    builders: Record<string, string[]>;
  };
  preconfig: {
    appliance_sizes: string[];
  };
  regions: Record<string, RegionConfig>;
}

export interface RegionInfo {
  code: string;
  label: string;
  depot_id: number;
}

export const useRegionsConfig = () => {
  const [config, setConfig] = useState<RegionsConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConfig = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const backendUrl = getBackendUrl();
      const response = await fetch(`${backendUrl}/api/config`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setConfig(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch regions config');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  // Derive regions list from config
  const regions: RegionInfo[] = config
    ? Object.entries(config.regions).map(([code, regionConfig]) => ({
        code: code.toUpperCase(),
        label: regionConfig.name,
        depot_id: regionConfig.depot_id,
      }))
    : [];

  // Helper to get depot_id for a region code
  const getDepotForRegion = (regionCode: string): number | undefined => {
    const code = regionCode.toLowerCase();
    return config?.regions[code]?.depot_id;
  };

  // Helper to get region code for a depot_id
  const getRegionForDepot = (depotId: number): string | undefined => {
    if (!config) return undefined;
    for (const [code, regionConfig] of Object.entries(config.regions)) {
      if (regionConfig.depot_id === depotId) {
        return code.toUpperCase();
      }
    }
    return undefined;
  };

  // Helper to get region label (name) for a depot_id
  const getRegionLabelForDepot = (depotId: number): string => {
    if (!config) return 'Unknown';
    for (const regionConfig of Object.values(config.regions)) {
      if (regionConfig.depot_id === depotId) {
        return regionConfig.name;
      }
    }
    return 'Unknown';
  };

  // Get valid depot IDs
  const validDepotIds: number[] = config
    ? Object.values(config.regions).map((r) => r.depot_id)
    : [];

  return {
    config,
    regions,
    validDepotIds,
    isLoading,
    error,
    refetch: fetchConfig,
    getDepotForRegion,
    getRegionForDepot,
    getRegionLabelForDepot,
  };
};
