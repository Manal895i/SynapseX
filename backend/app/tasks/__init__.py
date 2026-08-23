"""
Tasks package for ADEIP background processing.

Exports the celery_app instance so it can be referenced by:
  - The Celery CLI: celery -A app.tasks worker
  - FastAPI startup (optional health check)
  - Tests
"""
from app.tasks.celery_app import celery_app
from app.tasks.evidence_tasks import process_evidence_task

__all__ = ["celery_app", "process_evidence_task"]
