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
CONFIG_EXAMPLE_PATH = Path(__file__).parent.parent.parent / "config" / "config.json.example"

_config: Dict[str, Any] = {}


def _load_config() -> Dict[str, Any]:
    """Load regions config from JSON file, with fallback to config.json.example"""
    global _config
    if not _config:
        # Try config.json first, then fall back to config.json.example
        for config_path in [CONFIG_PATH, CONFIG_EXAMPLE_PATH]:
            try:
                with open(config_path, "r") as f:
                    _config = json.load(f)
                logger.info(f"Loaded regions config from {config_path}")
                break
            except FileNotFoundError:
                continue
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in config file {config_path}: {e}")
                continue

        if not _config:
            logger.error("No valid config file found (tried config.json and config.json.example)")
            _config = {"regions": {}}
    return _config


def get_config() -> Dict[str, Any]:
    """Get the regions configuration"""
    return _load_config()


def get_appliance_sizes() -> List[str]:
    """Get the list of valid appliance sizes from config"""
    config = get_config()
    preconfig = config.get("preconfig", {})
    return preconfig.get("appliance_sizes", [])


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
