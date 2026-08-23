"""
Health & Diagnostic Routes for ADEIP.
Provides system health checks and database connectivity diagnostics.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, status  # type: ignore # pyrefly: ignore
from fastapi.responses import JSONResponse  # type: ignore # pyrefly: ignore

from app.core.config import settings
from app.database.mongodb import mongo_manager
from app.database.session import check_db_health

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Overall Application Health Check")
async def get_health():
    """
    Returns application health status, environment mode, current timestamp,
    and relational database connectivity diagnostics.
    """
    db_health = check_db_health()
    overall_status = "healthy" if db_health.get("status") == "connected" else "degraded"

    return {
        "status": overall_status,
        "project": settings.PROJECT_NAME,
        "environment": settings.APP_ENV,
        "version": settings.VERSION,
        "database": db_health,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/health/database",
    summary="MongoDB Database Health Check",
    response_description="MongoDB connection status diagnostics",
)
async def get_database_health():
    """
    Verifies the asynchronous MongoDB connection using a lightweight database command (ping).
    - Returns 200 OK with {"status": "healthy", "database": "mongodb"} when connected.
    - Returns 503 Service Unavailable with {"status": "unhealthy", "database": "mongodb"} when unreachable.
    """
    health_result = await mongo_manager.check_mongo_health()

    if health_result.get("status") == "healthy":
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "healthy",
                "database": "mongodb",
            },
        )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "unhealthy",
            "database": "mongodb",
        },
    )
