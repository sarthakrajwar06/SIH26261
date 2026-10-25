# Implementation checklist — honest delivery status

Legend: [x] code implemented (test scope below); [ ] incomplete or awaiting configuration/acceptance. This is not a claim that the entire master Definition of Done is met.

## Foundation and configuration
- [x] React/TypeScript/Vite/Tailwind, Radix accessible dialog, Router, Query, Hook Form/Zod, Recharts and Lucide.
- [x] FastAPI/Pydantic/Supabase SDK/JWT/PyMuPDF/Pillow/OpenCV/Tesseract interface/Pytest.
- [x] Modular boundaries, private env examples, lockfiles, Windows setup/start/stop scripts and optional Docker backend.
- [x] Required production-integration/regulatory/model folders actually exist and contain only handover READMEs.
- [ ] Windows and Docker execution verified (not available in sandbox).

## Supabase and security
- [x] Authoritative migrations, normalized records, indexes/constraints, all exposed-table RLS and scoped private-bucket SELECT policies.
- [x] Client mutation grants revoked; backend checks roles and RLS-scoped parents before service writes.
- [x] Asymmetric JWT validation, active profiles, trusted role provisioning, frontend cache clearing on account change.
- [x] Private original metadata immutability, append-only history, submission snapshots and document/submission concurrency guard.
- [x] Size/byte-format/page/pixel checks, safe filename/checksum, restricted CORS, local rate limit and safe generic errors.
- [ ] Apply migrations and run live Auth/RLS/Storage/trigger tests against a user-configured project.
- [ ] Exhaustive live per-table/read-write/storage/report/reviewer isolation acceptance matrix.
- [ ] Production parser sandbox/malware scan/distributed limits/retention purge/backup restore/security assessment.

## Core workflow
- [x] Supabase SDK sign in/out/session refresh/recovery UI, role-aware workspace and account provisioning gate.
- [x] Institution/dashboard registry, search/filter/sort/pagination, initial wizard, checklist uploads, submission/rectification/resubmission.
- [x] Original preservation, category replacement versions, active latest versions and private content serving.
- [x] Reviewer scope/assignment, evidence viewer and separate reasoned actions.
- [x] Internal notifications, audit trail with correlation UUID, private PDF/JSON reports.
- [x] Admin profile changes, rule authoring/versioning; institution/demo category creation APIs.
- [ ] Rich frontend institution/category administration and editing existing institution metadata.
- [ ] Single unified four-step wizard (metadata steps lead into document/review workspace rather than one persistent four-step component).
- [ ] Full official application-history/period/legal declaration model and reviewer-confidential notes.

## Document AI, rules and verification
- [x] Native text first, local Tesseract fallback, processing records/error/retry, page-linked fields and normalization.
- [x] Heuristic classification, OCR confidence warning, missing evidence, expiry, identifier/comparison, threshold/mandatory field/manual/external evaluator shapes.
- [x] Faculty/intake/reference/payment-status conflicts, SHA-256 duplicates, image dHash similarity, weak PDF metadata indicators.
- [x] Immutable rule versions and finding-run links; demo sources clearly distinct from production.
- [x] SIMULATED success/mismatch/unavailable/pending adapter; manual/QR/signature/live-safe unconfigured contracts.
- [x] Infrastructure checklist association/completeness and optional vision contract; no invented model.
- [ ] Real OCR binary execution and accuracy measurements in this environment.
- [ ] Durable queued workers/recovery automation/transactional cross-table workflows.
- [ ] Fully typed complex rule DSL, official academic-period applicability and per-facility infrastructure requirement registry.
- [ ] Full immutable extraction revision history (current fields are replaced on explicit reprocessing; findings retain original excerpts).
- [ ] Authorized issuer/AICTE/accreditation/repository adapters, trusted cryptographic verification and validated vision models (manual inputs required).
- [ ] Actual authoritative payment/intake/history verification, official provisions and expert approval (no such records supplied).

## Tests and finalization
- [x] Backend offline suite: 42 passed; live Supabase test correctly skipped.
- [x] Frontend tests: 7 passed, including reviewer action/error states.
- [x] Frontend production build, Python compile, SQL syntax parse and server/proxy smoke checks.
- [x] npm audit: 0 known vulnerabilities at execution time.
- [x] Repeatable fictional PDF generator, 12-scenario cloud seed software and measured limited-fixture metrics.
- [x] Setup, API, database, security, architecture, rule governance, integration, scenario and user guides.
- [ ] Cloud seed execution, real signed-in browser workflow and actual live database security tests.
- [ ] Full browser/accessibility/load test suite and real labeled OCR/anomaly corpus.

## External handover inputs

User must configure a Supabase project and create development Auth accounts. Official integrations need written access permissions, actual endpoints/schemas/sandbox details and securely supplied credentials. Production rules need authoritative handbook/regulation versions/amendments/effective dates and domain-expert confirmation. Vision needs licensed weights/validation data/measured performance. External email/SMS needs authorized provider/sender/templates. None are fabricated.
