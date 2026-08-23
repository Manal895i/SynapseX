"""
Unit tests for ADEIP MongoDB Asynchronous Database Support (Motor & PyMongo).
"""
import pytest
from httpx import ASGITransport, AsyncClient
from app.core.config import settings
from app.database.mongodb import MongoDBManager, mongo_manager
from app.main import app


@pytest.mark.asyncio
async def test_mongodb_health_check_payload_structure():
    """Verify MongoDB health check returns expected status and database identifier keys."""
    health_result = await mongo_manager.check_mongo_health()
    assert "status" in health_result
    assert "database" in health_result
    assert health_result["database"] == "mongodb"
    assert health_result["status"] in ["healthy", "unhealthy"]


@pytest.mark.asyncio
async def test_health_database_endpoint():
    """
    Test GET /api/health/database endpoint.
    Must return 200 (healthy) or 503 (unhealthy) with {"status": "...", "database": "mongodb"}.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/health/database")

        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert data["database"] == "mongodb"
        assert data["status"] in ["healthy", "unhealthy"]


def test_mongodb_config_defaults():
    """Verify default MongoDB configuration settings."""
    assert hasattr(settings, "MONGODB_URL")
    assert hasattr(settings, "DATABASE_NAME")
    assert settings.DATABASE_NAME == "adeip_db"
    assert "mongodb://" in settings.MONGODB_URL


@pytest.mark.asyncio
async def test_mongodb_index_structure_setup():
    """Verify index structure setup runs without exceptions."""
    await mongo_manager.init_collection_indexes()
