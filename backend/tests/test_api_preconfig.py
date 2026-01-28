"""
Integration tests for preconfig management endpoints
"""

import pytest


@pytest.mark.integration
class TestPreconfigsByRegionEndpoint:
    """Tests for get preconfigs by region endpoint"""

    def test_preconfigs_requires_auth(self, client):
        """Test preconfigs endpoint requires authentication"""
        response = client.get("/api/preconfig/cbg")
        assert response.status_code == 401

    def test_preconfigs_success(self, client, authenticated_admin):
        """Test admin can get preconfigs for all regions"""
        for region in ["cbg", "dub", "dal"]:
            response = client.get(f"/api/preconfig/{region}")

            assert response.status_code == 200
            data = response.json()

            # Verify response is a list
            assert isinstance(data, list)

            # Verify preconfig structure if any exist
            if data:
                preconfig = data[0]
                assert "dbid" in preconfig
                assert "depot" in preconfig
                assert "appliance_size" in preconfig
                assert "config" in preconfig
                assert "created_at" in preconfig

                # Verify depot is valid
                assert preconfig["depot"] in [1, 2, 4]

                # Verify config is a dict
                assert isinstance(preconfig["config"], dict)

    def test_preconfigs_admin_access(self, client, authenticated_admin):
        """Test admin can access preconfigs"""
        response = client.get("/api/preconfig/cbg")
        assert response.status_code == 200

    def test_preconfigs_invalid_region(self, client, authenticated_user):
        """Test invalid region returns 400"""
        response = client.get("/api/preconfig/invalid")
        assert response.status_code == 400
        assert "Invalid region" in response.json()["detail"]

    def test_preconfigs_case_insensitive(self, client, authenticated_admin):
        """Test region parameter is case insensitive"""
        for region in ["CBG", "Cbg", "cbg"]:
            response = client.get(f"/api/preconfig/{region}")
            assert response.status_code == 200


@pytest.mark.integration
class TestPushPreconfigEndpoint:
    """Tests for push preconfig endpoint"""

    def test_push_preconfig_requires_auth(self, client):
        """Test push preconfig endpoint requires authentication"""
        response = client.post("/api/preconfig/cbg/push")
        assert response.status_code == 401

    def test_push_preconfig_success(self, client, authenticated_admin):
        """Test admin can push preconfig to all regions"""
        for region in ["cbg", "dub", "dal"]:
            response = client.post(f"/api/preconfig/{region}/push")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "success"
            assert "successfully" in data["message"]
            assert region.upper() in data["message"]

    def test_push_preconfig_invalid_region(self, client, authenticated_admin):
        """Test push preconfig rejects invalid region"""
        response = client.post("/api/preconfig/invalid/push")
        assert response.status_code == 400
        assert "Invalid region" in response.json()["detail"]

    def test_push_preconfig_admin_access(self, client, authenticated_admin):
        """Test admin can push preconfig"""
        response = client.post("/api/preconfig/cbg/push")
        assert response.status_code == 200

    def test_push_preconfig_case_insensitive(self, client, authenticated_admin):
        """Test region parameter is case insensitive"""
        for region in ["CBG", "Cbg", "cbg"]:
            response = client.post(f"/api/preconfig/{region}/push")
            assert response.status_code == 200

    def test_push_preconfig_region_in_response(self, client, authenticated_admin):
        """Test region appears correctly in response message"""
        region_map = {"cbg": "CBG", "dub": "DUB", "dal": "DAL"}

        for region_input, region_expected in region_map.items():
            response = client.post(f"/api/preconfig/{region_input}/push")
            assert response.status_code == 200
            data = response.json()
            assert region_expected in data["message"]


@pytest.mark.integration
class TestPushedPreconfigsEndpoint:
    """Tests for get pushed preconfigs endpoint"""

    def test_pushed_preconfigs_requires_auth(self, client):
        """Test pushed preconfigs endpoint requires authentication"""
        response = client.get("/api/preconfig/pushed")
        assert response.status_code == 401

    def test_pushed_preconfigs_success(self, client, authenticated_user):
        """Test authenticated user can get pushed preconfigs"""
        response = client.get("/api/preconfig/pushed")

        assert response.status_code == 200
        data = response.json()

        # Verify response is a list
        assert isinstance(data, list)

        # Verify pushed preconfig structure if any exist
        if data:
            preconfig = data[0]
            assert "dbid" in preconfig
            assert "depot" in preconfig
            assert "config" in preconfig
            assert "last_pushed_at" in preconfig
