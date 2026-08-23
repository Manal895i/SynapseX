from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_db
from app.models.evidence import Evidence
from app.models.processing_job import ProcessingJob
from app.models.user import User
from app.schemas.job import ProcessingJobResponse, ProcessingStatusResponse
from app.services.processing_service import ProcessingService
from app.schemas.processing import ProcessingResultResponse
from fastapi import HTTPException

router = APIRouter(prefix="/evidence", tags=["Background Processing"])


@router.get(
    "/{evidence_id}/processing-status",
    response_model=ProcessingStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the background processing status for an evidence artifact",
)
def get_processing_status(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns the current processing status of an evidence artifact, including:
    - The evidence-level `processing_status` (pending/processing/completed/failed)
    - The most recent background job record (queued/processing/completed/failed)
    - Total number of processing attempts

    Poll this endpoint after upload to track async processing progress.
    """
    evidence = db.scalars(select(Evidence).where(Evidence.id == evidence_id)).first()
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence artifact #{evidence_id} not found.",
        )

    # Load all jobs for this evidence, ordered newest first
    jobs = list(
        db.scalars(
            select(ProcessingJob)
            .where(ProcessingJob.evidence_id == evidence_id)
            .order_by(ProcessingJob.queued_at.desc())
        ).all()
    )

    latest_job_response = None
    if jobs:
        j = jobs[0]
        latest_job_response = ProcessingJobResponse(
            id=j.id,
            celery_task_id=j.celery_task_id,
            evidence_id=j.evidence_id,
            requested_by=j.requested_by,
            requester_name=j.requester.full_name if j.requester else "System",
            status=j.status,
            events_extracted=j.events_extracted,
            error_message=j.error_message,
            queued_at=j.queued_at,
            started_at=j.started_at,
            completed_at=j.completed_at,
        )

    return ProcessingStatusResponse(
        evidence_id=evidence.id,
        evidence_number=evidence.evidence_number,
        original_filename=evidence.original_filename,
        processing_status=evidence.processing_status.value,
        latest_job=latest_job_response,
        total_jobs=len(jobs),
    )


@router.post(
    "/{evidence_id}/process",
    response_model=ProcessingResultResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Manually trigger background evidence processing",
)
def trigger_processing(
    evidence_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Manually enqueues a background processing job for an evidence artifact.
    Useful when automatic queueing failed at upload time, or to reprocess.
    Returns immediately — check `/processing-status` to track progress.
    """
    from app.models.evidence import ProcessingStatus
    from app.models.processing_job import JobStatus, ProcessingJob as PJ
    from app.tasks.evidence_tasks import process_evidence_task

    evidence = db.scalars(select(Evidence).where(Evidence.id == evidence_id)).first()
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence artifact #{evidence_id} not found.",
        )

    if evidence.processing_status == ProcessingStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Evidence is already being processed. Check /processing-status.",
        )

    job = PJ(
        evidence_id=evidence.id,
        requested_by=current_user.id,
        status=JobStatus.QUEUED,
    )
    db.add(job)
    db.flush()

    celery_result = process_evidence_task.delay(
        job_id=job.id,
        evidence_id=evidence.id,
        user_id=current_user.id,
    )
    job.celery_task_id = celery_result.id
    db.commit()

    # Return a lightweight immediate response
    return ProcessingResultResponse(
        evidence_id=evidence.id,
        evidence_number=evidence.evidence_number,
        original_filename=evidence.original_filename,
        processing_status=JobStatus.QUEUED.value,
        parser_used="pending",
        events_extracted=0,
        error=None,
    )
