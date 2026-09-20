from __future__ import annotations

import json
from pathlib import Path

from .schemas import CaseRecord


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: str | Path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_cases(path: str | Path | None = None) -> list[CaseRecord]:
    target = Path(path) if path else project_root() / "data" / "cases.json"
    return [CaseRecord.from_dict(item) for item in load_json(target)]


def load_policy_chunks(path: str | Path | None = None) -> list[dict]:
    target = Path(path) if path else project_root() / "data" / "policy_chunks.json"
    return load_json(target)

