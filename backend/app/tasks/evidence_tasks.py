"""
Evidence background processing tasks for ADEIP.

Each task:
  - Opens its own DB session (independent from the FastAPI request session).
  - Updates ProcessingJob status at each lifecycle stage.
  - Delegates all actual parsing to ProcessingService.
  - Catches all exceptions and writes safe error messages to the job record.
  - Never leaks stack traces or sensitive data into error_message.
"""
import datetime
import logging
from typing import Optional

from celery import Task  # type: ignore # pyrefly: ignore
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.custody import CustodyAction
from app.models.evidence import Evidence, ProcessingStatus
from app.models.processing_job import JobStatus, ProcessingJob
from app.services.custody_service import CustodyService
from app.tasks.celery_app import celery_app

logger = logging.getLogger("adeip.worker")


def _get_job(db: Session, job_id: int) -> Optional[ProcessingJob]:
    return db.scalars(select(ProcessingJob).where(ProcessingJob.id == job_id)).first()


def _get_evidence(db: Session, evidence_id: int) -> Optional[Evidence]:
    return db.scalars(select(Evidence).where(Evidence.id == evidence_id)).first()


@celery_app.task(
    bind=True,
    name="adeip.tasks.process_evidence",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def process_evidence_task(self: Task, job_id: int, evidence_id: int, user_id: Optional[int] = None) -> dict:
    """
    Background worker task: parse evidence and persist InvestigationEvents.

    Args:
        job_id:      ProcessingJob primary key — used to update status throughout.
        evidence_id: Evidence primary key to process.
        user_id:     ID of the user who triggered processing (for audit trail).

    Returns:
        Dict summary consumed by Celery result backend.
    """
    db: Session = SessionLocal()
    try:
        # ── Phase 1: Mark job as PROCESSING ──────────────────────────────
        job = _get_job(db, job_id)
        if not job:
            logger.error(f"process_evidence_task: job #{job_id} not found in DB. Aborting.")
            return {"status": "aborted", "reason": "job_not_found"}

        job.status = JobStatus.PROCESSING
        job.celery_task_id = self.request.id
        job.started_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()

        # ── Phase 2: Mark evidence as PROCESSING ─────────────────────────
        evidence = _get_evidence(db, evidence_id)
        if not evidence:
            job.status = JobStatus.FAILED
            job.error_message = f"Evidence #{evidence_id} not found during processing."
            job.completed_at = datetime.datetime.now(datetime.timezone.utc)
            db.commit()
            return {"status": "failed", "reason": "evidence_not_found"}

        evidence.processing_status = ProcessingStatus.PROCESSING
        db.commit()

        # Emit WebSocket event: evidence_processing_started
        from app.core.websocket import InvestigationWebSocketEvent, broadcast_case_event
        broadcast_case_event(
            case_id=evidence.case_id,
            event_type=InvestigationWebSocketEvent.EVIDENCE_PROCESSING_STARTED.value,
            data={"evidence_id": evidence_id, "job_id": job_id},
        )

        # ── Phase 3: Delegate to ProcessingService ────────────────────────
        # Import here to avoid circular dependency at module load time
        from app.services.processing_service import ProcessingService

        # Build a minimal user-like object for audit logging
        class _SystemActor:
            id = user_id
            full_name = "Background Worker"
            role = None

        result = ProcessingService.process_evidence(
            db=db,
            evidence_id=evidence_id,
            current_user=_SystemActor(),
            client_ip=None,
        )

        # ── Phase 4: Mark job as COMPLETED ───────────────────────────────
        job = _get_job(db, job_id)  # refresh after ProcessingService committed
        if job:
            job.status = JobStatus.COMPLETED
            job.events_extracted = result.events_extracted
            job.completed_at = datetime.datetime.now(datetime.timezone.utc)
            db.commit()

        # Emit WebSocket events: evidence_processing_completed, new_investigation_event, timeline_updated
        broadcast_case_event(
            case_id=evidence.case_id,
            event_type=InvestigationWebSocketEvent.EVIDENCE_PROCESSING_COMPLETED.value,
            data={"evidence_id": evidence_id, "job_id": job_id, "events_extracted": result.events_extracted},
        )
        broadcast_case_event(
            case_id=evidence.case_id,
            event_type=InvestigationWebSocketEvent.NEW_INVESTIGATION_EVENT.value,
            data={"evidence_id": evidence_id, "count": result.events_extracted},
        )
        broadcast_case_event(
            case_id=evidence.case_id,
            event_type=InvestigationWebSocketEvent.TIMELINE_UPDATED.value,
            data={"evidence_id": evidence_id, "events_added": result.events_extracted},
        )

        logger.info(
            f"process_evidence_task: job #{job_id} completed — "
            f"{result.events_extracted} events extracted from evidence #{evidence_id}."
        )

        return {
            "status": "completed",
            "job_id": job_id,
            "evidence_id": evidence_id,
            "events_extracted": result.events_extracted,
        }

    except Exception as exc:
        # ── Failure path: safe error message, no stack trace exposed ────────
        logger.error(
            f"process_evidence_task: job #{job_id} failed for evidence #{evidence_id}: {exc}",
            exc_info=True,
        )
        safe_error = f"Processing failed: {type(exc).__name__}."

        try:
            db_err: Session = SessionLocal()
            job = _get_job(db_err, job_id)
            evidence = _get_evidence(db_err, evidence_id)
            if job:
                job.status = JobStatus.FAILED
                job.error_message = safe_error
                job.completed_at = datetime.datetime.now(datetime.timezone.utc)
            if evidence:
                evidence.processing_status = ProcessingStatus.FAILED
            db_err.commit()
        except Exception as inner_exc:
            logger.error(f"Failed to record job failure in DB: {inner_exc}")
        finally:
            db_err.close()

        # Retry up to max_retries times with exponential backoff
        raise self.retry(exc=exc, countdown=30 * (self.request.retries + 1))

    finally:
        db.close()
