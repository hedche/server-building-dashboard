"""
Integration tests for server details endpoints
"""
import pytest


@pytest.mark.integration
class TestServerDetailsEndpoint:
    """Tests for server details endpoint"""

    def test_server_details_requires_auth(self, client):
        """Test server details endpoint requires authentication"""
        response = client.get("/api/server-details?hostname=test-server")
        assert response.status_code == 401

    def test_server_details_success(self, client, authenticated_user):
        """Test authenticated user can get server details"""
        response = client.get("/api/server-details?hostname=test-server-001")

        assert response.status_code == 200
        data = response.json()

        # Verify basic server fields
        assert "rackID" in data
        assert "hostname" in data
        assert data["hostname"] == "test-server-001"
        assert "dbid" in data
        assert "serial_number" in data
        assert "percent_built" in data
        assert "assigned_status" in data
        assert "machine_type" in data
        assert "status" in data

        # Verify extended fields
        assert "ip_address" in data
        assert "mac_address" in data
        assert "cpu_model" in data
        assert "ram_gb" in data
        assert "storage_gb" in data
        assert "install_start_time" in data
        assert "estimated_completion" in data
        assert "last_heartbeat" in data

    def test_server_details_missing_hostname(self, client, authenticated_user):
        """Test server details requires hostname parameter"""
        response = client.get("/api/server-details")

        assert response.status_code == 422  # Unprocessable Entity

    def test_server_details_empty_hostname(self, client, authenticated_user):
        """Test server details rejects empty hostname"""
        response = client.get("/api/server-details?hostname=")

        assert response.status_code == 400
        data = response.json()
        assert "Hostname is required" in data["detail"]

    def test_server_details_valid_values(self, client, authenticated_user):
        """Test server details returns valid data types and ranges"""
        response = client.get("/api/server-details?hostname=test-server")
        data = response.json()

        # Verify data types
        assert isinstance(data["percent_built"], int)
        assert isinstance(data["ram_gb"], int)
        assert isinstance(data["storage_gb"], int)

        # Verify ranges
        assert 0 <= data["percent_built"] <= 100
        assert data["ram_gb"] > 0
        assert data["storage_gb"] > 0

    def test_server_details_admin_access(self, client, authenticated_admin):
        """Test admin can access server details"""
        response = client.get("/api/server-details?hostname=test-server")
        assert response.status_code == 200

    def test_server_details_different_hostnames(self, client, authenticated_user):
        """Test server details with different hostnames"""
        hostnames = ["server-1", "cbg-srv-001", "test-machine"]

        for hostname in hostnames:
            response = client.get(f"/api/server-details?hostname={hostname}")
            assert response.status_code == 200
            data = response.json()
            assert data["hostname"] == hostname
