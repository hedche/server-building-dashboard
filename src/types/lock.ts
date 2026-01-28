export interface RegionLockInfo {
  region: string;
  is_locked: boolean;
  locked_by_email?: string;
  locked_by_name?: string;
  locked_at?: string;
  expires_at?: string;
}

export interface RegionLockResponse {
  locks: Record<string, RegionLockInfo>;
}

export interface LockConflictDetail {
  error: string;
  message: string;
  lock_info: RegionLockInfo;
}
