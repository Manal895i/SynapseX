"""
Recommendation Service for ADEIP Forensic Intelligence.

Orchestrates gap analysis and recommendation generation:
- Timeline Gaps
- Incomplete Correlations
- Missing Context
- Unsupported Hypotheses
Persists recommendations into the investigation_recommendations table.
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
from app.agents.missing_evidence_agent import missing_evidence_agent
from app.agents.reasoning_agent import reasoning_agent
from app.agents.timeline_agent import timeline_agent
from app.core.audit_actions import AuditAction, AuditResourceType
from app.models.case import InvestigationCase
from app.models.entity import ExtractedEntityModel
from app.models.evidence import Evidence
from app.models.finding import InvestigationFindingModel
from app.models.investigation_event import InvestigationEvent
from app.models.recommendation import (
    InvestigationRecommendationModel,
    RecommendationPriority,
)
from app.models.user import User
from app.schemas.recommendation import (
    RecommendationListResponse,
    RecommendationResponse,
    RecommendationRunResultResponse,
)
from app.services.audit_service import AuditService

logger = logging.getLogger("adeip.services.recommendation")


class RecommendationService:
    """
    Forensic service managing evidence gap analysis and advisory acquisition recommendations.
    """

    @classmethod
    def _to_recommendation_response(cls, model: InvestigationRecommendationModel) -> RecommendationResponse:
        """Converts an ORM model to a validated Pydantic schema."""
        ev_ids = json.loads(model.related_evidence_ids) if model.related_evidence_ids else []

        return RecommendationResponse(
            id=model.id,
            recommendation_id=model.recommendation_id,
            case_id=model.case_id,
            recommendation=model.recommendation,
            reason=model.reason,
            gap_type=model.gap_type,
            priority=model.priority,
            related_finding_id=model.related_finding_id,
            related_evidence_ids=ev_ids,
            suggested_source=model.suggested_source,
            created_at=model.created_at,
        )

    @classmethod
    def run_case_recommendations(
        cls,
        db: Session,
        case_id: int,
        current_user: User,
        client_ip: Optional[str] = None,
    ) -> RecommendationRunResultResponse:
        """
        Executes the Missing Evidence Agent on the case, persists identified gaps
        and advisory recommendations in the database, and returns the result summary.
        """
        case = db.scalars(select(InvestigationCase).where(InvestigationCase.id == case_id)).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Investigation case #{case_id} not found.",
            )

        # 1. Gather Case Data
        evidence_items = list(db.scalars(select(Evidence).where(Evidence.case_id == case_id)).all())
        events_records = list(
            db.scalars(
                select(InvestigationEvent)
                .where(InvestigationEvent.case_id == case_id)
                .order_by(InvestigationEvent.timestamp.asc().nullslast(), InvestigationEvent.id.asc())
            ).all()
        )
        entities_records = list(
            db.scalars(select(ExtractedEntityModel).where(ExtractedEntityModel.case_id == case_id)).all()
        )
        findings_records = list(
            db.scalars(select(InvestigationFindingModel).where(InvestigationFindingModel.case_id == case_id)).all()
        )

        evidence_dicts = [
            {
                "id": ev.id,
                "original_filename": ev.original_filename,
                "sha256_hash": ev.sha256_hash,
                "integrity_status": ev.integrity_status.value,
            }
            for ev in evidence_items
        ]
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
        extracted_entities = [
            {
                "id": ent.id,
                "entity_type": ent.entity_type.value,
                "entity_value": ent.entity_value,
                "normalized_value": ent.normalized_value,
                "evidence_id": ent.evidence_id,
                "event_id": ent.event_id,
                "event_ids": [ent.event_id] if ent.event_id else [],
                "confidence": ent.confidence,
            }
            for ent in entities_records
        ]
        findings_dicts = [
            {
                "finding_id": f.finding_id,
                "title": f.title,
                "category": f.category,
                "description": f.summary,
            }
            for f in findings_records
        ]

        # 2. Build mock state and run upstream agents
        mock_state = {
            "case_id": case_id,
            "evidence_ids": [ev.id for ev in evidence_items],
            "case_info": {"id": case.id, "title": case.title},
            "evidence_items": evidence_dicts,
            "raw_events": raw_events,
            "extracted_entities": extracted_entities,
            "findings": findings_dicts,
            "agent_logs": [],
        }

        timeline_res = timeline_agent(mock_state)
        mock_state["timeline"] = timeline_res.get("timeline", [])

        corr_res = correlation_agent(mock_state)
        mock_state["correlations"] = corr_res.get("correlations", [])

        # 3. Execute Missing Evidence Agent
        missing_res = missing_evidence_agent(mock_state)
        raw_recs = missing_res.get("recommendations", [])

        # 4. Deduplicate and persist recommendations to database
        existing_models = list(
            db.scalars(
                select(InvestigationRecommendationModel).where(InvestigationRecommendationModel.case_id == case_id)
            ).all()
        )
        existing_signatures = {
            (m.gap_type, m.recommendation) for m in existing_models
        }

        new_models_saved: List[InvestigationRecommendationModel] = []
        breakdown_priority: Dict[str, int] = {}
        breakdown_gap: Dict[str, int] = {}

        for item in raw_recs:
            gap_type = item.get("gap_type", "missing_context")
            rec_title = item.get("recommendation", "")
            prio_val = item.get("priority", "medium").lower()

            try:
                prio_enum = RecommendationPriority(prio_val)
            except ValueError:
                prio_enum = RecommendationPriority.MEDIUM

            breakdown_priority[prio_enum.value] = breakdown_priority.get(prio_enum.value, 0) + 1
            breakdown_gap[gap_type] = breakdown_gap.get(gap_type, 0) + 1

            sig = (gap_type, rec_title)
            if sig not in existing_signatures:
                existing_signatures.add(sig)
                rec_model = InvestigationRecommendationModel(
                    recommendation_id=item.get("recommendation_id"),
                    case_id=case_id,
                    recommendation=rec_title,
                    reason=item.get("reason", ""),
                    gap_type=gap_type,
                    priority=prio_enum,
                    related_finding_id=item.get("related_finding_id"),
                    related_evidence_ids=json.dumps(item.get("related_evidence_ids", [])),
                    suggested_source=item.get("suggested_source"),
                )
                db.add(rec_model)
                new_models_saved.append(rec_model)

        if new_models_saved:
            db.commit()

        # 5. Log Audit Trail
        AuditService.log(
            db=db,
            action=AuditAction.ANALYSIS_COMPLETED,
            resource_type=AuditResourceType.CASE,
            user_id=current_user.id,
            resource_id=str(case_id),
            details={
                "action": "recommendations_run",
                "case_id": case_id,
                "recommendations_generated": len(raw_recs),
                "new_persisted": len(new_models_saved),
            },
            ip_address=client_ip,
            flush=True,
        )

        all_models = list(
            db.scalars(
                select(InvestigationRecommendationModel)
                .where(InvestigationRecommendationModel.case_id == case_id)
                .order_by(InvestigationRecommendationModel.created_at.desc())
            ).all()
        )

        return RecommendationRunResultResponse(
            case_id=case_id,
            recommendations_generated=len(all_models),
            new_recommendations_saved=len(new_models_saved),
            breakdown_by_priority=breakdown_priority,
            breakdown_by_gap_type=breakdown_gap,
            items=[cls._to_recommendation_response(m) for m in all_models],
        )

    @classmethod
    def list_case_recommendations(
        cls,
        db: Session,
        case_id: int,
        priority: Optional[str] = None,
        gap_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> RecommendationListResponse:
        """Retrieves paginated, filtered recommendations for a case."""
        case = db.scalars(select(InvestigationCase).where(InvestigationCase.id == case_id)).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Investigation case #{case_id} not found.",
            )

        stmt = select(InvestigationRecommendationModel).where(InvestigationRecommendationModel.case_id == case_id)
        if priority:
            stmt = stmt.where(InvestigationRecommendationModel.priority == priority.strip().lower())
        if gap_type:
            stmt = stmt.where(InvestigationRecommendationModel.gap_type == gap_type.strip().lower())

        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        offset = (max(1, page) - 1) * page_size
        items = list(
            db.scalars(
                stmt.order_by(InvestigationRecommendationModel.created_at.desc())
                .offset(offset)
                .limit(page_size)
            ).all()
        )

        return RecommendationListResponse(
            case_id=case_id,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total > 0 else 0,
            items=[cls._to_recommendation_response(m) for m in items],
        )
