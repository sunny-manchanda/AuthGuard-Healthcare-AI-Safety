from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import gradio as gr  # noqa: E402

from authguard.data import load_cases, load_json  # noqa: E402
from authguard.evaluation import evaluate_suite  # noqa: E402
from authguard.router import LABELS  # noqa: E402
from authguard.schemas import CaseRecord  # noqa: E402
from authguard.workflow import AuthGuardWorkflow  # noqa: E402


CASES = {case.case_id: case for case in load_cases()}
ATTACKS = load_json(ROOT / "evals" / "attack_suite.json")


def _case_values(case_id: str):
    case = CASES[case_id]
    return (
        case.requested_service,
        case.diagnosis,
        case.message,
        case.clinical_notes,
        ", ".join(case.attachments),
        case.current_status,
    )


def build_app(workflow: AuthGuardWorkflow | None = None):
    workflow = workflow or AuthGuardWorkflow.default()

    def analyze_case(case_id, service, diagnosis, message, notes, attachments, status, role, protected):
        original = CASES[case_id]
        case = CaseRecord(
            case_id=case_id,
            member_id=original.member_id,
            member_name=original.member_name,
            date_of_birth=original.date_of_birth,
            requested_service=service,
            diagnosis=diagnosis,
            message=message,
            clinical_notes=notes,
            attachments=[item.strip() for item in attachments.split(",") if item.strip()],
            current_status=status,
            expected_route=original.expected_route,
        )
        result = workflow.analyze(case, actor_role=role, protected=protected)
        evidence_md = "\n\n".join(
            f"**{item.citation()}**  \n{item.text}  \n_Retrieval score: {item.score}_"
            for item in result.evidence
        ) or "No matching policy evidence was retrieved."
        flags = "\n".join(f"- {flag}" for flag in result.safety_flags) or "- No safety flags"
        missing = "\n".join(f"- {item}" for item in result.missing_documents) or "- None identified"
        discrepancies = "\n".join(f"- {item}" for item in result.discrepancies) or "- None identified"
        decision = {
            "case_id": result.case_id,
            "recommended_queue": result.route,
            "confidence": round(result.confidence, 4),
            "router": result.route_source,
            "risk_level": result.risk_level,
            "protected_mode": result.protected,
            "recommended_action": result.recommended_action,
            "tool_status": result.tool_status,
            "audit_id": result.audit_id,
        }
        return decision, result.case_summary, flags, missing, discrepancies, evidence_md, result.draft_message

    def request_action(case_id, action, target_queue, role, approved):
        return workflow.tools.request_action(
            case_id=case_id,
            action=action,
            actor_role=role,
            approved=approved,
            target_queue=target_queue,
        )

    def run_red_team():
        rows, metrics = evaluate_suite(workflow, ATTACKS)
        table = [
            [
                row["id"],
                row["family"],
                row["expected_route"],
                row["baseline_route"],
                "PASS" if row["baseline_pass"] else "FAIL",
                row["protected_route"],
                "PASS" if row["protected_pass"] else "FAIL",
            ]
            for row in rows
        ]
        return metrics, table

    def audit_snapshot():
        return list(reversed(workflow.audit.events[-50:]))

    first_case = next(iter(CASES))
    initial_values = _case_values(first_case)

    with gr.Blocks(title="AuthGuard — Governed Prior Authorization Operations") as demo:
        gr.Markdown(
            "# AuthGuard\n"
            "### Governed prior-authorization operations and adversarial testing\n"
            "Synthetic-data prototype. AuthGuard recommends an administrative queue, retrieves policy "
            "evidence, identifies documentation gaps, and requires human confirmation before case changes. "
            "It does **not** make clinical, coverage, approval, or denial decisions."
        )

        with gr.Tab("Case review"):
            with gr.Row():
                with gr.Column(scale=1):
                    case_id = gr.Dropdown(list(CASES), value=first_case, label="Synthetic case")
                    role = gr.Dropdown(
                        ["Operations analyst", "Clinical reviewer", "Operations supervisor"],
                        value="Operations analyst",
                        label="Signed-in role (simulated)",
                    )
                    protected = gr.Checkbox(value=True, label="Enable AuthGuard protections")
                    service = gr.Textbox(value=initial_values[0], label="Requested service")
                    diagnosis = gr.Textbox(value=initial_values[1], label="Documented diagnosis")
                    status = gr.Textbox(value=initial_values[5], label="Current case status")
                with gr.Column(scale=2):
                    message = gr.Textbox(value=initial_values[2], lines=5, label="Payer message")
                    notes = gr.Textbox(value=initial_values[3], lines=4, label="Clinical/administrative notes")
                    attachments = gr.Textbox(value=initial_values[4], lines=2, label="Attachment names, comma-separated")
                    analyze = gr.Button("Analyze safely", variant="primary")

            case_id.change(
                _case_values,
                inputs=case_id,
                outputs=[service, diagnosis, message, notes, attachments, status],
            )

            with gr.Row():
                decision = gr.JSON(label="Controlled decision record")
                summary = gr.Textbox(lines=8, label="Reviewer summary")
            with gr.Row():
                flags = gr.Markdown(label="Safety findings")
                missing = gr.Markdown(label="Missing documents")
                discrepancies = gr.Markdown(label="Discrepancies")
            evidence = gr.Markdown(label="Retrieved policy evidence")
            draft = gr.Textbox(lines=5, label="Draft administrative communication")

            analyze.click(
                analyze_case,
                inputs=[case_id, service, diagnosis, message, notes, attachments, status, role, protected],
                outputs=[decision, summary, flags, missing, discrepancies, evidence, draft],
            )

        with gr.Tab("Human-approved actions"):
            gr.Markdown(
                "Only allowlisted administrative actions are available. Approval and denial are intentionally excluded. "
                "Every state-changing action requires an authorized role and explicit confirmation."
            )
            action_case = gr.Dropdown(list(CASES), value=first_case, label="Case")
            action = gr.Dropdown(
                ["create_work_item", "update_queue", "request_information", "approve_request"],
                value="update_queue",
                label="Requested action",
            )
            target_queue = gr.Dropdown(LABELS, value="Document collection", label="Target queue")
            action_role = gr.Dropdown(
                ["Operations analyst", "Clinical reviewer", "Operations supervisor"],
                value="Operations analyst",
                label="Actor role",
            )
            approved = gr.Checkbox(value=False, label="Human reviewer confirms this action")
            action_button = gr.Button("Request simulated action", variant="primary")
            action_result = gr.JSON(label="Authorization result")
            action_button.click(
                request_action,
                inputs=[action_case, action, target_queue, action_role, approved],
                outputs=action_result,
            )

        with gr.Tab("Red-team evaluation"):
            gr.Markdown(
                "Run the same adversarial suite against the baseline and protected workflows. "
                "The suite covers jailbreaks, document injection, obfuscation, crescendo, privacy, "
                "social engineering, unauthorized tools, clinical boundaries, and clean controls."
            )
            run_eval = gr.Button("Run 32-test evaluation", variant="primary")
            metrics = gr.JSON(label="Evaluation metrics")
            results = gr.Dataframe(
                headers=["ID", "Family", "Expected", "Baseline", "Baseline result", "Protected", "Protected result"],
                datatype="str",
                interactive=False,
                label="Attack evidence",
            )
            run_eval.click(run_red_team, outputs=[metrics, results])

        with gr.Tab("Audit trail"):
            refresh_audit = gr.Button("Refresh audit trail")
            audit_output = gr.JSON(label="Most recent events")
            refresh_audit.click(audit_snapshot, outputs=audit_output)

        gr.Markdown(
            "**Prototype boundary:** Synthetic data only. All recommendations require staff validation. "
            "No live payer submission, approval, denial, diagnosis, or treatment recommendation is performed."
        )

    return demo


if __name__ == "__main__":
    build_app().launch()

