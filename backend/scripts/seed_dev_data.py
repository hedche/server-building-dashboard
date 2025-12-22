#!/usr/bin/env python3
"""
Development database seeding script.

Generates realistic test data for the build_history, based, and preconfigs tables.
Intended for local development and testing only - NOT for production use.

Usage:
    python scripts/seed_dev_data.py              # Reset mode (default): clears tables, seeds ~20 rows
    python scripts/seed_dev_data.py --append     # Append mode: add records without clearing
    python scripts/seed_dev_data.py --count 30   # Custom record count
    python scripts/seed_dev_data.py --today-only # Only seed today's data (no historical)
"""
import argparse
import asyncio
import json
import logging
import random
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_config() -> dict:
    """Load config.json with fallback to config.json.example"""
    config_dir = Path(__file__).parent.parent / "config"
    for filename in ["config.json", "config.json.example"]:
        config_path = config_dir / filename
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            continue
        except json.JSONDecodeError:
            continue
    return {}

from sqlalchemy import delete, text
from app.db.database import get_db_context, init_db
from app.db.models import BuildHistoryDB, BasedDB, PreconfigDB

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Region configuration
REGIONS = {
    "cbg": {
        "depot_id": 1,
        "name": "Cambridge",
        "build_server": "cbg-build-01",
        "ip_prefix": "192.168.1",
        "racks": ["1-1", "1-2", "2-1", "2-2"],
    },
    "dub": {
        "depot_id": 2,
        "name": "Dublin",
        "build_server": "dub-build-01",
        "ip_prefix": "192.168.2",
        "racks": ["1-1", "1-2"],
    },
    "dal": {
        "depot_id": 4,
        "name": "Dallas",
        "build_server": "dal-build-01",
        "ip_prefix": "192.168.3",
        "racks": ["1-1", "1-2"],
    },
}

# Configuration options for realistic data
BUILD_STATUSES = ["installing", "complete", "failed"]
BUILD_STATUS_WEIGHTS = [0.4, 0.5, 0.1]  # 40% installing, 50% complete, 10% failed

ASSIGNED_STATUSES = ["assigned", "not assigned"]
MACHINE_TYPES = ["Server", "Storage", "Network"]
BUNDLES = ["standard", "premium", "enterprise", None]
CONDITIONS = ["good", "needs_repair", "pending_qa"]

# Load appliance sizes from config (with fallback)
_config = load_config()
APPLIANCE_SIZES = _config.get("preconfig", {}).get("appliance_sizes", ["small", "medium", "large"])

OS_OPTIONS = ["Ubuntu 22.04 LTS", "Rocky Linux 9", "Debian 12", "RHEL 9"]
CPU_OPTIONS = [
    "2x Intel Xeon Gold 6248R",
    "2x Intel Xeon Gold 6348",
    "2x AMD EPYC 7763",
    "1x Intel Xeon Silver 4314",
]
RAM_OPTIONS = ["64GB DDR4", "128GB DDR4", "256GB DDR4", "512GB DDR4", "1TB DDR4"]
STORAGE_OPTIONS = [
    "4x 1TB NVMe SSD",
    "8x 2TB NVMe SSD",
    "12x 4TB NVMe SSD",
    "16x 8TB NVMe SSD",
]
RAID_OPTIONS = ["RAID 1", "RAID 5", "RAID 10", "RAID 60"]
NETWORK_OPTIONS = ["2x 10Gbps", "2x 25Gbps", "2x 100Gbps", "4x 100Gbps"]

SAMPLE_USERS = [
    "admin@example.com",
    "engineer@example.com",
    "builder@example.com",
]


# =============================================================================
# Helper Functions for Generating Realistic Data
# =============================================================================

def generate_serial() -> str:
    """Generate an 8-digit serial number."""
    return str(random.randint(10000000, 99999999))


def generate_mac() -> str:
    """Generate a random MAC address."""
    return ":".join(f"{random.randint(0, 255):02X}" for _ in range(6))


def generate_ip(region: str, host_num: int) -> str:
    """Generate an IP address based on region subnet."""
    prefix = REGIONS[region]["ip_prefix"]
    return f"{prefix}.{host_num}"


def generate_hostname(region: str, idx: int) -> str:
    """Generate a hostname like 'cbg-srv-001'."""
    return f"{region}-srv-{idx:03d}"


def generate_dbid(region: str, idx: int) -> str:
    """Generate a database ID."""
    depot = REGIONS[region]["depot_id"]
    return f"{depot}{idx:05d}"


def random_datetime_today(hours_ago_max: int = 8) -> datetime:
    """Generate a random datetime within today."""
    now = datetime.utcnow()
    hours_ago = random.uniform(0, hours_ago_max)
    return now - timedelta(hours=hours_ago)


def random_datetime_yesterday() -> datetime:
    """Generate a random datetime from yesterday."""
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)
    hours_offset = random.uniform(0, 24)
    return yesterday.replace(hour=0, minute=0, second=0) + timedelta(hours=hours_offset)


def generate_config() -> dict:
    """Generate a realistic server configuration."""
    return {
        "os": random.choice(OS_OPTIONS),
        "cpu": random.choice(CPU_OPTIONS),
        "ram": random.choice(RAM_OPTIONS),
        "storage": random.choice(STORAGE_OPTIONS),
        "raid": random.choice(RAID_OPTIONS),
        "network": random.choice(NETWORK_OPTIONS),
    }


# =============================================================================
# Data Generation Functions
# =============================================================================

def generate_build_history_records(count: int, include_yesterday: bool = True) -> list[BuildHistoryDB]:
    """Generate build_history records distributed across regions and dates."""
    records = []
    regions = list(REGIONS.keys())

    # Split count between today and yesterday if applicable
    today_count = count if not include_yesterday else int(count * 0.6)
    yesterday_count = count - today_count if include_yesterday else 0

    idx = 1
    used_serials = set()

    # Generate today's records
    for i in range(today_count):
        region = regions[i % len(regions)]
        config = REGIONS[region]

        # Generate unique serial
        serial = generate_serial()
        while serial in used_serials:
            serial = generate_serial()
        used_serials.add(serial)

        # Determine build status and percent
        status = random.choices(BUILD_STATUSES, weights=BUILD_STATUS_WEIGHTS)[0]
        if status == "complete":
            percent = 100
        elif status == "failed":
            percent = random.randint(10, 90)
        else:  # installing
            percent = random.randint(5, 95)

        # Determine assignment (only complete builds can be assigned)
        assigned_status = "not assigned"
        assigned_by = None
        assigned_at = None
        if status == "complete" and random.random() > 0.3:
            assigned_status = "assigned"
            assigned_by = random.choice(SAMPLE_USERS)
            assigned_at = random_datetime_today(2)

        build_start = random_datetime_today(8)
        build_end = None
        if status in ["complete", "failed"]:
            build_end = build_start + timedelta(hours=random.uniform(0.5, 3))

        records.append(BuildHistoryDB(
            uuid=str(uuid.uuid4()),
            hostname=generate_hostname(region, idx),
            rack_id=random.choice(config["racks"]),
            dbid=generate_dbid(region, idx),
            serial_number=serial,
            machine_type=random.choice(MACHINE_TYPES),
            bundle=random.choice(BUNDLES),
            ip_address=generate_ip(region, 100 + idx),
            mac_address=generate_mac(),
            build_server=config["build_server"],
            percent_built=percent,
            build_status=status,
            assigned_status=assigned_status,
            build_start=build_start,
            build_end=build_end,
            assigned_by=assigned_by,
            assigned_at=assigned_at,
        ))
        idx += 1

    # Generate yesterday's records (mostly complete)
    for i in range(yesterday_count):
        region = regions[i % len(regions)]
        config = REGIONS[region]

        serial = generate_serial()
        while serial in used_serials:
            serial = generate_serial()
        used_serials.add(serial)

        # Yesterday's builds are mostly complete
        status = random.choices(["complete", "failed"], weights=[0.85, 0.15])[0]
        percent = 100 if status == "complete" else random.randint(20, 80)

        assigned_status = "not assigned"
        assigned_by = None
        assigned_at = None
        if status == "complete" and random.random() > 0.2:
            assigned_status = "assigned"
            assigned_by = random.choice(SAMPLE_USERS)
            assigned_at = random_datetime_yesterday()

        build_start = random_datetime_yesterday()
        build_end = build_start + timedelta(hours=random.uniform(1, 4))

        records.append(BuildHistoryDB(
            uuid=str(uuid.uuid4()),
            hostname=generate_hostname(region, idx),
            rack_id=random.choice(config["racks"]),
            dbid=generate_dbid(region, idx),
            serial_number=serial,
            machine_type=random.choice(MACHINE_TYPES),
            bundle=random.choice(BUNDLES),
            ip_address=generate_ip(region, 100 + idx),
            mac_address=generate_mac(),
            build_server=config["build_server"],
            percent_built=percent,
            build_status=status,
            assigned_status=assigned_status,
            build_start=build_start,
            build_end=build_end,
            assigned_by=assigned_by,
            assigned_at=assigned_at,
        ))
        idx += 1

    return records


def generate_based_records(count: int, include_yesterday: bool = True) -> list[BasedDB]:
    """Generate based table records."""
    records = []
    regions = list(REGIONS.keys())

    today_count = count if not include_yesterday else int(count * 0.65)
    yesterday_count = count - today_count if include_yesterday else 0

    used_serials = set()

    # Today's records
    for i in range(today_count):
        region = regions[i % len(regions)]
        config = REGIONS[region]

        serial = generate_serial()
        while serial in used_serials:
            serial = generate_serial()
        used_serials.add(serial)

        records.append(BasedDB(
            uuid=str(uuid.uuid4()),
            date_added=random_datetime_today(6),
            serial_number=serial,
            machine_type=random.choice(MACHINE_TYPES),
            rack_id=random.choice(config["racks"]),
            condition=random.choice(CONDITIONS),
            mac_address=generate_mac(),
            ip_address=generate_ip(region, 200 + i),
            build_server=config["build_server"],
        ))

    # Yesterday's records
    for i in range(yesterday_count):
        region = regions[i % len(regions)]
        config = REGIONS[region]

        serial = generate_serial()
        while serial in used_serials:
            serial = generate_serial()
        used_serials.add(serial)

        records.append(BasedDB(
            uuid=str(uuid.uuid4()),
            date_added=random_datetime_yesterday(),
            serial_number=serial,
            machine_type=random.choice(MACHINE_TYPES),
            rack_id=random.choice(config["racks"]),
            condition=random.choice(CONDITIONS),
            mac_address=generate_mac(),
            ip_address=generate_ip(region, 200 + today_count + i),
            build_server=config["build_server"],
        ))

    return records


def generate_preconfig_records(count: int) -> list[PreconfigDB]:
    """Generate preconfig records distributed across depots."""
    records = []
    regions = list(REGIONS.keys())

    for i in range(count):
        region = regions[i % len(regions)]
        config = REGIONS[region]

        # Some preconfigs have been pushed, some haven't
        pushed_at = None
        if random.random() > 0.4:
            pushed_at = random_datetime_today(24)

        records.append(PreconfigDB(
            dbid=f"pre-{region}-{i+1:03d}",
            depot=config["depot_id"],
            appliance_size=random.choice(APPLIANCE_SIZES),
            config=generate_config(),
            created_by=random.choice(SAMPLE_USERS),
            pushed_at=pushed_at,
        ))

    return records


# =============================================================================
# Database Operations
# =============================================================================

async def clear_tables():
    """Clear all seed tables (build_history, based, preconfigs)."""
    async with get_db_context() as db:
        logger.info("Clearing existing data from tables...")

        # Delete in order to avoid foreign key issues
        await db.execute(delete(BuildHistoryDB))
        await db.execute(delete(BasedDB))
        await db.execute(delete(PreconfigDB))
        await db.commit()

        logger.info("Tables cleared successfully")


async def seed_build_history(records: list[BuildHistoryDB]):
    """Insert build_history records."""
    async with get_db_context() as db:
        db.add_all(records)
        await db.commit()
        logger.info(f"Seeded {len(records)} build_history records")


async def seed_based(records: list[BasedDB]):
    """Insert based records."""
    async with get_db_context() as db:
        db.add_all(records)
        await db.commit()
        logger.info(f"Seeded {len(records)} based records")


async def seed_preconfigs(records: list[PreconfigDB]):
    """Insert preconfig records."""
    async with get_db_context() as db:
        db.add_all(records)
        await db.commit()
        logger.info(f"Seeded {len(records)} preconfig records")


# =============================================================================
# Main Entry Point
# =============================================================================

async def main(args):
    """Main seeding function."""
    logger.info("=" * 60)
    logger.info("Development Database Seeder")
    logger.info("=" * 60)

    # Initialize database (creates tables if they don't exist)
    await init_db()

    # Clear tables unless in append mode
    if not args.append:
        await clear_tables()
    else:
        logger.info("Append mode: keeping existing data")

    include_yesterday = not args.today_only

    # Calculate record counts for each table
    # Default total is ~20, distributed roughly: 50% build_history, 30% based, 20% preconfigs
    total = args.count
    build_count = max(1, int(total * 0.5))
    based_count = max(1, int(total * 0.3))
    # Skip preconfigs in append mode (they have fixed IDs and would cause duplicates)
    preconfig_count = 0 if args.append else max(1, total - build_count - based_count)

    if args.append:
        logger.info(f"Generating {build_count} build_history, {based_count} based records (skipping preconfigs in append mode)")
    else:
        logger.info(f"Generating {build_count} build_history, {based_count} based, {preconfig_count} preconfig records")
    if include_yesterday:
        logger.info("Including data from yesterday")

    # Generate and insert records
    build_records = generate_build_history_records(build_count, include_yesterday)
    based_records = generate_based_records(based_count, include_yesterday)

    await seed_build_history(build_records)
    await seed_based(based_records)

    total_created = len(build_records) + len(based_records)
    if preconfig_count > 0:
        preconfig_records = generate_preconfig_records(preconfig_count)
        await seed_preconfigs(preconfig_records)
        total_created += len(preconfig_records)

    logger.info("=" * 60)
    logger.info("Seeding completed successfully!")
    logger.info(f"Total records created: {total_created}")
    logger.info("=" * 60)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Seed the development database with test data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to existing data instead of clearing tables first"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=20,
        help="Total number of records to generate (default: 20)"
    )
    parser.add_argument(
        "--today-only",
        action="store_true",
        help="Only generate records for today (no historical data)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args))
