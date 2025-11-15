"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


# User Models
class User(BaseModel):
    """User model"""
    id: str
    email: EmailStr
    name: Optional[str] = None
    role: str = "user"
    groups: List[str] = []


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
    percent_built: int = Field(..., ge=0, le=100, description="Build completion percentage")
    assigned_status: str = Field(default="not assigned")
    machine_type: str = Field(default="Server")
    status: str = Field(default="installing")
    
    @validator('percent_built')
    def validate_percent(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('percent_built must be between 0 and 100')
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
    """Build status response model"""
    cbg: List[Server] = []
    dub: List[Server] = []
    dal: List[Server] = []


class BuildHistory(BaseModel):
    """Build history response model"""
    cbg: List[Server] = []
    dub: List[Server] = []
    dal: List[Server] = []


# Preconfig Models
class PreconfigData(BaseModel):
    """Preconfig data model"""
    id: str
    depot: int = Field(..., ge=1, le=4)
    config: Dict[str, Any]
    created_at: datetime
    
    @validator('depot')
    def validate_depot(cls, v):
        valid_depots = [1, 2, 4]
        if v not in valid_depots:
            raise ValueError(f'depot must be one of {valid_depots}')
        return v


class PushPreconfigRequest(BaseModel):
    """Push preconfig request model"""
    depot: int = Field(..., ge=1)

    @validator('depot')
    def validate_depot(cls, v):
        valid_depots = [1, 2, 4]
        if v not in valid_depots:
            raise ValueError(f'depot must be one of {valid_depots}')
        return v


class PushPreconfigResponse(BaseModel):
    """Push preconfig response model"""
    status: str
    message: str


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