"""
Integration tests for build status and build history endpoints
"""

import pytest
from datetime import date
from app.routers.config import get_config


def get_valid_regions() -> list:
    """Get valid region codes from config.json"""
    config = get_config()
    return list(config.get("regions", {}).keys())


@pytest.mark.integration
class TestBuildStatusEndpoint:
    """Tests for build status endpoint"""

    def test_build_status_requires_auth(self, client):
        """Test build status endpoint requires authentication"""
        response = client.get("/api/build-status")
        assert response.status_code == 401

    def test_build_status_success(self, client, authenticated_admin):
        """Test admin can get build status for all regions"""
        response = client.get("/api/build-status")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure contains all regions from config
        regions = get_valid_regions()
        for region in regions:
            assert region in data
            # Verify each region returns a list
            assert isinstance(data[region], list)

    def test_build_status_server_structure(self, client, authenticated_admin):
        """Test build status servers have correct structure"""
        response = client.get("/api/build-status")
        data = response.json()

        # Check at least one region has servers
        regions = get_valid_regions()
        all_servers = []
        for region in regions:
            all_servers.extend(data.get(region, []))
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
    """Tests for build history endpoint with region-based routing"""

    def test_build_history_requires_auth(self, client):
        """Test build history endpoint requires authentication"""
        regions = get_valid_regions()
        region = regions[0]
        response = client.get(f"/api/build-history/{region}")
        assert response.status_code == 401

    def test_build_history_today_success(self, client, authenticated_user):
        """Test authenticated user can get today's build history for a region"""
        regions = get_valid_regions()
        region = regions[0]
        response = client.get(f"/api/build-history/{region}")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "region" in data
        assert "date" in data
        assert "servers" in data

        # Verify region matches request
        assert data["region"] == region

        # Verify date is today
        assert data["date"] == date.today().isoformat()

        # Verify servers is a list
        assert isinstance(data["servers"], list)

    def test_build_history_with_date_success(
        self, client, authenticated_admin, sample_date
    ):
        """Test admin can get build history for specific date"""
        regions = get_valid_regions()
        region = regions[1] if len(regions) > 1 else regions[0]
        response = client.get(f"/api/build-history/{region}/{sample_date}")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["region"] == region
        assert data["date"] == sample_date
        assert isinstance(data["servers"], list)

    def test_build_history_all_regions(self, client, authenticated_admin):
        """Test admin can access build history for all valid regions"""
        regions = get_valid_regions()
        for region in regions:
            response = client.get(f"/api/build-history/{region}")
            assert response.status_code == 200, f"Failed for region {region}"
            data = response.json()
            assert data["region"] == region

    def test_build_history_invalid_region(self, client, authenticated_user):
        """Test build history rejects invalid region"""
        response = client.get("/api/build-history/invalid")

        assert response.status_code == 400
        data = response.json()
        assert "Invalid region" in data["detail"]

    def test_build_history_invalid_date_format(self, client, authenticated_user):
        """Test build history rejects invalid date format"""
        regions = get_valid_regions()
        region = regions[0]
        response = client.get(f"/api/build-history/{region}/invalid-date")

        assert response.status_code == 400
        data = response.json()
        assert "Invalid date format" in data["detail"]

    def test_build_history_valid_date_formats(self, client, authenticated_user):
        """Test build history accepts valid date formats"""
        regions = get_valid_regions()
        region = regions[0]
        valid_dates = ["2024-01-15", "2024-12-31", "2023-06-01"]

        for date_str in valid_dates:
            response = client.get(f"/api/build-history/{region}/{date_str}")
            assert response.status_code == 200, f"Failed for date {date_str}"

    def test_build_history_invalid_region_with_date(self, client, authenticated_user):
        """Test invalid region still rejected with date parameter"""
        response = client.get("/api/build-history/xyz/2024-01-15")

        assert response.status_code == 400
        assert "Invalid region" in response.json()["detail"]

    def test_build_history_admin_access(self, client, authenticated_admin):
        """Test admin can access build history"""
        regions = get_valid_regions()
        region = regions[0]
        response = client.get(f"/api/build-history/{region}")
        assert response.status_code == 200

    def test_build_history_response_structure(
        self, client, authenticated_user, sample_date
    ):
        """Test build history response has correct structure"""
        regions = get_valid_regions()
        region = regions[0]
        response = client.get(f"/api/build-history/{region}/{sample_date}")
        data = response.json()

        # Required top-level fields
        assert "region" in data
        assert "date" in data
        assert "servers" in data

        # Type checks
        assert isinstance(data["region"], str)
        assert isinstance(data["date"], str)
        assert isinstance(data["servers"], list)
