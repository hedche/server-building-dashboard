"""
Config endpoint for region/rack/build-server mappings
Returns configuration data from config.json
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status

router = APIRouter()
logger = logging.getLogger(__name__)

# Load config at module level
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "config.json"

_config: Dict[str, Any] = {}


def _load_config() -> Dict[str, Any]:
    """Load regions config from JSON file"""
    global _config
    if not _config:
        try:
            with open(CONFIG_PATH, "r") as f:
                _config = json.load(f)
            logger.info(f"Loaded regions config from {CONFIG_PATH}")
        except FileNotFoundError:
            logger.error(f"Config file not found: {CONFIG_PATH}")
            _config = {"regions": {}}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            _config = {"regions": {}}
    return _config


def get_config() -> Dict[str, Any]:
    """Get the regions configuration"""
    return _load_config()


def get_build_servers_for_region(region: str) -> List[str]:
    """
    Get list of build server hostnames for a given region.

    Args:
        region: Region code (cbg, dub, dal)

    Returns:
        List of build server hostnames for the region
    """
    config = get_config()
    regions = config.get("regions", {})
    region_config = regions.get(region, {})
    build_servers = region_config.get("build_servers", {})
    return list(build_servers.keys())


def get_region_for_build_server(build_server: str) -> Optional[str]:
    """
    Find which region a build server belongs to.

    Args:
        build_server: Build server hostname

    Returns:
        Region code (cbg, dub, dal) or None if not found
    """
    config = get_config()
    regions = config.get("regions", {})

    for region_code, region_config in regions.items():
        build_servers = region_config.get("build_servers", {})
        if build_server in build_servers:
            return region_code

    return None


@router.get(
    "/config",
    summary="Get regions configuration",
    description="Returns the full regions configuration including build servers and racks",
)
async def get_regions_config() -> Dict[str, Any]:
    """
    Get the full regions configuration.
    Returns build servers and rack mappings for all regions.
    This endpoint is public and does not require authentication.
    """
    try:
        logger.info("Config requested")
        return get_config()
    except Exception as e:
        logger.error(f"Error fetching config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch configuration",
        )


@router.get(
    "/config/preconfig",
    summary="Get preconfig configuration",
    description="Returns preconfig settings including appliance sizes",
)
async def get_preconfig_config() -> Dict[str, Any]:
    """
    Get preconfig configuration settings.
    Returns appliance sizes and other preconfig-related settings.
    This endpoint is public and does not require authentication.
    """
    try:
        logger.info("Preconfig config requested")
        config = get_config()
        preconfig = config.get("preconfig", {})
        return {
            "appliance_sizes": preconfig.get("appliance_sizes", []),
        }
    except Exception as e:
        logger.error(f"Error fetching preconfig config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch preconfig configuration",
        )
