"""
Database seeding script for development and testing
Populates initial data for Users, Preconfigs, and BuildHistory
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select
import logging

from app.db.database import get_db_context
from app.db.models import UserDB, PreconfigDB, BuildHistoryDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_users():
    """Seed initial users with builder, engineer, and admin roles"""
    async with get_db_context() as db:
        # Check if users already exist
        result = await db.execute(select(UserDB).limit(1))
        if result.scalar_one_or_none():
            logger.info("Users already seeded, skipping...")
            return

        users = [
            UserDB(
                id="admin@example.com",
                email="admin@example.com",
                name="Admin User",
                role="admin",
                groups=["Dashboard-Admins", "IT-Admins"],
            ),
            UserDB(
                id="engineer@example.com",
                email="engineer@example.com",
                name="Engineer User",
                role="engineer",
                groups=["Dashboard-Engineers"],
            ),
            UserDB(
                id="builder@example.com",
                email="builder@example.com",
                name="Builder User",
                role="builder",
                groups=["Dashboard-Builders"],
            ),
        ]

        db.add_all(users)
        await db.commit()
        logger.info(f"Seeded {len(users)} users")


async def seed_preconfigs():
    """Seed initial preconfigs"""
    async with get_db_context() as db:
        result = await db.execute(select(PreconfigDB).limit(1))
        if result.scalar_one_or_none():
            logger.info("Preconfigs already seeded, skipping...")
            return

        preconfigs = [
            PreconfigDB(
                id="pre-cbg-001",
                depot=1,
                appliance_size="medium",
                config={
                    "os": "Ubuntu 22.04 LTS",
                    "cpu": "2x Intel Xeon Gold 6248R",
                    "ram": "128GB DDR4",
                    "storage": "4x 1TB NVMe SSD",
                    "raid": "RAID 10",
                    "network": "2x 25Gbps",
                },
                created_by="admin@example.com",
            ),
            PreconfigDB(
                id="pre-dub-001",
                depot=2,
                appliance_size="large",
                config={
                    "os": "Ubuntu 22.04 LTS",
                    "cpu": "2x Intel Xeon Gold 6348",
                    "ram": "512GB DDR4",
                    "storage": "12x 4TB NVMe SSD",
                    "raid": "RAID 10",
                    "network": "2x 100Gbps",
                },
                created_by="admin@example.com",
            ),
            PreconfigDB(
                id="pre-dal-001",
                depot=4,
                appliance_size="xlarge",
                config={
                    "os": "Rocky Linux 9",
                    "cpu": "2x AMD EPYC 7763",
                    "ram": "1TB DDR4",
                    "storage": "16x 8TB NVMe SSD",
                    "raid": "RAID 60",
                    "network": "4x 100Gbps",
                },
                created_by="admin@example.com",
                pushed_at=datetime.utcnow(),
            ),
        ]

        db.add_all(preconfigs)
        await db.commit()
        logger.info(f"Seeded {len(preconfigs)} preconfigs")


async def seed_build_history():
    """Seed sample build history"""
    async with get_db_context() as db:
        result = await db.execute(select(BuildHistoryDB).limit(1))
        if result.scalar_one_or_none():
            logger.info("Build history already seeded, skipping...")
            return

        now = datetime.utcnow()
        builds = [
            # CBG region - installing
            BuildHistoryDB(
                uuid=str(uuid.uuid4()),
                hostname="cbg-srv-001",
                rack_id="1-E",
                dbid="100001",
                serial_number="SN-CBG-001",
                machine_type="Server",
                bundle="standard",
                ip_address="192.168.1.101",
                mac_address="00:1A:2B:3C:4D:01",
                build_server="cbg-build-01",
                percent_built=55,
                build_status="installing",
                assigned_status="not assigned",
                build_start=now - timedelta(hours=2),
                build_end=None,
            ),
            # CBG region - complete and assigned
            BuildHistoryDB(
                uuid=str(uuid.uuid4()),
                hostname="cbg-srv-002",
                rack_id="2-A",
                dbid="100002",
                serial_number="SN-CBG-002",
                machine_type="Server",
                bundle="premium",
                ip_address="192.168.1.102",
                mac_address="00:1A:2B:3C:4D:02",
                build_server="cbg-build-01",
                percent_built=100,
                build_status="complete",
                assigned_status="assigned",
                build_start=now - timedelta(hours=4),
                build_end=now - timedelta(hours=1),
                assigned_by="engineer@example.com",
                assigned_at=now - timedelta(minutes=30),
            ),
            # DUB region - installing
            BuildHistoryDB(
                uuid=str(uuid.uuid4()),
                hostname="dub-srv-001",
                rack_id="1-B",
                dbid="200001",
                serial_number="SN-DUB-001",
                machine_type="Server",
                bundle="standard",
                ip_address="192.168.2.101",
                mac_address="00:1A:2B:3C:4D:03",
                build_server="dub-build-01",
                percent_built=45,
                build_status="installing",
                assigned_status="not assigned",
                build_start=now - timedelta(hours=1),
                build_end=None,
            ),
            # DAL region - failed
            BuildHistoryDB(
                uuid=str(uuid.uuid4()),
                hostname="dal-srv-001",
                rack_id="1-F",
                dbid="300001",
                serial_number="SN-DAL-001",
                machine_type="Server",
                bundle="standard",
                ip_address="192.168.3.101",
                mac_address="00:1A:2B:3C:4D:04",
                build_server="dal-build-01",
                percent_built=30,
                build_status="failed",
                assigned_status="not assigned",
                build_start=now - timedelta(hours=3),
                build_end=now - timedelta(hours=2, minutes=30),
            ),
            # Historical record (yesterday)
            BuildHistoryDB(
                uuid=str(uuid.uuid4()),
                hostname="cbg-hist-2024-12-03-001",
                rack_id="1-A",
                dbid="400001",
                serial_number="SN-CBG-H001",
                machine_type="Server",
                bundle="premium",
                ip_address="192.168.1.201",
                mac_address="00:1A:2B:3C:4D:05",
                build_server="cbg-build-01",
                percent_built=100,
                build_status="complete",
                assigned_status="assigned",
                build_start=now - timedelta(days=1, hours=4),
                build_end=now - timedelta(days=1, hours=1),
                assigned_by="admin@example.com",
                assigned_at=now - timedelta(days=1, hours=0.5),
            ),
        ]

        db.add_all(builds)
        await db.commit()
        logger.info(f"Seeded {len(builds)} build history records")


async def seed_all():
    """Run all seed functions"""
    logger.info("Starting database seeding...")
    try:
        await seed_users()
        await seed_preconfigs()
        await seed_build_history()
        logger.info("Database seeding completed successfully!")
    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(seed_all())
