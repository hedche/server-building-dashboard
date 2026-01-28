import React from 'react';
import { Lock, RefreshCw, Clock } from 'lucide-react';
import { RegionLockInfo } from '../types/lock';

interface RegionLockBannerProps {
  lockInfo: RegionLockInfo;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

const RegionLockBanner: React.FC<RegionLockBannerProps> = ({
  lockInfo,
  onRefresh,
  isRefreshing = false,
}) => {
  if (!lockInfo.is_locked) {
    return null;
  }

  const displayName = lockInfo.locked_by_name || lockInfo.locked_by_email || 'Another user';

  // Format the locked_at time
  const formatTime = (isoString?: string): string => {
    if (!isoString) return 'recently';
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return 'recently';
    }
  };

  // Calculate time until expiry
  const getExpiryText = (expiresAt?: string): string => {
    if (!expiresAt) return '';
    try {
      const expiryDate = new Date(expiresAt);
      const now = new Date();
      const diffMs = expiryDate.getTime() - now.getTime();

      if (diffMs <= 0) return 'expired';

      const diffMins = Math.ceil(diffMs / 60000);
      if (diffMins === 1) return 'in 1 minute';
      if (diffMins < 60) return `in ${diffMins} minutes`;

      const diffHours = Math.floor(diffMins / 60);
      const remainingMins = diffMins % 60;
      if (diffHours === 1) {
        return remainingMins > 0 ? `in 1 hour ${remainingMins} min` : 'in 1 hour';
      }
      return `in ${diffHours} hours`;
    } catch {
      return '';
    }
  };

  const lockedAtText = formatTime(lockInfo.locked_at);
  const expiryText = getExpiryText(lockInfo.expires_at);

  return (
    <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3">
          <Lock size={20} className="text-yellow-400 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="text-yellow-400 font-mono font-semibold text-sm">
              Region Locked
            </h3>
            <p className="text-yellow-200 font-mono text-sm mt-1">
              <span className="font-semibold">{displayName}</span> is currently pushing to this region.
            </p>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-xs text-yellow-300/80 font-mono">
              <span className="flex items-center gap-1">
                <Clock size={12} />
                Started at {lockedAtText}
              </span>
              {expiryText && (
                <span>
                  Lock expires {expiryText}
                </span>
              )}
            </div>
          </div>
        </div>
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="flex items-center space-x-1 px-2 py-1 bg-yellow-700/30 hover:bg-yellow-700/50 disabled:bg-yellow-800/20 text-yellow-300 rounded transition-colors text-xs font-mono"
          >
            <RefreshCw size={12} className={isRefreshing ? 'animate-spin' : ''} />
            <span>Check Again</span>
          </button>
        )}
      </div>
    </div>
  );
};

export default RegionLockBanner;
