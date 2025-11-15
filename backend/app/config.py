"""
Configuration management using Pydantic Settings
Follows 12-factor app principles for configuration
"""
import os
import json
from typing import List, Optional
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation"""

    # Application
    APP_NAME: str = "Server Building Dashboard"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str
    SESSION_LIFETIME_SECONDS: int = 28800  # 8 hours
    COOKIE_DOMAIN: Optional[str] = None

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"

    # SAML2 Configuration
    SAML_METADATA_PATH: str = "./saml_metadata/idp_metadata.xml"
    SAML_ENTITY_ID: str
    SAML_ACS_URL: str  # Assertion Consumer Service URL
    SAML_SLS_URL: Optional[str] = None  # Single Logout Service URL (optional)

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 100

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "/var/log/server-building-dashboard"

    # Database (optional)
    DATABASE_URL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    def _parse_cors_origins(cls, v):
        """
        Accept either:
         - a JSON array string: ["http://a","http://b"]
         - a comma-separated string: http://a,http://b
         - an actual list from the environment loader
        """
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []
            # try JSON array first
            if s.startswith("[") and s.endswith("]"):
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        return parsed
                except Exception:
                    pass
            # comma-separated fallback
            return [item.strip().strip('"').strip("'") for item in s.split(",") if item.strip()]
        return v

    def get_saml_settings(self) -> dict:
        """
        Generate SAML settings dictionary for python3-saml.
        Returns an empty dict if metadata file is missing.
        """
        if not os.path.exists(self.SAML_METADATA_PATH):
            return {}
        try:
            with open(self.SAML_METADATA_PATH, "r", encoding="utf-8") as f:
                metadata = f.read()
            return {"idp_metadata": metadata}
        except Exception:
            return {}


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Global settings instance
settings = get_settings()