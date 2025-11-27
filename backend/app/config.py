"""
Configuration management using Pydantic Settings
Follows 12-factor app principles for configuration
"""

import os
import json
from typing import List, Optional, Union
from functools import lru_cache
from urllib.parse import urlparse

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation"""

    # Application
    APP_NAME: str = "Server Building Dashboard"
    ENVIRONMENT: str = "dev"

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
    SAML_ACS_URL: str  # Assertion Consumer Service URL

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

    @property
    def DEBUG(self) -> bool:
        """
        Derive DEBUG mode from LOG_LEVEL.
        Returns True when LOG_LEVEL is set to DEBUG, False otherwise.
        Used for SAML library debug mode and other debug features.
        """
        return self.LOG_LEVEL.upper() == "DEBUG"

    @property
    def SAML_ENTITY_ID(self) -> str:
        """
        Derive SAML Entity ID from SAML_ACS_URL.
        Entity ID is the origin (scheme + host + port) of the ACS URL.
        Example: https://api.example.com/api/auth/callback -> https://api.example.com
        """
        parsed = urlparse(self.SAML_ACS_URL)
        return f"{parsed.scheme}://{parsed.netloc}"

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

        - saml_settings_dict: dict suitable for python3-saml (contains SP config and "idp_metadata")
        - idp_metadata_str_or_none: raw metadata XML string or None if missing/error
        """
        # Build SP (Service Provider) configuration
        saml_settings = {
            "strict": True,
            "debug": self.DEBUG,
            "sp": {
                "entityId": self.SAML_ENTITY_ID,
                "assertionConsumerService": {
                    "url": self.SAML_ACS_URL,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                },
                "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
            },
            "security": {
                "nameIdEncrypted": False,
                "authnRequestsSigned": False,
                "logoutRequestSigned": False,
                "logoutResponseSigned": False,
                "signMetadata": False,
                "wantMessagesSigned": False,
                "wantAssertionsSigned": False,
                "wantAssertionsEncrypted": False,
                "wantNameIdEncrypted": False,
                "requestedAuthnContext": True,
            },
        }

        # Try to load IDP metadata
        if not os.path.exists(self.SAML_METADATA_PATH):
            return saml_settings, None

        try:
            with open(self.SAML_METADATA_PATH, "r", encoding="utf-8") as f:
                metadata = f.read()
            saml_settings["idp_metadata"] = metadata
            return saml_settings, metadata
        except Exception:
            return saml_settings, None


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Global settings instance
settings = get_settings()
