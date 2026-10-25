# Executed checks — 25 October 2026

These results describe the sandbox checkout, not a certified production deployment.

| Command/check | Actual result |
|---|---|
| `.venv/bin/python -m pytest backend/tests -q` | **42 passed, 1 skipped** (live Supabase isolation requires configured project/accounts) |
| `npm test --prefix frontend` | **7 passed**, 2 test files |
| `npm run build --prefix frontend` | TypeScript and Vite production build passed; output split into React, Supabase and chart chunks |
| `npm audit --prefix frontend` | **0 known vulnerabilities** after dependency updates, including runtime and development dependencies |
| `python -m compileall -q backend scripts` | Passed |
| pglast parse of migration and seed SQL | 50 + 12 + 6 + 3 statements parsed; **syntax only**, not live migration execution |
| Uvicorn start / `/health` | Running on 0.0.0.0:8000, health 200, configured=false |
| Vite start / `/` | Running on 0.0.0.0:5173, HTML 200 |
| Same-origin Vite `/health` proxy | 200 |
| Same-origin unauthenticated applications request | 401, no data |

## Backend coverage actually exercised

- RSA JWT signature, issuer, audience and expiry verification; missing-token denial.
- Role guard, production-rule confirmation and evaluator parameter checks.
- Foreign-resource denial before server-secret access (API test doubles, not live tenant RLS).
- Actual generated PDF byte validation and native extraction, field normalization and page/excerpt evidence.
- Corrupt/unsupported/empty/oversize/encrypted input rejection; PNG and scanned-PDF OCR behavior using a stub.
- Required documents, expiry, identifier comparison, cross-document consistency, duplicate hashes, incomplete processing and rule applicability.
- Four simulated verification statuses and unconfigured QR/signature/live responses.
- Report generation with actual PyMuPDF PDF output, notices and simulation labels.
- API workflow with an in-memory Supabase test double: create → invalid empty submission → upload → submit/background extraction/validation → locked-upload denial → reviewer rectification → institutional review denial → evidence upload/resubmission → duplicate finding → simulated verification → reasoned review → JSON/PDF stored-report generation → audit and notification checks.
- SQL static guardrails and OpenAPI parameter safety. Actual database triggers, grants and RLS are **not** exercised by the memory double.

## Frontend coverage actually exercised

Status/simulation labels, empty/error states, confirmation dialog, unconfigured login behavior, reviewer finding display, reason validation, finding-scoped action submission and unauthorized-case error rendering. jsdom plus mocked API, **not** full browser/real Supabase E2E.

## Measured synthetic fixture metrics

`python scripts/metrics.py` generated 12 native-text certificate PDFs with 60 labeled fields. Actual latest measured output:

- Field matches: **60/60 (100%)**.
- Synthetic expiry precision/recall: **1.0 / 1.0**.
- Synthetic metadata-difference indicator precision/recall: **1.0 / 1.0**.
- Mean local processing time: approximately **0.00233 seconds/document** (machine/run-dependent).
- Findings with document evidence in this limited set: **100%**. Missing-document findings in real checklists naturally have no existing-document reference and are not part of this metric set.
- Test-double API workflow completed: **true**.
- Live Supabase workflow tested: **false**.

These simple generated fixtures are designed around the parser patterns. They provide no estimate of real document OCR, semantic extraction, anomaly/forgery detection, regulatory compliance accuracy or validated model performance. No real-world accuracy claim is made.

## Not executed / outstanding

Hosted Supabase migrations/seed, real Auth/session refresh/recovery, RLS and Storage enforcement, reviewer isolation against an actual database, Windows scripts, Docker image, real Tesseract recognition, browser screenshot/accessibility/complete E2E tests, government APIs, official rule acceptance, validated vision models, load/penetration/retention/backup tests. The connected Supabase account had no projects. No credentials or working development accounts were invented.

The backend environment emits a Starlette warning that its TestClient httpx adapter is deprecated; tests currently pass. Update the test transport alongside supported FastAPI/Starlette changes rather than concealing warnings.
