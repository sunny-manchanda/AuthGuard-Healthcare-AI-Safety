from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CaseRecord:
    case_id: str
    member_id: str
    member_name: str
    date_of_birth: str
    requested_service: str
    diagnosis: str
    message: str
    clinical_notes: str
    attachments: list[str]
    current_status: str = "Received"
    expected_route: str | None = None

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "CaseRecord":
        return cls(**value)


@dataclass
class PolicyEvidence:
    evidence_id: str
    policy_id: str
    title: str
    section: str
    text: str
    score: float
    required_documents: list[str] = field(default_factory=list)

    def citation(self) -> str:
        return f"[{self.evidence_id}] {self.title} — {self.section}"


@dataclass
class SafetyAssessment:
    risk_level: str
    score: int
    flags: list[str]
    categories: list[str]
    escalate: bool
    redacted_text: str


@dataclass
class RouteDecision:
    label: str
    confidence: float
    source: str


@dataclass
class AnalysisResult:
    case_id: str
    route: str
    confidence: float
    route_source: str
    risk_level: str
    safety_flags: list[str]
    missing_documents: list[str]
    discrepancies: list[str]
    evidence: list[PolicyEvidence]
    case_summary: str
    recommended_action: str
    draft_message: str
    tool_status: str
    protected: bool
    audit_id: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["citations"] = [item.citation() for item in self.evidence]
        return value

