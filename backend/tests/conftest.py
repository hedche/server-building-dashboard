"""
Shared test fixtures and configuration
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any

from main import app
from app.auth import saml_auth, _sessions
from app.routers.config import get_config


def get_valid_regions() -> list:
    """Get valid region codes from config.json"""
    config = get_config()
    return list(config.get("regions", {}).keys())


def get_builder_email_for_region(region_index: int = 0) -> str:
    """Get a builder email for a specific region index from config"""
    config = get_config()
    permissions = config.get("permissions", {})
    builders = permissions.get("builders", {})
    regions = list(builders.keys())
    if region_index < len(regions):
        region = regions[region_index]
        emails = builders.get(region, [])
        if emails:
            return emails[0]
    return "builder@example.com"


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
        "groups": ["Dashboard-Users"],
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
        "groups": ["Dashboard-Admins"],
    }


@pytest.fixture
def mock_first_region_builder_data() -> Dict[str, Any]:
    """
    Provides mock builder user data for testing (first region from config)
    """
    email = get_builder_email_for_region(0)
    regions = get_valid_regions()
    region = regions[0].upper() if regions else "UNKNOWN"
    return {
        "id": email,
        "email": email,
        "name": f"{region} Builder",
        "role": "user",
        "groups": [],
    }


@pytest.fixture
def mock_unauthorized_user_data() -> Dict[str, Any]:
    """
    Provides mock unauthorized user data for testing (not in permissions)
    """
    return {
        "id": "unauthorized@example.com",
        "email": "unauthorized@example.com",
        "name": "Unauthorized User",
        "role": "user",
        "groups": [],
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


@pytest.fixture
def authenticated_first_region_builder(client, mock_first_region_builder_data) -> str:
    """
    Creates an authenticated builder session for the first region and returns the session token
    """
    session_token = "first-region-builder-session-token-123"
    saml_auth.store_session(session_token, mock_first_region_builder_data)

    # Set the cookie on the client
    client.cookies.set("session_token", session_token)

    yield session_token

    # Cleanup: remove the session
    if session_token in _sessions:
        del _sessions[session_token]


@pytest.fixture
def authenticated_unauthorized_user(client, mock_unauthorized_user_data) -> str:
    """
    Creates an authenticated session for a user not in permissions
    This should result in 403 Forbidden errors
    """
    session_token = "unauthorized-session-token-123"
    saml_auth.store_session(session_token, mock_unauthorized_user_data)

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
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress": [
            "test@example.com"
        ],
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname": ["Test"],
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname": ["User"],
        "http://schemas.microsoft.com/ws/2008/06/identity/claims/groups": [
            "Dashboard-Users"
        ],
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
        "status": "installing",
    }


@pytest.fixture
def mock_build_status_data() -> Dict[str, Any]:
    """
    Provides mock build status data for testing (dynamically keyed by regions from config)
    """
    regions = get_valid_regions()
    data = {}
    for i, region in enumerate(regions):
        if i == 0:
            # First region has a sample server
            data[region] = [
                {
                    "rackID": "1-E",
                    "hostname": f"{region}-srv-001",
                    "dbid": "100001",
                    "serial_number": f"SN-{region.upper()}-001",
                    "percent_built": 55,
                    "assigned_status": "not assigned",
                    "machine_type": "Server",
                    "status": "installing",
                }
            ]
        else:
            data[region] = []
    return data


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
