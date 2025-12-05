"""
Test database connection script
Verifies MySQL connectivity and displays database information
"""
import asyncio
import sys
from sqlalchemy import text


async def test_connection():
    """Test database connection and display information"""
    try:
        # Import after path setup
        from app.db.database import get_db_context

        print("Testing database connection...")
        print("-" * 50)

        async with get_db_context() as db:
            # Test basic connectivity
            result = await db.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✓ Database connection successful! Test query result: {row[0]}")

            # Get database version
            result = await db.execute(text("SELECT VERSION()"))
            version = result.fetchone()[0]
            print(f"✓ MySQL version: {version}")

            # Get current database name
            result = await db.execute(text("SELECT DATABASE()"))
            db_name = result.fetchone()[0]
            print(f"✓ Current database: {db_name}")

            # Check tables
            result = await db.execute(text("SHOW TABLES"))
            tables = result.fetchall()

            if tables:
                print(f"✓ Tables in database ({len(tables)}):")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("⚠ No tables found in database (run migrations first)")

            # If tables exist, show row counts
            if tables:
                print("\n" + "-" * 50)
                print("Table row counts:")
                for table in tables:
                    table_name = table[0]
                    result = await db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.fetchone()[0]
                    print(f"  - {table_name}: {count} rows")

        print("\n" + "=" * 50)
        print("✓ All database tests passed!")
        print("=" * 50)
        return 0

    except Exception as e:
        print("\n" + "=" * 50)
        print(f"✗ Database connection failed!")
        print("=" * 50)
        print(f"\nError: {e}")
        print("\nTroubleshooting steps:")
        print("1. Ensure MySQL container is running: docker-compose ps")
        print("2. Check DATABASE_URL in .env file")
        print("3. Verify MySQL is healthy: docker-compose logs mysql-dev")
        print("4. Test MySQL directly: docker-compose exec mysql-dev mysql -u dashboard_user -p")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_connection())
    sys.exit(exit_code)
