"""
Integration tests for build status endpoints
"""

import pytest


@pytest.mark.integration
class TestBuildStatusEndpoint:
    """Tests for build status endpoint"""

    def test_build_status_requires_auth(self, client):
        """Test build status endpoint requires authentication"""
        response = client.get("/api/build-status")
        assert response.status_code == 401

    def test_build_status_success(self, client, authenticated_user):
        """Test authenticated user can get build status"""
        response = client.get("/api/build-status")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "cbg" in data
        assert "dub" in data
        assert "dal" in data

        # Verify each region returns a list
        assert isinstance(data["cbg"], list)
        assert isinstance(data["dub"], list)
        assert isinstance(data["dal"], list)

    def test_build_status_server_structure(self, client, authenticated_user):
        """Test build status servers have correct structure"""
        response = client.get("/api/build-status")
        data = response.json()

        # Check at least one region has servers
        all_servers = data["cbg"] + data["dub"] + data["dal"]
        if all_servers:
            server = all_servers[0]

            # Verify server has required fields
            assert "rackID" in server
            assert "hostname" in server
            assert "dbid" in server
            assert "serial_number" in server
            assert "percent_built" in server
            assert "assigned_status" in server
            assert "machine_type" in server
            assert "status" in server

            # Verify percent_built is valid
            assert 0 <= server["percent_built"] <= 100

    def test_build_status_admin_access(self, client, authenticated_admin):
        """Test admin can access build status"""
        response = client.get("/api/build-status")
        assert response.status_code == 200


@pytest.mark.integration
class TestBuildHistoryEndpoint:
    """Tests for build history endpoint"""

    def test_build_history_requires_auth(self, client, sample_date):
        """Test build history endpoint requires authentication"""
        response = client.get(f"/api/build-history/{sample_date}")
        assert response.status_code == 401

    def test_build_history_success(self, client, authenticated_user, sample_date):
        """Test authenticated user can get build history"""
        response = client.get(f"/api/build-history/{sample_date}")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "cbg" in data
        assert "dub" in data
        assert "dal" in data

        # Verify each region returns a list
        assert isinstance(data["cbg"], list)
        assert isinstance(data["dub"], list)
        assert isinstance(data["dal"], list)

    def test_build_history_invalid_date_format(self, client, authenticated_user):
        """Test build history rejects invalid date format"""
        response = client.get("/api/build-history/invalid-date")

        assert response.status_code == 400
        data = response.json()
        assert "Invalid date format" in data["detail"]

    def test_build_history_valid_date_formats(self, client, authenticated_user):
        """Test build history accepts valid date formats"""
        valid_dates = ["2024-01-15", "2024-12-31", "2023-06-01"]

        for date in valid_dates:
            response = client.get(f"/api/build-history/{date}")
            assert response.status_code == 200, f"Failed for date {date}"

    def test_build_history_server_structure(
        self, client, authenticated_user, sample_date
    ):
        """Test build history servers have correct structure"""
        response = client.get(f"/api/build-history/{sample_date}")
        data = response.json()

        # Check at least one region has servers
        all_servers = data["cbg"] + data["dub"] + data["dal"]
        if all_servers:
            server = all_servers[0]

            # Verify server has required fields
            assert "hostname" in server
            assert "percent_built" in server
            assert (
                server["percent_built"] == 100
            ), "Historical builds should be 100% complete"
            assert (
                server["status"] == "complete"
            ), "Historical builds should have 'complete' status"
