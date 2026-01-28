"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from enum import Enum


def _get_valid_depot_ids() -> List[int]:
    """Get valid depot IDs from config.json"""
    from app.routers.config import get_config
    config = get_config()
    regions = config.get("regions", {})
    depot_ids = [r.get("depot_id") for r in regions.values() if r.get("depot_id") is not None]
    if not depot_ids:
        raise ValueError("No depot_ids found in config.json regions configuration")
    return depot_ids


# User Models
class User(BaseModel):
    """User model"""

    id: str
    email: EmailStr
    name: Optional[str] = None
    role: str = "user"
    groups: List[str] = []
    is_admin: bool = False
    allowed_regions: List[str] = Field(default_factory=list)


# Server Models
class ServerStatus(str, Enum):
    """Server status enum"""

    INSTALLING = "installing"
    COMPLETE = "complete"
    FAILED = "failed"


class AssignedStatus(str, Enum):
    """Assigned status enum"""

    ASSIGNED = "assigned"
    NOT_ASSIGNED = "not assigned"


class Server(BaseModel):
    """Server model"""

    rackID: str = Field(..., description="Rack identifier (e.g., '1-E', 'S1-A')")
    hostname: str = Field(..., description="Server hostname")
    dbid: str = Field(..., description="Database ID")
    serial_number: str = Field(..., description="Serial number")
    percent_built: int = Field(
        ..., ge=0, le=100, description="Build completion percentage"
    )
    assigned_status: str = Field(default="not assigned")
    machine_type: str = Field(default="Server")
    status: str = Field(default="installing")

    @validator("percent_built")
    def validate_percent(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("percent_built must be between 0 and 100")
        return v


class ServerDetails(Server):
    """Extended server details model"""

    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    cpu_model: Optional[str] = None
    ram_gb: Optional[int] = None
    storage_gb: Optional[int] = None
    install_start_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None


class BuildStatus(BaseModel):
    """Build status response model - dynamically keyed by region codes from config"""

    class Config:
        extra = "allow"  # Allow dynamic region keys


class BuildHistory(BaseModel):
    """Build history response model (deprecated - use BuildHistoryResponse) - dynamically keyed by region codes"""

    class Config:
        extra = "allow"  # Allow dynamic region keys


class BuildHistoryRecord(BaseModel):
    """Build history record with all database columns"""

    id: int
    uuid: str
    hostname: str
    rack_id: str
    dbid: str
    serial_number: str
    machine_type: str = "Server"
    bundle: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    build_server: str
    percent_built: int = Field(ge=0, le=100, default=0)
    build_status: str = "installing"
    assigned_status: str = "not assigned"
    build_start: datetime
    build_end: Optional[datetime] = None
    assigned_by: Optional[str] = None
    assigned_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BuildHistoryResponse(BaseModel):
    """Build history response for a single region"""

    region: str = Field(..., description="Region code (cbg, dub, dal)")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    servers: List[BuildHistoryRecord] = []


# Preconfig Models
class PreconfigData(BaseModel):
    """Preconfig data model"""

    dbid: str = Field(..., description="Database ID from external preconfig API")
    depot: int = Field(..., ge=1)
    appliance_size: Optional[str] = Field(None, description="Appliance size (small, medium, large)")
    config: Dict[str, Any]
    created_at: datetime
    last_pushed_at: Optional[datetime] = None
    pushed_to: List[str] = Field(default_factory=list, description="Build server hostnames pushed to")

    @validator("depot")
    def validate_depot(cls, v):
        valid_depots = _get_valid_depot_ids()
        if v not in valid_depots:
            raise ValueError(f"depot must be one of {valid_depots}")
        return v

    class Config:
        from_attributes = True


class BuildServerPushResult(BaseModel):
    """Result of push to a single build server"""

    build_server: str = Field(..., description="Build server hostname")
    status: Literal["success", "failed", "skipped"] = Field(..., description="Push status")
    error: Optional[str] = Field(None, description="Error message if failed")
    preconfig_count: int = Field(0, description="Number of preconfigs pushed to this server")


class PushPreconfigResponse(BaseModel):
    """Push preconfig response model with per-server status"""

    status: Literal["success", "partial", "failed"] = Field(..., description="Overall push status")
    message: str = Field(..., description="Human-readable status message")
    results: List[BuildServerPushResult] = Field(default_factory=list, description="Per-server push results")
    pushed_preconfigs: List[PreconfigData] = Field(default_factory=list, description="Preconfigs that were pushed")


class PushPreconfigRequest(BaseModel):
    """Push preconfig request model (deprecated - region now taken from URL path)"""

    depot: int = Field(..., ge=1, description="Depot ID to push to")

    @validator("depot")
    def validate_depot(cls, v):
        valid_depots = _get_valid_depot_ids()
        if v not in valid_depots:
            raise ValueError(f"depot must be one of {valid_depots}")
        return v


# Assignment Models
class AssignRequest(BaseModel):
    """Server assignment request model"""

    serial_number: str = Field(..., min_length=1)
    hostname: str = Field(..., min_length=1)
    dbid: str = Field(..., min_length=1)


class AssignResponse(BaseModel):
    """Server assignment response model"""

    status: str
    message: str


# Generic Response Models
class SuccessResponse(BaseModel):
    """Generic success response"""

    status: str = "success"
    message: str


class ErrorResponse(BaseModel):
    """Generic error response"""

    error: str
    code: int
    detail: Optional[str] = None


# Lock Models
class RegionLockInfo(BaseModel):
    """Information about a region's push lock status"""

    region: str = Field(..., description="Region code (e.g., 'cbg', 'dub', 'dal')")
    is_locked: bool = Field(..., description="Whether the region is currently locked")
    locked_by_email: Optional[str] = Field(None, description="Email of user holding the lock")
    locked_by_name: Optional[str] = Field(None, description="Name of user holding the lock")
    locked_at: Optional[datetime] = Field(None, description="When the lock was acquired")
    expires_at: Optional[datetime] = Field(None, description="When the lock will expire")


class RegionLockResponse(BaseModel):
    """Response containing lock info for all regions"""

    locks: Dict[str, RegionLockInfo] = Field(
        default_factory=dict,
        description="Map of region code to lock info"
    )


class LockConflictDetail(BaseModel):
    """Detail payload for 409 Conflict responses"""

    error: str = Field(default="region_locked", description="Error code")
    message: str = Field(..., description="Human-readable error message")
    lock_info: RegionLockInfo = Field(..., description="Information about the existing lock")
