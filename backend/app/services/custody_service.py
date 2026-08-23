import json
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.custody import ChainOfCustody, CustodyAction
from app.models.evidence import Evidence
from app.models.user import UserRole
from app.schemas.custody import ChainOfCustodyResponse, CustodyEventResponse


class CustodyService:
    """
    Service for recording and retrieving chain-of-custody events for forensic evidence.

    Design principle:
    - Events are append-only at the application layer.
    - No UPDATE or DELETE operations are exposed to any user role.
    - Only admins can view the full audit trail; other roles can view events for their authorized evidence.
    """

    @staticmethod
    def _to_event_response(event: ChainOfCustody) -> CustodyEventResponse:
        actor_name = event.actor.full_name if event.actor else "System"
        return CustodyEventResponse(
            id=event.id,
            evidence_id=event.evidence_id,
            actor_id=event.actor_id,
            actor_name=actor_name,
            action=event.action,
            details=event.details,
            created_at=event.created_at,
        )

    @classmethod
    def record_event(
        cls,
        db: Session,
        evidence_id: int,
        action: CustodyAction,
        actor_id: Optional[int] = None,
        details: Optional[dict] = None,
        flush: bool = False,
    ) -> ChainOfCustody:
        """
        Appends a new, immutable chain-of-custody event for a given evidence artifact.
        Can be called from any service (upload, verification, analysis, report).

        Args:
            db:          Active database session.
            evidence_id: ID of the evidence artifact this event belongs to.
            action:      Discrete custody action from the CustodyAction enum.
            actor_id:    User ID performing the action (None for system events).
            details:     Optional structured metadata dict serialized to JSON.
            flush:       If True, flush to DB without committing (useful before a larger commit).
        """
        event = ChainOfCustody(
            evidence_id=evidence_id,
            actor_id=actor_id,
            action=action,
            details=json.dumps(details) if details else None,
        )
        db.add(event)
        if flush:
            db.flush()
        return event

    @classmethod
    def get_chain_for_evidence(
        cls,
        db: Session,
        evidence_id: int,
        current_user,
    ) -> ChainOfCustodyResponse:
        """
        Returns the complete chronological chain-of-custody log for a piece of evidence.
        """
        evidence = db.scalars(select(Evidence).where(Evidence.id == evidence_id)).first()
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evidence artifact #{evidence_id} not found.",
            )

        events = db.scalars(
            select(ChainOfCustody)
            .where(ChainOfCustody.evidence_id == evidence_id)
            .order_by(ChainOfCustody.created_at.asc())
        ).all()

        return ChainOfCustodyResponse(
            evidence_id=evidence.id,
            evidence_number=evidence.evidence_number,
            original_filename=evidence.original_filename,
            total_events=len(events),
            events=[cls._to_event_response(e) for e in events],
        )
