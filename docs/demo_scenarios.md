# Synthetic demonstration scenarios

Generate: `python scripts/generate_fixtures.py`. Seed after hosted setup/profile provisioning: `python scripts/seed_demo.py --user-id <ACTUAL_INSTITUTION_AUTH_UUID> --reviewer-id <ACTUAL_REVIEWER_AUTH_UUID>`.

Every generated PDF is fictional, visibly DEMO, and not valid for official use. There are no real personal/institutional records. Generated PDFs are ignored by Git and reconstructed from code. The label manifest is `data/fixtures/labels.json`.

| Scenario | Seed behavior / expected preliminary observation |
|---|---|
| complete | Four category documents, matching fictional identifiers, future certificate date |
| missing_required_document | Undertaking absent; checklist finding |
| expired_certificate | Date 2020-01-01; expiry finding |
| identifier_mismatch | DEMO-WRONG-999 versus fictional institution identifier |
| faculty_discrepancy | Faculty list count 18 versus 24 in related documents; consistency warning |
| duplicate_document | Identical bytes under two different checklist associations; SHA-256 warning |
| metadata_anomaly | Different PDF creation/modification metadata; weak indicator requiring review, **not forgery proof** |
| simulated_success | SIMULATED / VERIFIED; no real authority |
| simulated_mismatch | SIMULATED / MISMATCH_DETECTED |
| source_unavailable | SIMULATED / SOURCE_UNAVAILABLE |
| verification_pending | SIMULATED / PENDING |
| infrastructure_incomplete | Infrastructure evidence absent; completeness failure and manual follow-up |

Different demo references across supporting documents can also produce a conservative reference inconsistency warning. A "complete" evidence package is not necessarily free from warnings and never implies approval. The current baseline cannot semantically distinguish all legitimate per-document reference types.

Metrics uses 12 single-certificate native-text fixtures with 60 labeled fields. The cloud seed makes multi-document applications and exercises more scenarios. Perfect scores on trivial generated fixtures demonstrate only that those deterministic fixture expectations match the implementation; no general-purpose forgery, OCR or regulatory accuracy is claimed.
