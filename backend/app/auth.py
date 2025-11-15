"""
SAML2 Authentication module
Handles SAML authentication with Microsoft IDP
"""

from fastapi import HTTPException, status, Request
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.idp_metadata_parser import OneLogin_Saml2_IdPMetadataParser
from typing import Dict, Any
import logging
from datetime import datetime, timedelta

from app.config import settings
from app.models import User

logger = logging.getLogger(__name__)

# In-memory session store (use Redis in production)
_sessions: Dict[str, Dict[str, Any]] = {}


class SAMLAuth:
    """SAML Authentication handler"""

    def __init__(self):
        """Initialize SAML auth with settings"""
        self.saml_settings, self.idp_metadata = settings.get_saml_settings()
        self._parse_idp_metadata()

    def _parse_idp_metadata(self):
        """Parse IDP metadata and merge with settings"""
        try:
            idp_data = OneLogin_Saml2_IdPMetadataParser.parse(self.idp_metadata)

            # Merge IDP data into SAML settings
            if "idp" in idp_data:
                self.saml_settings["idp"] = idp_data["idp"]

            logger.info("IDP metadata parsed successfully")
        except Exception as e:
            logger.error(f"Failed to parse IDP metadata: {str(e)}")
            raise

    def _prepare_request_data(self, request: Request) -> Dict[str, Any]:
        """Prepare request data for python3-saml"""
        return {
            "https": "on" if request.url.scheme == "https" else "off",
            "http_host": request.url.netloc,
            "server_port": request.url.port
            or (443 if request.url.scheme == "https" else 80),
            "script_name": request.url.path,
            "get_data": dict(request.query_params),
            "post_data": {},
        }

    def prepare_auth_request(self, request: Request) -> Dict[str, str]:
        """
        Prepare SAML authentication request
        Returns redirect URL for IDP
        """
        try:
            req_data = self._prepare_request_data(request)
            auth = OneLogin_Saml2_Auth(req_data, self.saml_settings)

            # Generate SSO URL
            sso_url = auth.login()

            logger.info("SAML auth request prepared")
            return {"url": sso_url}

        except Exception as e:
            logger.error(f"Failed to prepare auth request: {str(e)}")
            raise

    def process_saml_response(
        self, saml_response: str, request: Request
    ) -> Dict[str, Any]:
        """
        Process SAML response from IDP
        Returns user data
        """
        try:
            req_data = self._prepare_request_data(request)
            req_data["post_data"] = {"SAMLResponse": saml_response}

            auth = OneLogin_Saml2_Auth(req_data, self.saml_settings)
            auth.process_response()

            errors = auth.get_errors()
            if errors:
                error_reason = auth.get_last_error_reason()
                logger.error(
                    f"SAML authentication errors: {errors}, reason: {error_reason}"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"SAML authentication failed: {error_reason}",
                )

            if not auth.is_authenticated():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="SAML authentication failed",
                )

            # Extract user attributes
            attributes = auth.get_attributes()
            nameid = auth.get_nameid()

            # Map SAML attributes to user data
            user_data = self._extract_user_data(nameid, attributes)

            logger.info(f"User authenticated: {user_data['email']}")
            return user_data

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to process SAML response: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="SAML authentication processing failed",
            )

    def _extract_user_data(self, nameid: str, attributes: Dict) -> Dict[str, Any]:
        """
        Extract user data from SAML attributes
        Handles Microsoft-specific attribute names
        """
        # Microsoft attribute mappings
        email = (
            nameid
            or self._get_attribute(
                attributes,
                "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
            )
            or self._get_attribute(attributes, "email")
            or self._get_attribute(attributes, "mail")
        )

        given_name = self._get_attribute(
            attributes,
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname",
            "givenname",
            "firstname",
        )

        surname = self._get_attribute(
            attributes,
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname",
            "surname",
            "lastname",
        )

        groups = self._get_attribute(
            attributes,
            "http://schemas.microsoft.com/ws/2008/06/identity/claims/groups",
            "groups",
        )

        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email address not found in SAML response",
            )

        # Construct full name
        name_parts = [p for p in [given_name, surname] if p]
        full_name = " ".join(name_parts) if name_parts else None

        return {
            "id": email,  # Use email as unique ID
            "email": email,
            "name": full_name,
            "role": self._determine_role(groups),
            "groups": (
                groups if isinstance(groups, list) else [groups] if groups else []
            ),
        }

    def _get_attribute(self, attributes: Dict, *keys: str) -> Any:
        """
        Get attribute value, trying multiple possible keys
        Handles both single values and lists
        """
        for key in keys:
            if key in attributes:
                value = attributes[key]
                # If it's a list, return first element
                if isinstance(value, list) and len(value) > 0:
                    return value[0]
                return value
        return None

    def _determine_role(self, groups: Any) -> str:
        """
        Determine user role based on group membership
        Customize this based on your organization's groups
        """
        if not groups:
            return "user"

        group_list = groups if isinstance(groups, list) else [groups]

        # Example role mapping - customize for your organization
        admin_groups = ["Dashboard-Admins", "IT-Admins"]
        operator_groups = ["Dashboard-Operators", "IT-Operators"]

        for group in group_list:
            if any(admin_group in str(group) for admin_group in admin_groups):
                return "admin"
            if any(op_group in str(group) for op_group in operator_groups):
                return "operator"

        return "user"

    def store_session(self, session_token: str, user_data: Dict[str, Any]):
        """
        Store session data
        In production, use Redis or similar
        """
        _sessions[session_token] = {
            "user_data": user_data,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow()
            + timedelta(seconds=settings.SESSION_LIFETIME_SECONDS),
        }

        logger.info(f"Session created for user: {user_data['email']}")

    def get_session(self, session_token: str) -> Dict[str, Any] | None:
        """
        Retrieve session data
        Returns None if session doesn't exist or is expired
        """
        if session_token not in _sessions:
            return None

        session = _sessions[session_token]

        # Check expiration
        if datetime.utcnow() > session["expires_at"]:
            del _sessions[session_token]
            logger.info("Session expired and removed")
            return None

        return session["user_data"]

    def delete_session(self, session_token: str):
        """Delete session"""
        if session_token in _sessions:
            del _sessions[session_token]
            logger.info("Session deleted")


# Global SAML auth instance
saml_auth = SAMLAuth()


async def get_current_user(request: Request) -> User:
    """
    Dependency to get current authenticated user
    Validates session token from cookie
    """
    session_token = request.cookies.get("session_token")

    if not session_token:
        logger.warning("No session token in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "SAML"},
        )

    user_data = saml_auth.get_session(session_token)

    if not user_data:
        logger.warning("Invalid or expired session token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid",
            headers={"WWW-Authenticate": "SAML"},
        )

    return User(**user_data)
