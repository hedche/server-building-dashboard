"""
Permission checking utilities for email-based access control
"""

from typing import Dict, List, Set, Tuple
import logging

logger = logging.getLogger(__name__)


def _load_config() -> dict:
    """Load config.json"""
    from app.routers.config import get_config

    return get_config()


def _get_valid_regions() -> Set[str]:
    """Get valid regions from config.json"""
    config = _load_config()
    regions = config.get("regions", {})
    return set(regions.keys())


def _get_depot_to_region_map() -> Dict[int, str]:
    """Build depot_id to region mapping from config.json"""
    config = _load_config()
    regions = config.get("regions", {})
    depot_map = {}
    for region_code, region_config in regions.items():
        depot_id = region_config.get("depot_id")
        if depot_id is not None:
            depot_map[depot_id] = region_code
    return depot_map


def _get_region_to_depot_map() -> Dict[str, int]:
    """Build region to depot_id mapping from config.json"""
    config = _load_config()
    regions = config.get("regions", {})
    region_map = {}
    for region_code, region_config in regions.items():
        depot_id = region_config.get("depot_id")
        if depot_id is not None:
            region_map[region_code] = depot_id
    return region_map


def _load_permissions() -> dict:
    """Load permissions from config.json"""
    config = _load_config()
    return config.get("permissions", {"admins": [], "builders": {}})


def get_user_permissions(email: str) -> Tuple[bool, List[str]]:
    """
    Determine if user is admin and what regions they can access.

    Args:
        email: User's email address

    Returns:
        Tuple of (is_admin, allowed_regions)
        - is_admin: True if email is in admins list
        - allowed_regions: List of region codes user can access
    """
    permissions = _load_permissions()
    email_lower = email.lower()

    # Check if admin - admins get all regions
    admins = [e.lower() for e in permissions.get("admins", [])]
    if email_lower in admins:
        return True, list(_get_valid_regions())

    # Check builder permissions
    builders = permissions.get("builders", {})
    allowed_regions = []
    for region, emails in builders.items():
        if email_lower in [e.lower() for e in emails]:
            allowed_regions.append(region.lower())

    return False, allowed_regions


def check_user_has_access(email: str) -> Tuple[bool, List[str]]:
    """
    Check if user has any access at all.

    Args:
        email: User's email address

    Returns:
        Tuple of (has_access, allowed_regions)
    """
    is_admin, allowed_regions = get_user_permissions(email)
    has_access = is_admin or len(allowed_regions) > 0
    return has_access, allowed_regions


def check_region_access(email: str, region: str) -> bool:
    """
    Check if user can access a specific region.

    Args:
        email: User's email address
        region: Region code (cbg, dub, dal)

    Returns:
        True if user can access the region
    """
    is_admin, allowed_regions = get_user_permissions(email)
    if is_admin:
        return True
    return region.lower() in [r.lower() for r in allowed_regions]


def check_depot_access(email: str, depot: int) -> bool:
    """
    Check if user can access a specific depot.

    Args:
        email: User's email address
        depot: Depot number (from config.json depot_id)

    Returns:
        True if user can access the depot
    """
    depot_to_region = _get_depot_to_region_map()
    region = depot_to_region.get(depot)
    if not region:
        return False
    return check_region_access(email, region)


def get_depot_for_region(region: str) -> int | None:
    """
    Get depot_id for a region.

    Args:
        region: Region code

    Returns:
        Depot ID or None if not found
    """
    region_to_depot = _get_region_to_depot_map()
    return region_to_depot.get(region.lower())


def get_region_for_depot(depot: int) -> str | None:
    """
    Get region code for a depot_id.

    Args:
        depot: Depot ID

    Returns:
        Region code or None if not found
    """
    depot_to_region = _get_depot_to_region_map()
    return depot_to_region.get(depot)
