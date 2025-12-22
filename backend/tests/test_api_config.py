"""
Integration tests for config endpoints
"""

import pytest


@pytest.mark.integration
class TestConfigEndpoint:
    """Tests for config endpoint"""

    def test_config_is_public(self, client):
        """Test config endpoint is public (no authentication required)"""
        response = client.get("/api/config")
        assert response.status_code == 200

    def test_config_success(self, client):
        """Test authenticated user can get config"""
        response = client.get("/api/config")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "regions" in data
        regions = data["regions"]

        # Verify expected regions exist
        assert "cbg" in regions
        assert "dub" in regions
        assert "dal" in regions

    def test_config_region_structure(self, client):
        """Test config regions have correct structure"""
        response = client.get("/api/config")
        data = response.json()

        for region_code in ["cbg", "dub", "dal"]:
            region = data["regions"][region_code]

            # Verify region has required fields
            assert "build_servers" in region
            assert "racks" in region

            # Verify build_servers is a dict
            assert isinstance(region["build_servers"], dict)

            # Verify racks has normal and small
            assert "normal" in region["racks"]
            assert "small" in region["racks"]

            # Verify racks are lists
            assert isinstance(region["racks"]["normal"], list)
            assert isinstance(region["racks"]["small"], list)

    def test_config_build_server_structure(self, client):
        """Test config build servers have correct structure"""
        response = client.get("/api/config")
        data = response.json()

        for region_code in ["cbg", "dub", "dal"]:
            region = data["regions"][region_code]
            build_servers = region["build_servers"]

            for server_name, server_config in build_servers.items():
                # Verify build server has required fields
                assert "location" in server_config
                assert "build_racks" in server_config

                # Verify build_racks is a list
                assert isinstance(server_config["build_racks"], list)

    def test_config_admin_access(self, client, authenticated_admin):
        """Test admin can access config"""
        response = client.get("/api/config")
        assert response.status_code == 200


@pytest.mark.unit
class TestConfigHelpers:
    """Tests for config helper functions"""

    def test_get_build_servers_for_region(self):
        """Test getting build servers for a region"""
        from app.routers.config import get_build_servers_for_region

        # Test valid region
        cbg_servers = get_build_servers_for_region("cbg")
        assert isinstance(cbg_servers, list)
        # Should have at least one build server (placeholder data)
        assert len(cbg_servers) >= 1

    def test_get_build_servers_for_invalid_region(self):
        """Test getting build servers for invalid region returns empty list"""
        from app.routers.config import get_build_servers_for_region

        servers = get_build_servers_for_region("invalid")
        assert servers == []

    def test_get_region_for_build_server(self):
        """Test getting region for a build server"""
        from app.routers.config import get_region_for_build_server

        # Test known build server from placeholder data
        region = get_region_for_build_server("cbg-build-01")
        assert region == "cbg"

    def test_get_region_for_unknown_build_server(self):
        """Test getting region for unknown build server returns None"""
        from app.routers.config import get_region_for_build_server

        region = get_region_for_build_server("unknown-server")
        assert region is None
