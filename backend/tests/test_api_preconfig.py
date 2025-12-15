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
        response = client.post("/api/push-preconfig", json={"depot": 1})
        assert response.status_code == 401

    def test_push_preconfig_success(self, client, authenticated_admin):
        """Test admin can push preconfig to all depots"""
        for depot in [1, 2, 4]:
            response = client.post("/api/push-preconfig", json={"depot": depot})

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "success"
            assert "successfully" in data["message"]
            assert str(depot) in data["message"]

    def test_push_preconfig_invalid_depot(self, client, authenticated_user):
        """Test push preconfig rejects invalid depot"""
        # Depot 3 is not valid (only 1, 2, 4 are valid)
        response = client.post("/api/push-preconfig", json={"depot": 3})
        assert response.status_code == 422

        # Depot 0 is not valid
        response = client.post("/api/push-preconfig", json={"depot": 0})
        assert response.status_code == 422

        # Depot 5 is not valid
        response = client.post("/api/push-preconfig", json={"depot": 5})
        assert response.status_code == 422

    def test_push_preconfig_missing_depot(self, client, authenticated_user):
        """Test push preconfig requires depot field"""
        response = client.post("/api/push-preconfig", json={})
        assert response.status_code == 422

    def test_push_preconfig_invalid_depot_type(self, client, authenticated_user):
        """Test push preconfig rejects non-integer depot"""
        response = client.post("/api/push-preconfig", json={"depot": "invalid"})
        assert response.status_code == 422

    def test_push_preconfig_admin_access(self, client, authenticated_admin):
        """Test admin can push preconfig"""
        response = client.post("/api/push-preconfig", json={"depot": 1})
        assert response.status_code == 200

    def test_push_preconfig_depot_region_mapping(self, client, authenticated_admin):
        """Test depot numbers map to correct regions in response"""
        depot_region_map = {1: "CBG", 2: "DUB", 4: "DAL"}

        for depot, region in depot_region_map.items():
            response = client.post("/api/push-preconfig", json={"depot": depot})
            assert response.status_code == 200
            data = response.json()
            assert region in data["message"]


@pytest.mark.integration
class TestPushedPreconfigsEndpoint:
    """Tests for get pushed preconfigs endpoint"""

    def test_pushed_preconfigs_requires_auth(self, client):
        """Test pushed preconfigs endpoint requires authentication"""
        response = client.get("/api/preconfigs/pushed")
        assert response.status_code == 401

    def test_pushed_preconfigs_success(self, client, authenticated_user):
        """Test authenticated user can get pushed preconfigs"""
        response = client.get("/api/preconfigs/pushed")

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
            assert "pushed_at" in preconfig
