"""
Tests for permission system
"""

import pytest


@pytest.mark.unit
class TestPermissionFunctions:
    """Tests for permission checking functions"""

    def test_admin_has_all_regions(self):
        """Admin email should have access to all regions"""
        from app.permissions import get_user_permissions

        is_admin, allowed_regions = get_user_permissions("admin@example.com")

        assert is_admin is True
        assert "cbg" in allowed_regions
        assert "dub" in allowed_regions
        assert "dal" in allowed_regions

    def test_builder_has_assigned_region_only(self):
        """Builder should only have access to their assigned region"""
        from app.permissions import get_user_permissions

        is_admin, allowed_regions = get_user_permissions("cbg-builder@example.com")

        assert is_admin is False
        assert allowed_regions == ["cbg"]

    def test_unknown_user_has_no_access(self):
        """User not in any permission list should have no access"""
        from app.permissions import get_user_permissions, check_user_has_access

        is_admin, allowed_regions = get_user_permissions("unknown@example.com")

        assert is_admin is False
        assert allowed_regions == []

        has_access, _ = check_user_has_access("unknown@example.com")
        assert has_access is False

    def test_case_insensitive_email(self):
        """Email matching should be case insensitive"""
        from app.permissions import get_user_permissions

        is_admin1, _ = get_user_permissions("ADMIN@EXAMPLE.COM")
        is_admin2, _ = get_user_permissions("Admin@Example.Com")

        assert is_admin1 is True
        assert is_admin2 is True

    def test_check_region_access_admin(self):
        """Admin should have access to any region"""
        from app.permissions import check_region_access

        assert check_region_access("admin@example.com", "cbg") is True
        assert check_region_access("admin@example.com", "dub") is True
        assert check_region_access("admin@example.com", "dal") is True

    def test_check_region_access_builder(self):
        """Builder should only have access to their region"""
        from app.permissions import check_region_access

        assert check_region_access("cbg-builder@example.com", "cbg") is True
        assert check_region_access("cbg-builder@example.com", "dub") is False
        assert check_region_access("cbg-builder@example.com", "dal") is False

    def test_check_depot_access(self):
        """Depot access should map correctly to region access"""
        from app.permissions import check_depot_access

        # Admin has access to all depots
        assert check_depot_access("admin@example.com", 1) is True  # cbg
        assert check_depot_access("admin@example.com", 2) is True  # dub
        assert check_depot_access("admin@example.com", 4) is True  # dal

        # CBG builder only has access to depot 1 (cbg)
        assert check_depot_access("cbg-builder@example.com", 1) is True
        assert check_depot_access("cbg-builder@example.com", 2) is False
        assert check_depot_access("cbg-builder@example.com", 4) is False


@pytest.mark.integration
class TestPermissionEndpoints:
    """Integration tests for permission checks on endpoints"""

    def test_unauthorized_user_denied(self, client, authenticated_unauthorized_user):
        """User not in permissions should get 403"""
        response = client.get("/api/build-status")
        assert response.status_code == 403
        assert "not authorized" in response.json()["detail"].lower()

    def test_admin_can_access_all_regions(self, client, authenticated_admin):
        """Admin should be able to access all regions"""
        # Access CBG
        response = client.get("/api/preconfig/cbg")
        assert response.status_code == 200

        # Access DUB
        response = client.get("/api/preconfig/dub")
        assert response.status_code == 200

        # Access DAL
        response = client.get("/api/preconfig/dal")
        assert response.status_code == 200

    def test_builder_can_access_own_region(self, client, authenticated_cbg_builder):
        """Builder should be able to access their assigned region"""
        response = client.get("/api/preconfig/cbg")
        assert response.status_code == 200

    def test_builder_cannot_access_other_region(self, client, authenticated_cbg_builder):
        """Builder should not be able to access other regions"""
        response = client.get("/api/preconfig/dub")
        assert response.status_code == 403
        assert "do not have permission" in response.json()["detail"].lower()

        response = client.get("/api/preconfig/dal")
        assert response.status_code == 403

    def test_build_status_filtered_for_builder(self, client, authenticated_cbg_builder):
        """Build status should only show builder's region"""
        response = client.get("/api/build-status")
        assert response.status_code == 200

        data = response.json()
        # Builder should only see CBG
        assert "cbg" in data
        # Other regions should be empty (filtered out)
        assert data.get("dub", []) == []
        assert data.get("dal", []) == []

    def test_build_status_shows_all_for_admin(self, client, authenticated_admin):
        """Admin should see all regions in build status"""
        response = client.get("/api/build-status")
        assert response.status_code == 200

        data = response.json()
        # Admin should see all regions
        assert "cbg" in data
        assert "dub" in data
        assert "dal" in data

    def test_me_endpoint_includes_permissions(self, client, authenticated_admin):
        """GET /api/me should include permission fields"""
        response = client.get("/api/me")
        assert response.status_code == 200

        data = response.json()
        assert "is_admin" in data
        assert "allowed_regions" in data
        assert data["is_admin"] is True
        assert "cbg" in data["allowed_regions"]

    def test_me_endpoint_builder_permissions(self, client, authenticated_cbg_builder):
        """GET /api/me should show correct permissions for builder"""
        response = client.get("/api/me")
        assert response.status_code == 200

        data = response.json()
        assert data["is_admin"] is False
        assert data["allowed_regions"] == ["cbg"]

    def test_config_endpoint_public(self, client):
        """Config endpoint should not require authentication"""
        response = client.get("/api/config")
        assert response.status_code == 200


@pytest.mark.integration
class TestPushPreconfigPermissions:
    """Tests for push-preconfig permission checks"""

    def test_admin_can_push_to_any_depot(self, client, authenticated_admin):
        """Admin should be able to push to any depot"""
        response = client.post("/api/push-preconfig", json={"depot": 1})
        assert response.status_code == 200

        response = client.post("/api/push-preconfig", json={"depot": 2})
        assert response.status_code == 200

    def test_builder_can_push_to_own_depot(self, client, authenticated_cbg_builder):
        """Builder should be able to push to their depot"""
        response = client.post("/api/push-preconfig", json={"depot": 1})
        assert response.status_code == 200

    def test_builder_cannot_push_to_other_depot(self, client, authenticated_cbg_builder):
        """Builder should not be able to push to other depots"""
        response = client.post("/api/push-preconfig", json={"depot": 2})
        assert response.status_code == 403
        assert "do not have permission" in response.json()["detail"].lower()
