"""
Knowledge Graph Pydantic Schemas for ADEIP.
Provides structured node and edge schemas directly compatible with the frontend graph visualization.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class GraphNodeItem(BaseModel):
    """
    Structured node in the Investigation Knowledge Graph.
    Fully compatible with frontend interactive graph visualizers.
    """
    id: str
    label: str
    type: str             # "Person", "Device", "Account", "IP Address", "File", "USB Device", "Location", "Evidence", "Event"
    typeKey: str          # "person", "device", "account", "ip", "file", "usb", "location", "evidence", "event"
    risk: str = "info"    # "critical", "high", "medium", "low", "info"
    riskScore: int = 50   # 0 to 100
    details: Optional[str] = None
    evidence: List[str] = Field(default_factory=list)
    evidence_ids: List[int] = Field(default_factory=list)
    event_ids: List[int] = Field(default_factory=list)
    timeline: List[Dict[str, Any]] = Field(default_factory=list)
    properties: Dict[str, Any] = Field(default_factory=dict)

    # Optional display coordinates
    x: Optional[float] = None
    y: Optional[float] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class GraphEdgeItem(BaseModel):
    """
    Structured directed relationship in the Investigation Knowledge Graph.
    Maintains dual field aliases ('from'/'to' and 'source'/'target') for maximum frontend compatibility.
    """
    id: str
    source: str
    target: str
    from_node: str = Field(..., alias="from")
    to_node: str = Field(..., alias="to")
    label: str            # "USED", "ACCESSED", "CONNECTED_TO", "TRANSFERRED_TO", "LOCATED_AT", "RELATED_TO", "OBSERVED_IN"
    relationship: str
    type: str = "data"    # "causal", "access", "network", "hardware", "data", "auth", "physical", "correlation"
    risk: str = "medium"

    # Evidence grounding & explainability
    evidence_ids: List[int] = Field(default_factory=list)
    event_ids: List[int] = Field(default_factory=list)
    correlation_id: Optional[str] = None
    score: Optional[float] = None
    reasons: List[str] = Field(default_factory=list)
    properties: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class CaseKnowledgeGraphResponse(BaseModel):
    """
    Complete Investigation Knowledge Graph response for a case.
    """
    case_id: int
    case_title: str
    case_number: Optional[str] = None
    neo4j_synced: bool = False
    node_count: int
    edge_count: int
    nodes: List[GraphNodeItem] = Field(default_factory=list)
    edges: List[GraphEdgeItem] = Field(default_factory=list)
    links: List[GraphEdgeItem] = Field(default_factory=list)  # Alias for edges
    breakdown_by_type: Dict[str, int] = Field(default_factory=dict)
    summary: Dict[str, Any] = Field(default_factory=dict)


class GraphSyncResultResponse(BaseModel):
    """Result returned after synchronizing case graph topology to Neo4j."""
    case_id: int
    neo4j_status: str     # "connected", "offline", "synced"
    nodes_synced: int
    relationships_synced: int
    message: str
