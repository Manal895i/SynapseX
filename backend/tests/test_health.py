from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


def test_root_endpoint():
    """Verify root endpoint returns basic platform metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "platform" in data
    assert data["platform"] == settings.PROJECT_NAME
    assert data["environment"] == settings.APP_ENV
    assert data["docs_url"] == "/docs"


def test_health_endpoint():
    """Verify /api/health endpoint returns health status, environment, and DB diagnostics."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["environment"] == settings.APP_ENV
    assert data["version"] == settings.VERSION
    assert "database" in data
    assert "status" in data["database"]
    assert "timestamp" in data

