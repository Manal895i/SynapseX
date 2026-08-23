"""
Database Dependencies for ADEIP.

Provides reusable FastAPI dependencies for:
- Asynchronous MongoDB database access (get_mongo_db)
- Asynchronous MongoDB client access (get_mongo_client)
"""
from typing import Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase  # type: ignore # pyrefly: ignore

from app.database.mongodb import mongo_manager


async def get_mongo_db() -> AsyncIOMotorDatabase:
    """
    Reusable FastAPI dependency that yields the active Motor AsyncIOMotorDatabase instance.
    Ensures connection is available or raises HTTPException(503).
    """
    db = mongo_manager.get_database()
    if db is None:
        # Attempt fallback connection if not yet initialized
        await mongo_manager.connect_to_mongo()
        db = mongo_manager.get_database()

    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB service is currently unavailable.",
        )
    return db


async def get_mongo_client() -> AsyncIOMotorClient:
    """
    Reusable FastAPI dependency that yields the active AsyncIOMotorClient connection pool.
    """
    if mongo_manager.client is None:
        await mongo_manager.connect_to_mongo()

    if mongo_manager.client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB client is currently unavailable.",
        )
    return mongo_manager.client
