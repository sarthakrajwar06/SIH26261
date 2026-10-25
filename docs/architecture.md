# Architecture

## Trust boundaries

Browser → same-origin Vite proxy → FastAPI `/api/v1` → hosted Supabase. Browser signs in through Supabase Auth with a publishable key. No independent authentication store exists. FastAPI verifies ES256/RS256 JWT signature, issuer, expiry, audience and required claims via the configured project JWKS. An active database profile determines role, never user-editable token metadata.

Scoped PostgREST clients attach the user's token for all reads. RLS scopes institutions and assigned reviewer cases. The server's separate secret client performs writes **only after** role and scoped-record checks. The secret never crosses the frontend boundary. Client direct writes are revoked, so an arbitrary browser REST call cannot create findings, mutate workflow, elevate a profile or erase audit events.

## Modules

- `security/auth.py`: JWT, profile status, scope and role guards.
- `api/routes.py`: validated transport, lifecycle, private file coordination and administrative actions.
- `repositories/store.py`: privileged writes, append-only audit insertion and notifications.
- `services/workflow.py`: extraction jobs, active rules, latest category document selection and validation runs.
- `document_ai/extract.py`: file checks, native PDF text first, Tesseract fallback, field normalization, evidence and classification.
- `rules/engine.py`: pure deterministic rule functions and cross-record/anomaly checks.
- `verification/adapters.py`: typed adapter contract, mock, QR/signature placeholders and safe unsupported responses.
- `infrastructure/plugins.py`: optional validated vision contract and evidence-presence checks. No model is loaded.
- `reporting/reports.py`: JSON/PDF with evidence, rule versions and decision-support notice.

Additional namespace directories preserve extension boundaries, not claims of separate working services. SQLAlchemy is unnecessary for this PostgREST implementation.

## Processing

Upload checks actual bytes and size, stores original privately and registers a checksum/version. User may process a draft document, or submit the application to schedule serial document extraction followed by validation. FastAPI BackgroundTasks runs synchronous processing off the event loop. Jobs persist status; the task execution itself is in-process and **not durable**. OCR never runs in a SQL trigger. A future queue must add claim/lease/retry semantics and reauthorize queued access; merely increasing Uvicorn worker count is unsafe.

Native PDFs retain page/excerpt evidence without invented confidence. OCR retains available recognition confidence. Classification is a keyword heuristic and does not change the user-declared checklist association. Image dHash, checksum and PDF metadata are weak investigation indicators, not proof of authenticity/fraud.

## Reproducibility

Each validation run appends results with exact rule version IDs. Each submission has a database-triggered snapshot. Replacements create a new immutable original record. Reviewer actions are separate records; findings are not overwritten. Reprocessing currently replaces the current extracted-field rows, while prior findings retain excerpts/page references. Full extraction revisioning is a future improvement.
