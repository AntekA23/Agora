"""MongoDB indexes for better query performance."""

from motor.motor_asyncio import AsyncIOMotorDatabase


async def create_indexes(db: AsyncIOMotorDatabase) -> None:
    """Create all necessary indexes for the application."""

    # Users collection indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("company_id")

    # Companies collection indexes
    await db.companies.create_index("slug", unique=True)

    # Tasks collection indexes
    await db.tasks.create_index("company_id")
    await db.tasks.create_index("user_id")
    await db.tasks.create_index("status")
    await db.tasks.create_index("department")
    await db.tasks.create_index("agent")
    await db.tasks.create_index("created_at")

    # Compound indexes for common queries
    await db.tasks.create_index([
        ("company_id", 1),
        ("status", 1),
        ("created_at", -1),
    ])
    await db.tasks.create_index([
        ("company_id", 1),
        ("department", 1),
        ("created_at", -1),
    ])
