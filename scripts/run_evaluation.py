from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from authguard.data import load_json  # noqa: E402
from authguard.evaluation import evaluate_suite, save_results  # noqa: E402
from authguard.workflow import AuthGuardWorkflow  # noqa: E402


def main() -> None:
    workflow = AuthGuardWorkflow.default()
    attacks = load_json(ROOT / "evals" / "attack_suite.json")
    rows, metrics = evaluate_suite(workflow, attacks)
    save_results(rows, metrics, ROOT / "outputs")

    print("AuthGuard red-team evaluation")
    print(f"Tests: {metrics['total_tests']}")
    print(f"Baseline containment: {metrics['baseline_attack_containment_rate']:.1%}")
    print(f"Protected containment: {metrics['protected_attack_containment_rate']:.1%}")
    print(f"Protected clean accuracy: {metrics['protected_clean_accuracy']:.1%}")
    print(json.dumps(metrics["by_family"], indent=2))
    print("Saved outputs/red_team_results.csv and outputs/red_team_metrics.json")


if __name__ == "__main__":
    main()

