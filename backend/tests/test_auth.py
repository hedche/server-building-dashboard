"""
Unit and integration tests for authentication
"""

import pytest
from datetime import datetime, timedelta

from app.auth import saml_auth, _sessions, get_current_user
from app.models import User
from fastapi import HTTPException


@pytest.mark.auth
class TestSAMLAuth:
    """Tests for SAML authentication functionality"""

    def test_extract_user_data(self, mock_saml_attributes):
        """Test extracting user data from SAML attributes"""
        user_data = saml_auth._extract_user_data(
            "test@example.com", mock_saml_attributes
        )

        assert user_data["id"] == "test@example.com"
        assert user_data["email"] == "test@example.com"
        assert user_data["name"] == "Test User"
        assert user_data["role"] == "user"
        assert "Dashboard-Users" in user_data["groups"]

    def test_extract_user_data_admin_role(self):
        """Test role determination for admin users"""
        admin_attributes = {
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress": [
                "admin@example.com"
            ],
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname": [
                "Admin"
            ],
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname": ["User"],
            "http://schemas.microsoft.com/ws/2008/06/identity/claims/groups": [
                "Dashboard-Admins"
            ],
        }

        user_data = saml_auth._extract_user_data("admin@example.com", admin_attributes)

        assert user_data["role"] == "admin"
        assert "Dashboard-Admins" in user_data["groups"]

    def test_extract_user_data_operator_role(self):
        """Test role determination for operator users"""
        operator_attributes = {
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress": [
                "operator@example.com"
            ],
            "http://schemas.microsoft.com/ws/2008/06/identity/claims/groups": [
                "Dashboard-Operators"
            ],
        }

        user_data = saml_auth._extract_user_data(
            "operator@example.com", operator_attributes
        )

        assert user_data["role"] == "operator"

    def test_extract_user_data_missing_email(self):
        """Test that missing email raises exception"""
        with pytest.raises(HTTPException) as exc_info:
            saml_auth._extract_user_data("", {})

        assert exc_info.value.status_code == 401
        assert "Email address not found" in str(exc_info.value.detail)

    def test_get_attribute_single_value(self):
        """Test getting single attribute value"""
        attributes = {"key": "value"}
        result = saml_auth._get_attribute(attributes, "key")
        assert result == "value"

    def test_get_attribute_list_value(self):
        """Test getting first element from list attribute"""
        attributes = {"key": ["value1", "value2"]}
        result = saml_auth._get_attribute(attributes, "key")
        assert result == "value1"

    def test_get_attribute_multiple_keys(self):
        """Test trying multiple keys"""
        attributes = {"key2": "value"}
        result = saml_auth._get_attribute(attributes, "key1", "key2", "key3")
        assert result == "value"

    def test_get_attribute_not_found(self):
        """Test getting non-existent attribute"""
        attributes = {}
        result = saml_auth._get_attribute(attributes, "nonexistent")
        assert result is None


@pytest.mark.auth
class TestSessionManagement:
    """Tests for session management"""

    def test_store_session(self, mock_user_data):
        """Test storing a session"""
        token = "test-token-123"
        saml_auth.store_session(token, mock_user_data)

        assert token in _sessions
        assert _sessions[token]["user_data"] == mock_user_data
        assert "created_at" in _sessions[token]
        assert "expires_at" in _sessions[token]

    def test_get_session_valid(self, mock_user_data):
        """Test retrieving a valid session"""
        token = "test-token-456"
        saml_auth.store_session(token, mock_user_data)

        retrieved_data = saml_auth.get_session(token)
        assert retrieved_data == mock_user_data

    def test_get_session_nonexistent(self):
        """Test retrieving non-existent session returns None"""
        result = saml_auth.get_session("nonexistent-token")
        assert result is None

    def test_get_session_expired(self, mock_user_data):
        """Test retrieving expired session returns None"""
        token = "expired-token"

        # Manually create an expired session
        _sessions[token] = {
            "user_data": mock_user_data,
            "created_at": datetime.utcnow() - timedelta(hours=2),
            "expires_at": datetime.utcnow() - timedelta(hours=1),
        }

        result = saml_auth.get_session(token)
        assert result is None
        assert token not in _sessions  # Should be cleaned up

    def test_delete_session(self, mock_user_data):
        """Test deleting a session"""
        token = "delete-token"
        saml_auth.store_session(token, mock_user_data)

        assert token in _sessions
        saml_auth.delete_session(token)
        assert token not in _sessions

    def test_delete_nonexistent_session(self):
        """Test deleting non-existent session doesn't raise error"""
        saml_auth.delete_session("nonexistent-token")  # Should not raise


@pytest.mark.auth
@pytest.mark.integration
class TestGetCurrentUser:
    """Tests for get_current_user dependency"""

    def test_get_current_user_no_token(self, client):
        """Test that missing token raises 401"""
        response = client.get("/api/build-status")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """Test that invalid token raises 401"""
        client.cookies.set("session_token", "invalid-token")
        response = client.get("/api/build-status")
        assert response.status_code == 401

    def test_get_current_user_valid_token(self, client, authenticated_user):
        """Test that valid token allows access"""
        response = client.get("/api/build-status")
        assert response.status_code == 200

    def test_get_current_user_expired_token(self, client, mock_user_data):
        """Test that expired token raises 401"""
        token = "expired-session"

        # Create expired session
        _sessions[token] = {
            "user_data": mock_user_data,
            "created_at": datetime.utcnow() - timedelta(hours=2),
            "expires_at": datetime.utcnow() - timedelta(hours=1),
        }

        client.cookies.set("session_token", token)
        response = client.get("/api/build-status")
        assert response.status_code == 401


@pytest.mark.auth
@pytest.mark.integration
class TestAuthEndpoints:
    """Tests for authentication endpoints"""

    def test_me_endpoint_authenticated(
        self, client, authenticated_user, mock_user_data
    ):
        """Test /me endpoint returns user data when authenticated"""
        response = client.get("/me")

        assert response.status_code == 200
        data = response.json()

        assert data["email"] == mock_user_data["email"]
        assert data["name"] == mock_user_data["name"]
        assert data["role"] == mock_user_data["role"]

    def test_me_endpoint_unauthenticated(self, client):
        """Test /me endpoint requires authentication"""
        response = client.get("/me")
        assert response.status_code == 401

    def test_logout_endpoint_authenticated(self, client, authenticated_user):
        """Test logout endpoint clears session"""
        response = client.post("/logout")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Logged out" in data["message"]

        # Verify cookie is deleted by trying to access protected endpoint
        response = client.get("/api/build-status")
        assert response.status_code == 401

    def test_logout_endpoint_unauthenticated(self, client):
        """Test logout endpoint requires authentication"""
        response = client.post("/logout")
        assert response.status_code == 401
