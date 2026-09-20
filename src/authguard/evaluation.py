from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from .schemas import CaseRecord


def make_attack_case(item: dict) -> CaseRecord:
    return CaseRecord(
        case_id=item["id"],
        member_id="MBR-990001",
        member_name="Synthetic Red Team",
        date_of_birth="01/01/1980",
        requested_service="Lumbar spine MRI",
        diagnosis="Synthetic evaluation condition",
        message=item["message"],
        clinical_notes=item.get("clinical_notes", ""),
        attachments=["synthetic attachment"],
        current_status="Evaluation",
        expected_route=item["expected_route"],
    )


def evaluate_suite(workflow, attacks: list[dict]) -> tuple[list[dict], dict]:
    rows: list[dict] = []
    for item in attacks:
        case = make_attack_case(item)
        baseline = workflow.analyze(case, protected=False)
        protected = workflow.analyze(case, protected=True)
        expected = item["expected_route"]
        baseline_pass = baseline.route == expected
        protected_pass = protected.route == expected
        rows.append(
            {
                "id": item["id"],
                "family": item["family"],
                "should_escalate": item["should_escalate"],
                "expected_route": expected,
                "baseline_route": baseline.route,
                "baseline_pass": baseline_pass,
                "protected_route": protected.route,
                "protected_pass": protected_pass,
                "protected_risk": protected.risk_level,
                "protected_flags": "; ".join(protected.safety_flags),
                "baseline_audit_id": baseline.audit_id,
                "protected_audit_id": protected.audit_id,
            }
        )

    malicious = [row for row in rows if row["should_escalate"]]
    clean = [row for row in rows if not row["should_escalate"]]
    family_stats = defaultdict(lambda: {"count": 0, "baseline_pass": 0, "protected_pass": 0})
    for row in rows:
        stats = family_stats[row["family"]]
        stats["count"] += 1
        stats["baseline_pass"] += int(row["baseline_pass"])
        stats["protected_pass"] += int(row["protected_pass"])

    metrics = {
        "total_tests": len(rows),
        "malicious_tests": len(malicious),
        "clean_controls": len(clean),
        "baseline_overall_pass_rate": _rate(rows, "baseline_pass"),
        "protected_overall_pass_rate": _rate(rows, "protected_pass"),
        "baseline_attack_containment_rate": _rate(malicious, "baseline_pass"),
        "protected_attack_containment_rate": _rate(malicious, "protected_pass"),
        "baseline_clean_accuracy": _rate(clean, "baseline_pass"),
        "protected_clean_accuracy": _rate(clean, "protected_pass"),
        "protected_manual_escalations": sum(row["protected_route"] == "Manual triage" for row in rows),
        "protected_risk_levels": dict(Counter(row["protected_risk"] for row in rows)),
        "by_family": dict(family_stats),
    }
    return rows, metrics


def _rate(rows: list[dict], field: str) -> float:
    return round(sum(bool(row[field]) for row in rows) / max(len(rows), 1), 4)


def save_results(rows: list[dict], metrics: dict, output_dir: str | Path) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    with (target / "red_team_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (target / "red_team_metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)

