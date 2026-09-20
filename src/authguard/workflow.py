from __future__ import annotations

from pathlib import Path

from .audit import AuditLog
from .data import load_policy_chunks, project_root
from .retrieval import PolicyRetriever
from .router import LABELS, RuleBasedRouter
from .safety import assess_input
from .schemas import AnalysisResult, CaseRecord
from .tools import SimulatedCaseTool


NEXT_ACTIONS = {
    "Document collection": "Request the missing supporting documents and hold the case for staff review.",
    "Administrative correction": "Return the case to operations for demographic or administrative correction.",
    "Clinician review": "Prepare the evidence summary for clinician review or peer-to-peer coordination.",
    "Denial review": "Send the notice and cited policy evidence to the denial and appeals review queue.",
    "Status follow-up": "Request an updated payer status and record the expected response date.",
    "Approval record review": "Ask staff to verify authorization dates, units, service code, and reference number.",
    "Manual triage": "Pause automation and send the case to a human reviewer with the safety flags.",
}


class AuthGuardWorkflow:
    def __init__(
        self,
        router=None,
        policy_chunks: list[dict] | None = None,
        audit_path: str | Path | None = None,
        confidence_threshold: float = 0.55,
    ):
        self.router = router or RuleBasedRouter()
        self.retriever = PolicyRetriever(policy_chunks or load_policy_chunks())
        self.audit = AuditLog(audit_path)
        self.tools = SimulatedCaseTool(self.audit)
        self.confidence_threshold = confidence_threshold

    @classmethod
    def default(cls, router=None) -> "AuthGuardWorkflow":
        root = project_root()
        return cls(router=router, audit_path=root / "outputs" / "audit_log.jsonl")

    def analyze(
        self,
        case: CaseRecord,
        actor_role: str = "Operations analyst",
        protected: bool = True,
    ) -> AnalysisResult:
        combined_text = "\n".join(
            [
                case.message,
                case.clinical_notes,
                "Attachments: " + ", ".join(case.attachments),
            ]
        ).strip()
        safety = assess_input(combined_text)

        # Untrusted case content is data, not an instruction channel. The protected
        # path uses the redacted version and escalates detected manipulation.
        routing_text = safety.redacted_text if protected else combined_text
        route = self.router.classify(routing_text)
        if route.label not in LABELS:
            route.label, route.confidence = "Manual triage", 0.0
        if protected and (safety.escalate or route.confidence < self.confidence_threshold):
            route.label = "Manual triage"

        query = " ".join(
            [
                case.requested_service,
                case.diagnosis,
                safety.redacted_text if protected else combined_text,
            ]
        )
        evidence = self._retrieve_scoped_evidence(case, combined_text, query)
        missing = self._missing_documents(case, evidence)
        discrepancies = self._find_discrepancies(case, combined_text)
        if protected and discrepancies:
            route.label = "Manual triage"

        summary = self._build_summary(case, route.label, evidence, missing, discrepancies)
        recommended_action = NEXT_ACTIONS[route.label]
        draft_message = self._draft_message(case, route.label, missing, evidence)
        tool_status = "No action executed; reviewer confirmation required."
        audit_id = self.audit.record(
            "case_analysis",
            case.case_id,
            actor_role,
            {
                "protected": protected,
                "route": route.label,
                "confidence": route.confidence,
                "risk_level": safety.risk_level,
                "flags": safety.flags,
                "citations": [item.citation() for item in evidence],
                "missing_documents": missing,
                "discrepancies": discrepancies,
                "tool_status": tool_status,
            },
        )
        return AnalysisResult(
            case_id=case.case_id,
            route=route.label,
            confidence=route.confidence,
            route_source=route.source,
            risk_level=safety.risk_level,
            safety_flags=safety.flags,
            missing_documents=missing,
            discrepancies=discrepancies,
            evidence=evidence,
            case_summary=summary,
            recommended_action=recommended_action,
            draft_message=draft_message,
            tool_status=tool_status,
            protected=protected,
            audit_id=audit_id,
        )

    @staticmethod
    def _missing_documents(case: CaseRecord, evidence) -> list[str]:
        required: list[str] = []
        for item in evidence:
            for document in item.required_documents:
                if document not in required:
                    required.append(document)
        supplied = " ".join(case.attachments).lower()
        return [item for item in required if item.lower() not in supplied]

    def _retrieve_scoped_evidence(self, case: CaseRecord, text: str, query: str):
        """Keep retrieval inside the applicable service and control policies.

        A broad lexical search is useful for ranking, but document requirements
        from unrelated services must never be mixed into the case checklist.
        """
        service = case.requested_service.lower()
        lowered = text.lower()
        allowed = {"AG-OPS-005"}
        if any(term in service for term in ("mri", "ct", "imaging")):
            allowed.add("AG-IMG-001")
        if "physical therapy" in service or "therapy extension" in service:
            allowed.add("AG-PT-002")
        if any(term in service for term in ("durable medical", "wheelchair", "equipment")):
            allowed.add("AG-DME-003")
        if any(term in service for term in ("medication", "pharmacy", "drug")):
            allowed.add("AG-RX-004")
        if any(term in lowered for term in ("denied", "denial", "appeal")):
            allowed.add("AG-APP-006")

        candidates = self.retriever.search(query, limit=len(self.retriever.chunks))
        scoped = [item for item in candidates if item.policy_id in allowed]
        return scoped[:3]

    @staticmethod
    def _find_discrepancies(case: CaseRecord, text: str) -> list[str]:
        lowered = text.lower()
        findings: list[str] = []
        if "approved" in lowered and any(term in lowered for term in ("denied", "denial", "not authorized")):
            findings.append("The content contains both approval and denial language.")
        if "two different authorization" in lowered or "conflicting authorization" in lowered:
            findings.append("Multiple or conflicting authorization identifiers are present.")
        if "conflicting service date" in lowered or "different service date" in lowered:
            findings.append("Conflicting service dates require manual reconciliation.")
        if case.current_status.lower() == "approved" and "denied" in lowered:
            findings.append("The stored case status conflicts with the new message.")
        return findings

    @staticmethod
    def _build_summary(case, route, evidence, missing, discrepancies) -> str:
        citations = ", ".join(item.citation() for item in evidence) or "No policy evidence retrieved"
        parts = [
            f"Case {case.case_id} concerns {case.requested_service} for the documented diagnosis of {case.diagnosis}.",
            f"Recommended administrative queue: {route}.",
            f"Evidence consulted: {citations}.",
        ]
        if missing:
            parts.append("Potentially missing documents: " + ", ".join(missing) + ".")
        if discrepancies:
            parts.append("Discrepancies: " + " ".join(discrepancies))
        parts.append("A staff member must verify the recommendation before any case change.")
        return " ".join(parts)

    @staticmethod
    def _draft_message(case, route, missing, evidence) -> str:
        if route == "Manual triage":
            return "No external message drafted. The case requires human review."
        citations = "; ".join(item.citation() for item in evidence)
        if missing:
            return (
                f"Please provide the following information for synthetic case {case.case_id}: "
                f"{', '.join(missing)}. Supporting reference: {citations}. "
                "This is an administrative request and not a coverage determination."
            )
        return (
            f"Synthetic case {case.case_id} has been prepared for {route.lower()}. "
            f"Supporting reference: {citations}. A staff reviewer will confirm the next step."
        )
