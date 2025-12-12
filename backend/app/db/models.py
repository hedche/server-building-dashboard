"""
SQLAlchemy ORM Models for Database Tables
Async-compatible models using SQLAlchemy 2.0 style
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, JSON, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func
import enum


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


# Enums
class UserRoleEnum(enum.Enum):
    BUILDER = "builder"
    ENGINEER = "engineer"
    ADMIN = "admin"


# User Model
class UserDB(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)  # Email as ID
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="builder")
    groups: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # Store as JSON array

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<UserDB(email={self.email}, role={self.role})>"


# Preconfig Model
class PreconfigDB(Base):
    __tablename__ = "preconfigs"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    depot: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    appliance_size: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    pushed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Audit
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # User email

    def __repr__(self):
        return f"<PreconfigDB(id={self.id}, depot={self.depot}, size={self.appliance_size})>"


# Build History Model
class BuildHistoryDB(Base):
    __tablename__ = "build_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)

    # Server identification
    hostname: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    rack_id: Mapped[str] = mapped_column(String(50), nullable=False)
    dbid: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    serial_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    machine_type: Mapped[str] = mapped_column(String(50), default="Server")
    bundle: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6 support
    mac_address: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)

    # Build information
    build_server: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    percent_built: Mapped[int] = mapped_column(Integer, default=0)
    build_status: Mapped[str] = mapped_column(String(20), default="installing", nullable=False)
    assigned_status: Mapped[str] = mapped_column(String(20), default="not assigned", nullable=False)

    # Build timeline
    build_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    build_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Assignment
    assigned_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # User email
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Audit (created_at same as build_start)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self):
        return f"<BuildHistoryDB(hostname={self.hostname}, build_server={self.build_server}, status={self.build_status})>"


# Repaired Model (for future frontend use)
class RepairedDB(Base):
    __tablename__ = "repaired"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    date_added: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    serial_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    machine_type: Mapped[str] = mapped_column(String(50), nullable=False)
    mac_address: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)
    hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6 support
    build_server: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    def __repr__(self):
        return f"<RepairedDB(uuid={self.uuid}, serial={self.serial_number}, build_server={self.build_server})>"


# Based Model
class BasedDB(Base):
    __tablename__ = "based"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    date_added: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    serial_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    machine_type: Mapped[str] = mapped_column(String(50), nullable=False)
    rack_id: Mapped[str] = mapped_column(String(50), nullable=False)
    condition: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mac_address: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6 support
    build_server: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    def __repr__(self):
        return f"<BasedDB(uuid={self.uuid}, serial={self.serial_number}, condition={self.condition})>"


# Push Credentials Model
class PushCredsDB(Base):
    __tablename__ = "push_creds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date_added: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    date_modified: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True
    )
    hostname: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    push_type: Mapped[str] = mapped_column(String(50), nullable=False)
    creds_processed_count: Mapped[int] = mapped_column(Integer, default=0)
    creds_pushed_count: Mapped[int] = mapped_column(Integer, default=0)
    build_server: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    def __repr__(self):
        return f"<PushCredsDB(hostname={self.hostname}, status={self.status}, processed={self.creds_processed_count}, pushed={self.creds_pushed_count})>"
