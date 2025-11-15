"""
Configuration management using Pydantic Settings
Follows 12-factor app principles for configuration
"""

import os
import json
from typing import List, Optional, Union, Tuple
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

    # CORS - accept either a list or a comma/JSON string from .env
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

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
         - an actual list provided by the environment loader
        This runs before pydantic's type coercion to avoid dotenv parsing errors.
        """
        if v is None:
            return []
        if isinstance(v, (list, tuple)):
            return [str(x) for x in v]
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []
            if s.startswith("[") and s.endswith("]"):
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        return [str(x) for x in parsed]
                except Exception:
                    pass
            return [
                item.strip().strip('"').strip("'")
                for item in s.split(",")
                if item.strip()
            ]
        return [item.strip() for item in str(v).split(",") if item.strip()]

    def get_saml_settings(self) -> tuple[dict, Optional[str]]:
        """
        Return (saml_settings_dict, idp_metadata_str_or_none).

        - saml_settings_dict: dict suitable for python3-saml (contains "idp_metadata" when present)
        - idp_metadata_str_or_none: raw metadata XML string or None if missing/error
        """
        if not os.path.exists(self.SAML_METADATA_PATH):
            return {}, None
        try:
            with open(self.SAML_METADATA_PATH, "r", encoding="utf-8") as f:
                metadata = f.read()
            saml_settings = {"idp_metadata": metadata}
            return saml_settings, metadata
        except Exception:
            return {}, None


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Global settings instance
settings = get_settings()
