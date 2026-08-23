"""
MongoDB Connection Manager & Asynchronous Database Layer for ADEIP.

Uses:
- Motor (AsyncIOMotorClient) for asynchronous database operations
- PyMongo for BSON/command utilities
- Centralized settings from app.core.config
"""
import logging
from typing import Any, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase  # type: ignore # pyrefly: ignore
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError  # type: ignore # pyrefly: ignore

from app.core.config import settings

logger = logging.getLogger("adeip.mongodb")


class MongoDBManager:
    """
    Manages the lifecycle of the asynchronous Motor MongoDB client.
    Ensures a single connection pool is created on startup and reused across requests.
    """
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect_to_mongo(cls):
        """
        Initializes the Motor MongoDB client and verifies connectivity using ping.
        """
        if cls.client is not None:
            logger.debug("[MongoDB] Connection already active.")
            return

        try:
            logger.info(f"[MongoDB] Connecting to MongoDB at {settings.MONGODB_URL} (Database: {settings.DATABASE_NAME})...")
            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=2000,
                connectTimeoutMS=2000,
            )
            cls.db = cls.client[settings.DATABASE_NAME]

            # Verify connection with lightweight ping command
            await cls.client.admin.command("ping")
            logger.info(f"[MongoDB] Connected successfully to MongoDB database '{settings.DATABASE_NAME}'.")

        except (ServerSelectionTimeoutError, ConnectionFailure, Exception) as exc:
            logger.warning(f"[MongoDB] Unable to connect to MongoDB on startup: {exc}. Application will run in degraded mode.")

    @classmethod
    async def close_mongo_connection(cls):
        """
        Closes the MongoDB connection pool cleanly on application shutdown.
        """
        if cls.client is not None:
            logger.info("[MongoDB] Closing MongoDB client connections...")
            cls.client.close()
            cls.client = None
            cls.db = None
            logger.info("[MongoDB] MongoDB connection closed.")

    @classmethod
    def get_database(cls) -> Optional[AsyncIOMotorDatabase]:
        """
        Returns the active Motor database instance.
        """
        if cls.db is None and cls.client is not None:
            cls.db = cls.client[settings.DATABASE_NAME]
        return cls.db

    @classmethod
    async def check_mongo_health(cls) -> Dict[str, Any]:
        """
        Executes a lightweight ping to verify database responsiveness.
        Returns {"status": "healthy", "database": "mongodb"} or {"status": "unhealthy", "database": "mongodb"}.
        """
        if cls.client is None:
            # Attempt to instantiate client if not initialized
            try:
                temp_client = AsyncIOMotorClient(
                    settings.MONGODB_URL,
                    serverSelectionTimeoutMS=2000,
                    connectTimeoutMS=2000,
                )
                await temp_client.admin.command("ping")
                cls.client = temp_client
                cls.db = temp_client[settings.DATABASE_NAME]
                return {
                    "status": "healthy",
                    "database": "mongodb",
                }
            except Exception as exc:
                logger.debug(f"[MongoDB] Health check failed: {exc}")
                return {
                    "status": "unhealthy",
                    "database": "mongodb",
                }

        try:
            await cls.client.admin.command("ping")
            return {
                "status": "healthy",
                "database": "mongodb",
            }
        except Exception as exc:
            logger.debug(f"[MongoDB] Health check ping failed: {exc}")
            return {
                "status": "unhealthy",
                "database": "mongodb",
            }

    @classmethod
    async def init_collection_indexes(cls):
        """
        Structure for future collection indexing.
        Prepares index definitions without creating mock records yet.
        Planned future collections:
        - users
        - cases
        - evidence
        - investigation_events
        - entities
        - correlations
        - findings
        - audit_logs
        - chain_of_custody
        - analysis_jobs
        """
        db = cls.get_database()
        if db is None:
            logger.debug("[MongoDB] Skipping index initialization: database not connected.")
            return

        try:
            # Future index structures:
            # users: [("email", 1), ("username", 1)]
            # cases: [("case_number", 1), ("status", 1)]
            # evidence: [("case_id", 1), ("sha256_hash", 1)]
            # investigation_events: [("case_id", 1), ("timestamp", 1), ("event_type", 1)]
            # entities: [("case_id", 1), ("entity_type", 1), ("normalized_value", 1)]
            # correlations: [("case_id", 1), ("correlation_id", 1)]
            # findings: [("case_id", 1), ("finding_id", 1)]
            # audit_logs: [("timestamp", -1), ("action", 1)]
            # chain_of_custody: [("evidence_id", 1), ("created_at", 1)]
            # analysis_jobs: [("case_id", 1), ("status", 1)]
            logger.debug("[MongoDB] Collection index structure initialized for future use.")
        except Exception as exc:
            logger.warning(f"[MongoDB] Failed to initialize collection indexes: {exc}")


mongo_manager = MongoDBManager
