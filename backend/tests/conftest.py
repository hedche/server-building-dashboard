"""
Shared test fixtures and configuration
"""
import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any
from datetime import datetime

from main import app
from app.auth import saml_auth, _sessions
from app.models import User


@pytest.fixture(scope="session")
def test_app():
    """
    Provides the FastAPI application instance
    """
    return app


@pytest.fixture
def client(test_app):
    """
    Provides a test client for making requests
    """
    return TestClient(test_app)


@pytest.fixture
def mock_user_data() -> Dict[str, Any]:
    """
    Provides mock user data for testing
    """
    return {
        "id": "test@example.com",
        "email": "test@example.com",
        "name": "Test User",
        "role": "user",
        "groups": ["Dashboard-Users"]
    }


@pytest.fixture
def mock_admin_user_data() -> Dict[str, Any]:
    """
    Provides mock admin user data for testing
    """
    return {
        "id": "admin@example.com",
        "email": "admin@example.com",
        "name": "Admin User",
        "role": "admin",
        "groups": ["Dashboard-Admins"]
    }


@pytest.fixture
def authenticated_user(client, mock_user_data) -> str:
    """
    Creates an authenticated session and returns the session token
    """
    session_token = "test-session-token-123"
    saml_auth.store_session(session_token, mock_user_data)

    # Set the cookie on the client
    client.cookies.set("session_token", session_token)

    yield session_token

    # Cleanup: remove the session
    if session_token in _sessions:
        del _sessions[session_token]


@pytest.fixture
def authenticated_admin(client, mock_admin_user_data) -> str:
    """
    Creates an authenticated admin session and returns the session token
    """
    session_token = "admin-session-token-123"
    saml_auth.store_session(session_token, mock_admin_user_data)

    # Set the cookie on the client
    client.cookies.set("session_token", session_token)

    yield session_token

    # Cleanup: remove the session
    if session_token in _sessions:
        del _sessions[session_token]


@pytest.fixture(autouse=True)
def clear_sessions():
    """
    Automatically clear sessions before and after each test
    """
    _sessions.clear()
    yield
    _sessions.clear()


@pytest.fixture
def mock_saml_attributes() -> Dict[str, Any]:
    """
    Provides mock SAML attributes for testing
    """
    return {
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress": ["test@example.com"],
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname": ["Test"],
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname": ["User"],
        "http://schemas.microsoft.com/ws/2008/06/identity/claims/groups": ["Dashboard-Users"]
    }


@pytest.fixture
def mock_server_data() -> Dict[str, Any]:
    """
    Provides mock server data for testing
    """
    return {
        "rackID": "1-E",
        "hostname": "test-server-001",
        "dbid": "100001",
        "serial_number": "SN-TEST-001",
        "percent_built": 75,
        "assigned_status": "not assigned",
        "machine_type": "Server",
        "status": "installing"
    }


@pytest.fixture
def mock_build_status_data() -> Dict[str, Any]:
    """
    Provides mock build status data for testing
    """
    return {
        "cbg": [
            {
                "rackID": "1-E",
                "hostname": "cbg-srv-001",
                "dbid": "100001",
                "serial_number": "SN-CBG-001",
                "percent_built": 55,
                "assigned_status": "not assigned",
                "machine_type": "Server",
                "status": "installing"
            }
        ],
        "dub": [],
        "dal": []
    }


@pytest.fixture
def sample_date() -> str:
    """
    Provides a sample date string for testing
    """
    return "2024-01-15"


@pytest.fixture
def invalid_date() -> str:
    """
    Provides an invalid date string for testing
    """
    return "invalid-date"


# Performance tracking fixtures
@pytest.fixture
def track_performance():
    """
    Track test execution time for performance testing
    """
    import time
    start = time.time()
    yield
    duration = time.time() - start
    if duration > 1.0:
        pytest.fail(f"Test took too long: {duration:.2f}s")
