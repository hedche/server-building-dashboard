"""
Tests for permission system
"""

import pytest
from app.routers.config import get_config


def get_valid_regions() -> list:
    """Get valid region codes from config.json"""
    config = get_config()
    return list(config.get("regions", {}).keys())


def get_admin_email() -> str:
    """Get first admin email from config"""
    config = get_config()
    admins = config.get("permissions", {}).get("admins", [])
    return admins[0] if admins else "admin@example.com"


def get_builder_info_for_region(region_index: int = 0) -> tuple:
    """Get builder email and region for a specific region index from config"""
    config = get_config()
    permissions = config.get("permissions", {})
    builders = permissions.get("builders", {})
    regions_list = list(builders.keys())
    if region_index < len(regions_list):
        region = regions_list[region_index]
        emails = builders.get(region, [])
        if emails:
            return emails[0], region
    return "builder@example.com", "unknown"


def get_depot_for_region(region: str) -> int | None:
    """Get depot_id for a region"""
    config = get_config()
    regions = config.get("regions", {})
    return regions.get(region, {}).get("depot_id")


@pytest.mark.unit
class TestPermissionFunctions:
    """Tests for permission checking functions"""

    def test_admin_has_all_regions(self):
        """Admin email should have access to all regions"""
        from app.permissions import get_user_permissions

        admin_email = get_admin_email()
        is_admin, allowed_regions = get_user_permissions(admin_email)
        valid_regions = get_valid_regions()

        assert is_admin is True
        for region in valid_regions:
            assert region in allowed_regions

    def test_builder_has_assigned_region_only(self):
        """Builder should only have access to their assigned region"""
        from app.permissions import get_user_permissions

        builder_email, expected_region = get_builder_info_for_region(0)
        is_admin, allowed_regions = get_user_permissions(builder_email)

        assert is_admin is False
        assert allowed_regions == [expected_region]

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

        admin_email = get_admin_email()
        is_admin1, _ = get_user_permissions(admin_email.upper())
        is_admin2, _ = get_user_permissions(admin_email.title())

        assert is_admin1 is True
        assert is_admin2 is True

    def test_check_region_access_admin(self):
        """Admin should have access to any region"""
        from app.permissions import check_region_access

        admin_email = get_admin_email()
        valid_regions = get_valid_regions()

        for region in valid_regions:
            assert check_region_access(admin_email, region) is True

    def test_check_region_access_builder(self):
        """Builder should only have access to their region"""
        from app.permissions import check_region_access

        builder_email, builder_region = get_builder_info_for_region(0)
        valid_regions = get_valid_regions()

        for region in valid_regions:
            if region == builder_region:
                assert check_region_access(builder_email, region) is True
            else:
                assert check_region_access(builder_email, region) is False

    def test_check_depot_access(self):
        """Depot access should map correctly to region access"""
        from app.permissions import check_depot_access

        admin_email = get_admin_email()
        builder_email, builder_region = get_builder_info_for_region(0)
        valid_regions = get_valid_regions()

        # Admin has access to all depots
        for region in valid_regions:
            depot = get_depot_for_region(region)
            if depot:
                assert check_depot_access(admin_email, depot) is True

        # Builder only has access to their region's depot
        for region in valid_regions:
            depot = get_depot_for_region(region)
            if depot:
                if region == builder_region:
                    assert check_depot_access(builder_email, depot) is True
                else:
                    assert check_depot_access(builder_email, depot) is False


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
        valid_regions = get_valid_regions()
        for region in valid_regions:
            response = client.get(f"/api/preconfig/{region}")
            assert response.status_code == 200, f"Failed for region {region}"

    def test_builder_can_access_own_region(self, client, authenticated_first_region_builder):
        """Builder should be able to access their assigned region"""
        _, builder_region = get_builder_info_for_region(0)
        response = client.get(f"/api/preconfig/{builder_region}")
        assert response.status_code == 200

    def test_builder_cannot_access_other_region(self, client, authenticated_first_region_builder):
        """Builder should not be able to access other regions"""
        _, builder_region = get_builder_info_for_region(0)
        valid_regions = get_valid_regions()

        for region in valid_regions:
            if region != builder_region:
                response = client.get(f"/api/preconfig/{region}")
                assert response.status_code == 403, f"Expected 403 for region {region}"
                assert "do not have permission" in response.json()["detail"].lower()

    def test_build_status_filtered_for_builder(self, client, authenticated_first_region_builder):
        """Build status should only show builder's region"""
        _, builder_region = get_builder_info_for_region(0)
        valid_regions = get_valid_regions()

        response = client.get("/api/build-status")
        assert response.status_code == 200

        data = response.json()
        # Builder should see their region
        assert builder_region in data
        # Other regions should be empty (filtered out)
        for region in valid_regions:
            if region != builder_region:
                assert data.get(region, []) == []

    def test_build_status_shows_all_for_admin(self, client, authenticated_admin):
        """Admin should see all regions in build status"""
        valid_regions = get_valid_regions()

        response = client.get("/api/build-status")
        assert response.status_code == 200

        data = response.json()
        # Admin should see all regions
        for region in valid_regions:
            assert region in data

    def test_me_endpoint_includes_permissions(self, client, authenticated_admin):
        """GET /api/me should include permission fields"""
        valid_regions = get_valid_regions()

        response = client.get("/api/me")
        assert response.status_code == 200

        data = response.json()
        assert "is_admin" in data
        assert "allowed_regions" in data
        assert data["is_admin"] is True
        # Admin should have all regions
        for region in valid_regions:
            assert region in data["allowed_regions"]

    def test_me_endpoint_builder_permissions(self, client, authenticated_first_region_builder):
        """GET /api/me should show correct permissions for builder"""
        _, builder_region = get_builder_info_for_region(0)

        response = client.get("/api/me")
        assert response.status_code == 200

        data = response.json()
        assert data["is_admin"] is False
        assert data["allowed_regions"] == [builder_region]

    def test_config_endpoint_public(self, client):
        """Config endpoint should not require authentication"""
        response = client.get("/api/config")
        assert response.status_code == 200


@pytest.mark.integration
class TestPushPreconfigPermissions:
    """Tests for push-preconfig permission checks"""

    def test_admin_can_push_to_any_region(self, client, authenticated_admin):
        """Admin should be able to push to any region"""
        valid_regions = get_valid_regions()
        for region in valid_regions:
            response = client.post(f"/api/preconfig/{region}/push")
            assert response.status_code == 200, f"Failed for region {region}"

    def test_builder_can_push_to_own_region(self, client, authenticated_first_region_builder):
        """Builder should be able to push to their region"""
        _, builder_region = get_builder_info_for_region(0)
        response = client.post(f"/api/preconfig/{builder_region}/push")
        assert response.status_code == 200

    def test_builder_cannot_push_to_other_region(self, client, authenticated_first_region_builder):
        """Builder should not be able to push to other regions"""
        _, builder_region = get_builder_info_for_region(0)
        valid_regions = get_valid_regions()

        for region in valid_regions:
            if region != builder_region:
                response = client.post(f"/api/preconfig/{region}/push")
                assert response.status_code == 403, f"Expected 403 for region {region}"
                assert "do not have permission" in response.json()["detail"].lower()
