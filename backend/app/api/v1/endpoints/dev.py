"""Development/debug endpoints - DO NOT USE IN PRODUCTION."""

from fastapi import APIRouter

from app.api.deps import Database

router = APIRouter(prefix="/dev", tags=["dev"])


@router.delete("/reset-db")
async def reset_database(db: Database) -> dict:
    """
    Reset database - delete all companies and users.
    WARNING: This is for development/testing only!
    """
    # Delete all documents from collections
    companies_result = await db.companies.delete_many({})
    users_result = await db.users.delete_many({})
    tasks_result = await db.tasks.delete_many({})

    return {
        "message": "Database reset successful",
        "deleted": {
            "companies": companies_result.deleted_count,
            "users": users_result.deleted_count,
            "tasks": tasks_result.deleted_count,
        },
    }
