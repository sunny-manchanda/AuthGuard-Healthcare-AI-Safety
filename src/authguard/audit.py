from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


class AuditLog:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self.events: list[dict] = []

    def record(self, event_type: str, case_id: str, actor: str, details: dict) -> str:
        event_id = f"AUD-{uuid.uuid4().hex[:10].upper()}"
        event = {
            "event_id": event_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "case_id": case_id,
            "actor": actor,
            "details": details,
        }
        self.events.append(event)
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event_id

