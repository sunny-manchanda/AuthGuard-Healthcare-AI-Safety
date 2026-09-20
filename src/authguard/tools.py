from __future__ import annotations

from .audit import AuditLog


ALLOWED_ACTIONS = {"create_work_item", "update_queue", "request_information"}
AUTHORIZED_ROLES = {"Clinical reviewer", "Operations supervisor"}


class SimulatedCaseTool:
    """Read-only by default; all state-changing calls need explicit approval."""

    def __init__(self, audit: AuditLog):
        self.audit = audit
        self.state: dict[str, dict] = {}

    def request_action(
        self,
        case_id: str,
        action: str,
        actor_role: str,
        approved: bool = False,
        target_queue: str | None = None,
    ) -> dict:
        if action not in ALLOWED_ACTIONS:
            status, reason = "blocked", "Action is not on the tool allowlist."
        elif actor_role not in AUTHORIZED_ROLES:
            status, reason = "blocked", "Actor role is not authorized for case changes."
        elif not approved:
            status, reason = "pending_approval", "Human confirmation is required."
        else:
            status, reason = "executed", "Simulated case action completed."
            self.state.setdefault(case_id, {})["last_action"] = action
            if target_queue:
                self.state[case_id]["queue"] = target_queue

        audit_id = self.audit.record(
            "tool_action",
            case_id,
            actor_role,
            {
                "action": action,
                "target_queue": target_queue,
                "approved": approved,
                "status": status,
                "reason": reason,
            },
        )
        return {"status": status, "reason": reason, "audit_id": audit_id}

