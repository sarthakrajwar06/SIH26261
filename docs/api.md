# Implemented REST API

Base path `/api/v1`. Interactive OpenAPI: `http://localhost:8000/docs`. Schema: `/openapi.json`.

Bearer tokens are issued by Supabase Auth. Login, logout, refresh and recovery use the Supabase JS SDK directly; there is no independent backend password-login endpoint. `/health` is public; business APIs require an active profile.

## Route inventory

| Method | Path | Operation |
|---|---|---|
| GET | `/health` | Health |
| GET | `/api/v1/auth/me` | Me |
| GET | `/api/v1/institutions` | Institutions |
| POST | `/api/v1/institutions` | Create Institution |
| GET | `/api/v1/institutions/{id}` | Institution |
| GET | `/api/v1/categories` | Categories |
| POST | `/api/v1/categories` | Create Category |
| GET | `/api/v1/applications` | Applications |
| POST | `/api/v1/applications` | Create Application |
| GET | `/api/v1/dashboard` | Dashboard |
| GET | `/api/v1/applications/{id}` | Application |
| PATCH | `/api/v1/applications/{id}` | Patch Application |
| POST | `/api/v1/applications/{id}/submit` | Submit |
| POST | `/api/v1/applications/{id}/rectification` | Rectification |
| POST | `/api/v1/applications/{id}/documents` | Upload |
| GET | `/api/v1/applications/{id}/documents` | Documents |
| GET | `/api/v1/documents/{id}` | Document |
| GET | `/api/v1/documents/{id}/content` | Content |
| POST | `/api/v1/documents/{id}/process` | Process |
| POST | `/api/v1/applications/{id}/validate` | Validate Application |
| GET | `/api/v1/applications/{id}/findings` | Findings |
| GET | `/api/v1/findings/{id}` | Finding |
| POST | `/api/v1/documents/{id}/verify` | Verify |
| GET | `/api/v1/documents/{id}/verification` | Verifications |
| GET | `/api/v1/verifications/{id}` | Verification |
| GET | `/api/v1/rules` | Rules |
| POST | `/api/v1/rules` | Create Rule |
| GET | `/api/v1/rules/{id}` | Rule |
| PATCH | `/api/v1/rules/{id}` | Patch Rule |
| POST | `/api/v1/rules/{id}/versions` | Version Rule |
| POST | `/api/v1/applications/{id}/review-actions` | Review Action |
| GET | `/api/v1/applications/{id}/review-actions` | Review History |
| POST | `/api/v1/findings/{id}/review` | Review Finding |
| GET | `/api/v1/applications/{id}/audit` | Application Audit |
| GET | `/api/v1/audit` | All Audit |
| GET | `/api/v1/applications/{id}/report` | Json Report |
| GET | `/api/v1/applications/{id}/report.pdf` | Pdf |
| GET | `/api/v1/notifications` | Notifications |
| POST | `/api/v1/notifications/{id}/read` | Read Notification |
| GET | `/api/v1/admin/users` | Users |
| PATCH | `/api/v1/admin/users/{id}` | User Patch |
| POST | `/api/v1/applications/{id}/assign` | Assign |
| GET | `/api/v1/system/integrations` | Integrations |
| GET | `/api/v1/applications/{id}/versions` | Application Versions |

## Access and requests

- Institution: own scoped applications; creation/upload only institution/admin; edits/uploads only DRAFT or RECTIFICATION_REQUIRED. Submit requires at least one document; missing checklist evidence becomes findings.
- Reviewer: assigned applications only. Verification/review routes require reviewer/admin. Institution can read authorized results but cannot assert verification.
- Administrator: trusted role changes, assignments, demo category/institution creation and versioned rule authoring. Cannot change their own role through the API.
- UUID path parameters reject malformed IDs. Schema validation uses Pydantic. No trusted role or institution is accepted from an unverified JWT payload.
- Application creation: `institution_id`, `category_id`, `academic_year` (YYYY-YY), optional `programme`. Reference generated in database.
- Multipart upload: `document_category` (lowercase underscore name), `file` (actual PDF/PNG/JPEG, at most 20 MiB). A category replacement appends a version. Originals are never removed by the API.
- Review: `action` enum plus `reason` of 10–4000 characters. Finding review resolves the application from the authorized finding; application review does not accept arbitrary finding IDs.
- Verification: `mode` (SIMULATED/MANUAL/OFFICIAL/QR/DIGITAL_SIGNATURE), synthetic `scenario` (success/mismatch/unavailable/pending), optional authority text. Unconfigured live/QR/signature routes return UNSUPPORTED, not success.
- Rule creation: logical `code`, `enabled`, nested version. Version requires title/evaluator/parameters/source/effective date/severity/suggested action/demo and expert flags. `POST .../versions` appends immutable versions.
- Profile changes require administrator, role/account status and institution if applicable. First provision existing Supabase Auth users with the local trusted script.

## Lists, files and errors

General lists return `{items,total,page,page_size}`. Application list supports page/page_size (1–100), status, safe reference search and newest/oldest sort. Dashboard uses exact head-only counts. Some case sublists cap at 100; unbounded large case streaming remains incomplete. Findings defaults to latest run; `history=true` includes old findings.
Private document content and PDF reports return binary bytes after resource authorization (no public URL). JSON/PDF report GET requests intentionally generate a new private stored report and audit record; they are not side-effect-free. File operations can fail after a partial write; inspect history before retry.
401: missing/invalid session. 403: role/account restriction. 404: missing or out-of-scope resource. 409: state lock/active job/concurrent transition. 413: size. 422: schema/file/parameter validation. 429: local rate limit. 503: missing configuration. Other failures return generic 500 without secrets.
Business mutations, notification creation and audit writes are not yet one database transaction. Database constraints prevent concurrent duplicate active jobs/version IDs, but callers may need to reload/retry. No endpoints issue a statutory approval or rejection.
