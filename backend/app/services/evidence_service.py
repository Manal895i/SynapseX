import datetime
import hashlib
import json
import os
import random
import string
import uuid
from typing import List, Optional
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.audit import AuditEvent
from app.models.case import InvestigationCase
from app.models.custody import CustodyAction
from app.models.evidence import Evidence, IntegrityStatus, ProcessingStatus
from app.models.user import User, UserRole
from app.schemas.evidence import EvidenceResponse, EvidenceVerificationResponse


class EvidenceService:
    """
    Forensic service managing secure evidence file ingestion, integrity hashing (SHA-256),
    path sanitization, storage isolation, periodic integrity auditing, and chain-of-custody logs.
    """

    @staticmethod
    def _generate_evidence_number(db: Session) -> str:
        """Generates a collision-resistant unique identifier: EVD-YYYY-XXXXX"""
        year = datetime.datetime.now(datetime.timezone.utc).year
        for _ in range(10):
            suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
            candidate = f"EVD-{year}-{suffix}"
            exists = db.scalars(select(Evidence).where(Evidence.evidence_number == candidate)).first()
            if not exists:
                return candidate
        ts = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        return f"EVD-{year}-{ts}"

    @staticmethod
    def _to_evidence_response(evidence: Evidence) -> EvidenceResponse:
        """Converts Evidence model to public response without leaking raw host storage paths."""
        uploader_name = evidence.uploader.full_name if evidence.uploader else None
        return EvidenceResponse(
            id=evidence.id,
            evidence_number=evidence.evidence_number,
            case_id=evidence.case_id,
            original_filename=evidence.original_filename,
            mime_type=evidence.mime_type,
            file_size=evidence.file_size,
            sha256_hash=evidence.sha256_hash,
            processing_status=evidence.processing_status,
            integrity_status=evidence.integrity_status,
            last_verified_at=evidence.last_verified_at,
            uploaded_by=evidence.uploaded_by,
            uploader_name=uploader_name,
            uploaded_at=evidence.uploaded_at,
        )

    @classmethod
    def _sanitize_extension(cls, filename: str) -> str:
        """Extracts and validates lowercased file extension."""
        _, ext = os.path.splitext(filename)
        ext_lower = ext.lower().strip()
        if not ext_lower or ext_lower not in settings.ALLOWED_EVIDENCE_EXTENSIONS:
            allowed = ", ".join(settings.ALLOWED_EVIDENCE_EXTENSIONS)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported or forbidden file type '{ext_lower}'. Allowed forensic formats: {allowed}",
            )
        return ext_lower

    @classmethod
    async def upload_evidence(
        cls,
        db: Session,
        case_id: int,
        file: UploadFile,
        current_user: User,
        client_ip: Optional[str] = None,
    ) -> EvidenceResponse:
        """
        Securely streams an uploaded forensic artifact to isolated storage, computes SHA-256 on the fly,
        validates size limits, and creates the Evidence and AuditEvent records.
        """
        # 1. Authorization check
        case = db.scalars(select(InvestigationCase).where(InvestigationCase.id == case_id)).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Investigation case #{case_id} not found.",
            )

        if current_user.role not in (UserRole.INVESTIGATOR, UserRole.SUPERVISOR, UserRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You lack authorization to upload evidence to this investigation.",
            )

        # 2. Filename and extension sanitization & safety validation
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing original filename in upload payload.",
            )

        from app.core.file_security import safe_join_path, sanitize_filename, validate_file_safety
        original_basename = sanitize_filename(file.filename)
        validate_file_safety(original_basename)
        ext = cls._sanitize_extension(original_basename)

        # 3. Secure storage directory setup
        base_storage_dir = settings.UPLOAD_STORAGE_DIR
        case_storage_dir = safe_join_path(base_storage_dir, f"case_{case_id}")
        os.makedirs(case_storage_dir, exist_ok=True)

        # 4. Generate randomized server-side storage filename
        stored_filename = f"{uuid.uuid4().hex}{ext}"
        destination_path = safe_join_path(case_storage_dir, stored_filename)

        # 5. Stream file to disk and calculate SHA-256 incrementally
        sha256 = hashlib.sha256()
        total_bytes = 0
        chunk_size = 64 * 1024  # 64 KB chunks

        try:
            with open(destination_path, "wb") as f_out:
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    total_bytes += len(chunk)
                    if total_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File exceeds maximum allowed upload limit of {settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024):.0f} MB.",
                        )
                    sha256.update(chunk)
                    f_out.write(chunk)
        except Exception as exc:
            if os.path.exists(destination_path):
                try:
                    os.remove(destination_path)
                except OSError:
                    pass
            if isinstance(exc, HTTPException):
                raise exc
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to securely store evidence artifact: {str(exc)}",
            )

        # 6. Reject empty files
        if total_bytes == 0:
            if os.path.exists(destination_path):
                os.remove(destination_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes). Forensic evidence must contain data.",
            )

        calculated_hash = sha256.hexdigest()
        detected_mime = file.content_type or "application/octet-stream"
        evidence_num = cls._generate_evidence_number(db)

        # 7. Create Evidence record
        evidence_record = Evidence(
            evidence_number=evidence_num,
            case_id=case_id,
            original_filename=original_basename,
            stored_filename=stored_filename,
            storage_path=destination_path,
            mime_type=detected_mime,
            file_size=total_bytes,
            sha256_hash=calculated_hash,
            processing_status=ProcessingStatus.PENDING,
            integrity_status=IntegrityStatus.UNVERIFIED,
            uploaded_by=current_user.id,
        )
        db.add(evidence_record)
        db.flush()

        # 8. Record forensic audit event
        audit_entry = AuditEvent(
            user_id=current_user.id,
            action="EVIDENCE_UPLOAD",
            resource_type="evidence",
            resource_id=str(evidence_record.id),
            details=json.dumps({
                "evidence_number": evidence_num,
                "case_id": case_id,
                "original_filename": original_basename,
                "file_size": total_bytes,
                "sha256_hash": calculated_hash,
                "mime_type": detected_mime,
            }),
            ip_address=client_ip,
        )
        db.add(audit_entry)

        # 9. Append immutable chain-of-custody upload event (deferred import avoids circular dependency)
        from app.services.custody_service import CustodyService
        CustodyService.record_event(
            db=db,
            evidence_id=evidence_record.id,
            action=CustodyAction.EVIDENCE_UPLOADED,
            actor_id=current_user.id,
            details={
                "evidence_number": evidence_num,
                "original_filename": original_basename,
                "sha256_hash": calculated_hash,
                "file_size": total_bytes,
            },
            flush=True,
        )

        db.commit()
        db.refresh(evidence_record)

        # 10. Create a ProcessingJob record and enqueue the Celery background task.
        #     The upload response is returned immediately — processing runs asynchronously.
        try:
            from app.models.processing_job import JobStatus, ProcessingJob
            from app.tasks.evidence_tasks import process_evidence_task

            job = ProcessingJob(
                evidence_id=evidence_record.id,
                requested_by=current_user.id,
                status=JobStatus.QUEUED,
            )
            db.add(job)
            db.flush()

            # Send task to Celery — worker will update the job record as it runs
            task = process_evidence_task.delay(evidence_id=evidence_record.id, job_id=job.id)
            job.celery_task_id = task.id
            db.commit()
            logger.info(f"Enqueued Celery background task {task.id} (job #{job.id}) for Evidence #{evidence_record.id}")

            # Emit real-time WebSocket event
            from app.core.websocket import InvestigationWebSocketEvent, broadcast_case_event
            broadcast_case_event(
                case_id=case_id,
                event_type=InvestigationWebSocketEvent.EVIDENCE_UPLOADED.value,
                data={
                    "evidence_id": evidence_record.id,
                    "evidence_number": evidence_record.evidence_number,
                    "original_filename": evidence_record.original_filename,
                    "file_size": evidence_record.file_size,
                    "sha256_hash": evidence_record.sha256_hash,
                    "processing_job_id": job.id,
                },
            )
            db.commit()
        except Exception as queue_exc:
            # Queueing failure must not fail the upload — evidence is already saved.
            # Log the error; the user can trigger manual processing via POST /process.
            import logging
            logging.getLogger("adeip.upload").warning(
                f"Evidence #{evidence_record.id} saved but failed to queue processing: {queue_exc}"
            )

        return cls._to_evidence_response(evidence_record)

    @classmethod
    def verify_evidence_integrity(
        cls,
        db: Session,
        evidence_id: int,
        current_user: User,
        client_ip: Optional[str] = None,
    ) -> EvidenceVerificationResponse:
        """
        Recalculates cryptographic SHA-256 hash of on-disk file in strictly read-only mode,
        compares with original stored hash, logs audit verification attempt, and updates status.
        """
        evidence = db.scalars(select(Evidence).where(Evidence.id == evidence_id)).first()
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evidence artifact #{evidence_id} not found.",
            )

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        verifier_name = current_user.full_name

        # Case 1: Stored file missing from storage disk
        if not os.path.exists(evidence.storage_path):
            evidence.integrity_status = IntegrityStatus.FILE_MISSING
            evidence.last_verified_at = now_utc

            audit_entry = AuditEvent(
                user_id=current_user.id,
                action="EVIDENCE_INTEGRITY_VERIFY",
                resource_type="evidence",
                resource_id=str(evidence.id),
                details=json.dumps({
                    "result": IntegrityStatus.FILE_MISSING.value,
                    "evidence_number": evidence.evidence_number,
                    "stored_hash": evidence.sha256_hash,
                    "error": "Evidence file not found on disk storage",
                }),
                ip_address=client_ip,
            )
            db.add(audit_entry)

            from app.services.custody_service import CustodyService
            CustodyService.record_event(
                db=db,
                evidence_id=evidence.id,
                action=CustodyAction.INTEGRITY_VERIFIED,
                actor_id=current_user.id,
                details={"result": IntegrityStatus.FILE_MISSING.value, "stored_hash": evidence.sha256_hash},
                flush=True,
            )

            db.commit()
            db.refresh(evidence)

            return EvidenceVerificationResponse(
                evidence_id=evidence.id,
                evidence_number=evidence.evidence_number,
                original_filename=evidence.original_filename,
                integrity_status=IntegrityStatus.FILE_MISSING,
                stored_hash=evidence.sha256_hash,
                computed_hash=None,
                is_valid=False,
                verified_at=now_utc,
                verified_by=current_user.id,
                verifier_name=verifier_name,
                message="Integrity check FAILED: The evidence file is missing from the storage disk.",
            )

        # Case 2: File exists — Recalculate SHA-256 (read-only mode)
        sha256 = hashlib.sha256()
        chunk_size = 64 * 1024

        try:
            with open(evidence.storage_path, "rb") as f_in:
                while True:
                    chunk = f_in.read(chunk_size)
                    if not chunk:
                        break
                    sha256.update(chunk)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read evidence artifact during verification: {str(exc)}",
            )

        computed_hash = sha256.hexdigest()

        # Case 3: Verify match vs mismatch
        if computed_hash.lower() == evidence.sha256_hash.lower():
            evidence.integrity_status = IntegrityStatus.VERIFIED
            is_valid = True
            message = "Integrity VERIFIED: Computed SHA-256 hash matches the original cryptographic signature."
        else:
            evidence.integrity_status = IntegrityStatus.HASH_MISMATCH
            is_valid = False
            message = "CRITICAL ALERT: Evidence hash mismatch! Stored file has been altered or corrupted."

        evidence.last_verified_at = now_utc

        # Record verification audit event
        audit_entry = AuditEvent(
            user_id=current_user.id,
            action="EVIDENCE_INTEGRITY_VERIFY",
            resource_type="evidence",
            resource_id=str(evidence.id),
            details=json.dumps({
                "result": evidence.integrity_status.value,
                "evidence_number": evidence.evidence_number,
                "stored_hash": evidence.sha256_hash,
                "computed_hash": computed_hash,
                "is_match": is_valid,
            }),
            ip_address=client_ip,
        )
        db.add(audit_entry)

        # Append immutable chain-of-custody verification event
        from app.services.custody_service import CustodyService
        CustodyService.record_event(
            db=db,
            evidence_id=evidence.id,
            action=CustodyAction.INTEGRITY_VERIFIED,
            actor_id=current_user.id,
            details={
                "result": evidence.integrity_status.value,
                "stored_hash": evidence.sha256_hash,
                "computed_hash": computed_hash,
                "is_match": is_valid,
            },
            flush=True,
        )

        db.commit()
        db.refresh(evidence)

        return EvidenceVerificationResponse(
            evidence_id=evidence.id,
            evidence_number=evidence.evidence_number,
            original_filename=evidence.original_filename,
            integrity_status=evidence.integrity_status,
            stored_hash=evidence.sha256_hash,
            computed_hash=computed_hash,
            is_valid=is_valid,
            verified_at=now_utc,
            verified_by=current_user.id,
            verifier_name=verifier_name,
            message=message,
        )

    @classmethod
    def list_evidence_for_case(cls, db: Session, case_id: int, current_user: User) -> List[EvidenceResponse]:
        """Retrieves all evidence records registered under a specific case."""
        case = db.scalars(select(InvestigationCase).where(InvestigationCase.id == case_id)).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Investigation case #{case_id} not found.",
            )

        records = db.scalars(
            select(Evidence).where(Evidence.case_id == case_id).order_by(Evidence.uploaded_at.desc())
        ).all()
        return [cls._to_evidence_response(e) for e in records]

    @classmethod
    def get_evidence(cls, db: Session, evidence_id: int, current_user: User) -> EvidenceResponse:
        """Retrieves metadata for a specific evidence item."""
        evidence = db.scalars(select(Evidence).where(Evidence.id == evidence_id)).first()
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evidence artifact #{evidence_id} not found.",
            )
        return cls._to_evidence_response(evidence)
