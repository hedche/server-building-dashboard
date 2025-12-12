"""
Integration tests for server assignment endpoints
"""

import pytest
from unittest.mock import patch, AsyncMock


@pytest.fixture
def mock_assign_request():
    """Provides mock assignment request data"""
    return {
        "serial_number": "SN-TEST-001",
        "hostname": "test-server-001",
        "dbid": "100001",
    }


@pytest.mark.integration
class TestAssignEndpoint:
    """Tests for server assignment endpoint"""

    def test_assign_requires_auth(self, client):
        """Test assign endpoint requires authentication"""
        response = client.post(
            "/api/assign",
            json={
                "serial_number": "SN-001",
                "hostname": "test-server",
                "dbid": "100001",
            },
        )
        assert response.status_code == 401

    @patch("app.routers.assign.asyncio.sleep", new_callable=AsyncMock)
    def test_assign_success(self, mock_sleep, client, authenticated_user):
        """Test authenticated user can assign a server (mock mode fallback)"""
        response = client.post(
            "/api/assign",
            json={
                "serial_number": "SN-TEST-001",
                "hostname": "test-server-001",
                "dbid": "100001",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "assigned successfully" in data["message"]
        assert "test-server-001" in data["message"]

        # Verify sleep was called (simulated processing)
        mock_sleep.assert_called_once_with(2)

    def test_assign_missing_fields(self, client, authenticated_user):
        """Test assign rejects request with missing fields"""
        # Missing serial_number
        response = client.post(
            "/api/assign", json={"hostname": "test-server", "dbid": "100001"}
        )
        assert response.status_code == 422

        # Missing hostname
        response = client.post(
            "/api/assign", json={"serial_number": "SN-001", "dbid": "100001"}
        )
        assert response.status_code == 422

        # Missing dbid
        response = client.post(
            "/api/assign", json={"serial_number": "SN-001", "hostname": "test-server"}
        )
        assert response.status_code == 422

    def test_assign_empty_fields(self, client, authenticated_user):
        """Test assign rejects empty field values (Pydantic validation)"""
        # Empty serial_number - Pydantic min_length=1 validation returns 422
        response = client.post(
            "/api/assign",
            json={"serial_number": "", "hostname": "test-server", "dbid": "100001"},
        )
        assert response.status_code == 422

    def test_assign_invalid_json(self, client, authenticated_user):
        """Test assign rejects invalid JSON"""
        response = client.post(
            "/api/assign", data="not-json", headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    @patch("app.routers.assign.asyncio.sleep", new_callable=AsyncMock)
    def test_assign_admin_access(self, mock_sleep, client, authenticated_admin):
        """Test admin can assign servers"""
        response = client.post(
            "/api/assign",
            json={
                "serial_number": "SN-ADMIN-001",
                "hostname": "admin-server-001",
                "dbid": "200001",
            },
        )
        assert response.status_code == 200

    @patch("app.routers.assign.asyncio.sleep", new_callable=AsyncMock)
    def test_assign_multiple_servers(self, mock_sleep, client, authenticated_user):
        """Test assigning multiple servers sequentially"""
        servers = [
            {"serial_number": "SN-001", "hostname": "server-1", "dbid": "1001"},
            {"serial_number": "SN-002", "hostname": "server-2", "dbid": "1002"},
            {"serial_number": "SN-003", "hostname": "server-3", "dbid": "1003"},
        ]

        for server in servers:
            response = client.post("/api/assign", json=server)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    @patch("app.routers.assign.asyncio.sleep", new_callable=AsyncMock)
    def test_assign_response_structure(
        self, mock_sleep, client, authenticated_user, mock_assign_request
    ):
        """Test assign response has correct structure"""
        response = client.post("/api/assign", json=mock_assign_request)
        data = response.json()

        # Required fields
        assert "status" in data
        assert "message" in data

        # Type checks
        assert isinstance(data["status"], str)
        assert isinstance(data["message"], str)
