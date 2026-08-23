"""
Correlation Service for ADEIP Forensic Intelligence.

Orchestrates explainable correlation detection across events, entities, and timeline.
Persists correlation signals into the investigation_correlations database table.
"""
import datetime
import json
import logging
import math
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents.correlation_agent import correlation_agent
from app.agents.timeline_agent import timeline_agent
from app.core.audit_actions import AuditAction, AuditResourceType
from app.models.case import InvestigationCase
from app.models.correlation import CorrelationSignalType, InvestigationCorrelation
from app.models.entity import ExtractedEntityModel
from app.models.evidence import Evidence
from app.models.investigation_event import InvestigationEvent
from app.models.user import User
from app.schemas.correlation import (
    CorrelationListResponse,
    CorrelationResponse,
    CorrelationRunResultResponse,
)
from app.services.audit_service import AuditService

logger = logging.getLogger("adeip.services.correlation")


class CorrelationService:
    """
    Forensic correlation service implementing explainable multi-signal relationship discovery.
    """

    @classmethod
    def _to_correlation_response(cls, model: InvestigationCorrelation) -> CorrelationResponse:
        """Converts an ORM instance to a validated Pydantic schema."""
        event_ids = json.loads(model.related_event_ids) if model.related_event_ids else []
        entity_ids = json.loads(model.related_entity_ids) if model.related_entity_ids else []
        evidence_ids = json.loads(model.supporting_evidence_ids) if model.supporting_evidence_ids else []
        reasons_list = json.loads(model.reasons) if model.reasons else []

        return CorrelationResponse(
            id=model.id,
            case_id=model.case_id,
            correlation_id=model.correlation_id,
            signal_type=model.signal_type,
            title=model.title,
            description=model.description,
            correlation_score=model.correlation_score,
            related_event_ids=event_ids,
            related_entity_ids=entity_ids,
            supporting_evidence_ids=evidence_ids,
            reasons=reasons_list,
            disclaimer=model.disclaimer,
            created_at=model.created_at,
        )

    @classmethod
    def run_case_correlations(
        cls,
        db: Session,
        case_id: int,
        current_user: User,
        client_ip: Optional[str] = None,
    ) -> CorrelationRunResultResponse:
        """
        Executes the explainable correlation engine across all evidence, entities,
        and events for the given case, and saves results in the database.
        """
        # 1. Verify case exists
        case = db.scalars(select(InvestigationCase).where(InvestigationCase.id == case_id)).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Investigation case #{case_id} not found.",
            )

        # 2. Ingest Case Evidence
        evidence_items = list(db.scalars(select(Evidence).where(Evidence.case_id == case_id)).all())
        evidence_dicts = [
            {
                "id": ev.id,
                "original_filename": ev.original_filename,
                "sha256_hash": ev.sha256_hash,
                "mime_type": ev.mime_type,
            }
            for ev in evidence_items
        ]

        # 3. Ingest Investigation Events
        events_records = list(
            db.scalars(
                select(InvestigationEvent)
                .where(InvestigationEvent.case_id == case_id)
                .order_by(InvestigationEvent.timestamp.asc().nullslast(), InvestigationEvent.id.asc())
            ).all()
        )
        raw_events = [
            {
                "id": ev.id,
                "evidence_id": ev.evidence_id,
                "source": ev.source,
                "event_type": ev.event_type.value,
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                "entity_type": ev.entity_type,
                "entity_value": ev.entity_value,
                "metadata": json.loads(ev.event_metadata) if ev.event_metadata else None,
            }
            for ev in events_records
        ]

        # 4. Ingest Extracted Entities
        entities_records = list(
            db.scalars(select(ExtractedEntityModel).where(ExtractedEntityModel.case_id == case_id)).all()
        )
        extracted_entities = [
            {
                "id": ent.id,
                "entity_type": ent.entity_type.value,
                "entity_value": ent.entity_value,
                "normalized_value": ent.normalized_value,
                "evidence_id": ent.evidence_id,
                "event_id": ent.event_id,
                "event_ids": [ent.event_id] if ent.event_id else [],
                "extraction_method": ent.extraction_method,
                "confidence": ent.confidence,
            }
            for ent in entities_records
        ]

        # 5. Build timeline representation for temporal correlation
        mock_state = {
            "case_id": case_id,
            "evidence_ids": [ev.id for ev in evidence_items],
            "case_info": {"id": case.id, "title": case.title},
            "evidence_items": evidence_dicts,
            "raw_events": raw_events,
            "extracted_entities": extracted_entities,
            "agent_logs": [],
        }

        timeline_result = timeline_agent(mock_state)
        mock_state["timeline"] = timeline_result.get("timeline", [])

        # 6. Execute Correlation Agent
        correlation_result = correlation_agent(mock_state)
        identified_correlations = correlation_result.get("correlations", [])

        # 7. Persist identified correlations in DB (deduplicate against existing)
        existing_models = list(
            db.scalars(
                select(InvestigationCorrelation).where(InvestigationCorrelation.case_id == case_id)
            ).all()
        )
        existing_signatures = {
            (m.signal_type, m.title) for m in existing_models
        }

        new_models_to_save: List[InvestigationCorrelation] = []
        breakdown: Dict[str, int] = {}

        for item in identified_correlations:
            sig = (item["signal_type"], item["title"])
            breakdown[item["signal_type"]] = breakdown.get(item["signal_type"], 0) + 1

            if sig not in existing_signatures:
                existing_signatures.add(sig)
                corr_model = InvestigationCorrelation(
                    case_id=case_id,
                    correlation_id=item["correlation_id"],
                    signal_type=item["signal_type"],
                    title=item["title"],
                    description=item["description"],
                    correlation_score=item["correlation_score"],
                    related_event_ids=json.dumps(item.get("related_event_ids", [])),
                    related_entity_ids=json.dumps(item.get("related_entity_ids", [])),
                    supporting_evidence_ids=json.dumps(item.get("supporting_evidence_ids", [])),
                    reasons=json.dumps(item.get("reasons", [])),
                    disclaimer=item.get("disclaimer", "Potential relationship detected. Observational correlation does not establish causation or definitive proof."),
                )
                new_models_to_save.append(corr_model)

        if new_models_to_save:
            db.add_all(new_models_to_save)
            db.commit()

        # 8. Log Audit Event
        AuditService.log(
            db=db,
            action=AuditAction.ANALYSIS_COMPLETED,
            resource_type=AuditResourceType.CASE,
            user_id=current_user.id,
            resource_id=str(case_id),
            details={
                "action": "correlations_run",
                "case_id": case_id,
                "correlations_identified": len(identified_correlations),
                "new_persisted": len(new_models_to_save),
            },
            ip_address=client_ip,
            flush=True,
        )

        all_models = list(
            db.scalars(
                select(InvestigationCorrelation)
                .where(InvestigationCorrelation.case_id == case_id)
                .order_by(InvestigationCorrelation.correlation_score.desc(), InvestigationCorrelation.id.asc())
            ).all()
        )

        return CorrelationRunResultResponse(
            case_id=case_id,
            correlations_identified=len(all_models),
            new_correlations_saved=len(new_models_to_save),
            breakdown_by_signal=breakdown,
            items=[cls._to_correlation_response(m) for m in all_models],
        )

    @classmethod
    def get_case_correlations(
        cls,
        db: Session,
        case_id: int,
        signal_type: Optional[str] = None,
        min_score: Optional[float] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> CorrelationListResponse:
        """Retrieves paginated, filtered correlations for a case."""
        case = db.scalars(select(InvestigationCase).where(InvestigationCase.id == case_id)).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Investigation case #{case_id} not found.",
            )

        stmt = select(InvestigationCorrelation).where(InvestigationCorrelation.case_id == case_id)
        if signal_type:
            stmt = stmt.where(InvestigationCorrelation.signal_type == signal_type.strip().lower())
        if min_score is not None:
            stmt = stmt.where(InvestigationCorrelation.correlation_score >= min_score)

        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        offset = (max(1, page) - 1) * page_size
        items = list(
            db.scalars(
                stmt.order_by(
                    InvestigationCorrelation.correlation_score.desc(),
                    InvestigationCorrelation.id.asc(),
                )
                .offset(offset)
                .limit(page_size)
            ).all()
        )

        return CorrelationListResponse(
            case_id=case_id,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total > 0 else 0,
            items=[cls._to_correlation_response(m) for m in items],
        )
