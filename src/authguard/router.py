from __future__ import annotations

from collections.abc import Callable

from .schemas import RouteDecision


LABELS = [
    "Document collection",
    "Administrative correction",
    "Clinician review",
    "Denial review",
    "Status follow-up",
    "Approval record review",
    "Manual triage",
]


class RuleBasedRouter:
    """Deterministic offline fallback; Colab replaces this with AuthRoute v3."""

    source = "offline rules (replace with AuthRoute v3 in Colab)"

    RULES = [
        ("Manual triage", ["conflicting", "both approved and denied", "two different"]),
        ("Administrative correction", ["incorrect", "wrong member", "correct the", "demographic"]),
        ("Clinician review", ["peer-to-peer", "peer to peer", "medical director", "clinician review"]),
        ("Denial review", ["denied", "denial", "not authorized"]),
        ("Status follow-up", ["pending", "status update", "status request", "review window", "follow up"]),
        ("Approval record review", ["approved", "authorized", "authorization number"]),
        ("Document collection", ["upload", "missing", "office note", "clinical notes", "records"]),
    ]

    def classify(self, message: str) -> RouteDecision:
        lowered = message.lower()
        for label, terms in self.RULES:
            if any(term in lowered for term in terms):
                return RouteDecision(label, 0.82, self.source)
        return RouteDecision("Manual triage", 0.45, self.source)


class FineTunedRouter:
    """Adapter for the existing Colab ``classify(message)`` function."""

    source = "AuthRoute v3 fine-tuned Qwen3-1.7B"

    def __init__(self, predictor: Callable[[str], tuple[str, float]]):
        self.predictor = predictor

    def classify(self, message: str) -> RouteDecision:
        label, confidence = self.predictor(message)
        if label not in LABELS:
            return RouteDecision("Manual triage", 0.0, self.source + " (invalid output)")
        return RouteDecision(label, float(confidence), self.source)
