# Evaluation protocol

## Objective

The evaluation measures whether the workflow reaches a predefined safe administrative outcome under adversarial and ordinary inputs. It does not evaluate clinical quality or medical necessity.

## Test set

The fixed synthetic suite contains 32 tests:

- 24 adversarial tests covering jailbreaks, document prompt injection, obfuscation, crescendo attacks, PII extraction, social engineering, unauthorized tool use, and medical-boundary requests.
- 8 clean and privacy-preserving controls covering the seven AuthRoute queues plus PII masking.

Each test defines an expected safe queue before execution. Adversarial tests generally expect `Manual triage`; clean controls expect their correct administrative queue.

## Compared workflows

1. **Baseline:** AuthRoute v3 model routing without AuthGuard escalation controls.
2. **Protected:** the same model plus input normalization, attack detection, PII minimization, allowed-label validation, confidence gating, discrepancy checks, scoped evidence retrieval, human authorization, and audit logging.

The same test messages and expected outcomes are used for both paths.

## Model-backed Colab results

| Metric | Result |
|---|---:|
| Total tests | 32 |
| Malicious/adversarial tests | 24 |
| Clean/privacy controls | 8 |
| Baseline attack containment | 29.2% |
| Protected attack containment | 100.0% |
| Baseline clean accuracy | 100.0% |
| Protected clean accuracy | 100.0% |

Family-level counts are recorded in `outputs/model_backed_family_results.csv`; aggregate metrics are recorded in `outputs/red_team_metrics.json`.

## Interpretation

The comparison isolates the contribution of workflow controls around the model. The protected path reached the defined safe outcome for every test in this small, intentionally designed suite while retaining all clean controls. This is useful prototype evidence, not a production certification. A deployable system would require larger independent test sets, longitudinal monitoring, specialist review, privacy and security assessment, and testing against live operational failure modes.
