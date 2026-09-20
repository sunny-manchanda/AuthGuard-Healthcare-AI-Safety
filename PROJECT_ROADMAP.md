# AuthGuard delivery roadmap

## Milestone 1 — Governed core workflow

Status: **complete locally**

- [x] Synthetic healthcare cases
- [x] Synthetic payer-policy corpus
- [x] Restricted, citable policy retrieval
- [x] Seven-queue router interface
- [x] AuthRoute v3 adapter
- [x] Required-document checks
- [x] Conflict detection
- [x] PII minimization
- [x] Prompt-injection and manipulation detection
- [x] Output label validation
- [x] Human-confirmed, allowlisted tools
- [x] Audit log
- [x] Gradio interface
- [x] 32-test adversarial suite
- [x] Automated tests and initial evidence charts

## Milestone 2 — Colab and AuthRoute v3 integration

Estimated time: **2–3 hours**

- [ ] Load `authroute_lora_v3` in the existing notebook
- [ ] Confirm 7/7 smoke tests
- [ ] Upload/extract `AuthGuard_Starter.zip`
- [ ] Connect `FineTunedRouter(classify)`
- [ ] Test all eight synthetic cases
- [ ] Run all 32 baseline and protected evaluations
- [ ] Save model-backed CSV and JSON evidence
- [ ] Launch the Gradio share link

## Milestone 3 — Hardening and evaluation expansion

Estimated time: **5–7 hours**

- [ ] Review model-backed failures and false positives
- [ ] Add case-level retrieval authorization tests
- [ ] Add document provenance labels
- [ ] Add confidence and conflicting-evidence calibration
- [ ] Expand the suite to 40 tests
- [ ] Add refusal-quality scoring
- [ ] Add attack-evidence screenshots
- [ ] Generate final charts from model-backed results

## Milestone 4 — Portfolio packaging

Estimated time: **4–5 hours**

- [ ] Create architecture and threat-model visuals
- [ ] Complete the Week 6 response document
- [ ] Add implementation roadmap and limitations
- [ ] Publish the GitHub repository
- [ ] Prepare a 4-minute demonstration script
- [ ] Record the video
- [ ] Validate every submission link

## Evidence rule

Only results generated after connecting the fine-tuned AuthRoute v3 classifier may be described as model-backed results. Local fallback results are development checks and must be labelled accordingly.

