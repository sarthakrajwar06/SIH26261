# AICTE Insight · SIH26261

**AICTE Intelligent Application Scrutiny and Verification System** — a working development implementation of preliminary application scrutiny, not an official AICTE service or an autonomous approval system.

React/TypeScript/Vite + FastAPI/Python + hosted **Supabase PostgreSQL, Auth and private Storage**. No second database, password store, paid LLM, or government API is required. This repository root is the `aicte-insight/` project; no redundant nested checkout is needed.

## Verification status (25 October 2026)

- Frontend production build, component tests, backend tests and synthetic API-to-report workflow executed. See [actual results](docs/test_results.md).
- Both servers started; frontend, backend health, same-origin proxy and unauthenticated API denial smoke-tested.
- **No Supabase project exists in the connected account.** Migrations have been SQL syntax-parsed, not applied to a cloud database. Auth, live Storage, triggers, RLS and cloud seed execution remain unverified until you configure a dedicated project.
- Tesseract is not installed in this sandbox. Scanned OCR behavior is tested with a stub, not real OCR recognition. Windows/PowerShell execution and full browser end-to-end automation have not been run here.
- **Not production-ready or the complete Definition of Done.** See [implementation checklist](IMPLEMENTATION_CHECKLIST.md) for gaps rather than assuming every requested capability is finished.

## What is implemented

Supabase login/session refresh/recovery, active profiles and three roles; scoped application registry, dashboard counts, draft wizard and checklist upload; private original PDF/PNG/JPEG uploads, hashes and replacement versions; background processing records, native PDF extraction, local Tesseract interface, heuristic classification and field evidence; versioned deterministic checks, missing evidence, expiry, identity, cross-record consistency, duplicate and weak metadata/perceptual indicators; reviewer evidence panel, separate reasoned actions, rectification and resubmission; visibly SIMULATED verification, safe unconfigured adapters; notifications, append-only audit history, submission snapshots, private PDF/JSON reports, trusted role management, twelve generated synthetic scenarios.

## Windows quick start

### 1. Prerequisites

- Windows 10/11, PowerShell, Git.
- **Python 3.11**, available as `py -3.11`.
- **Node.js 22.12+** and npm (tested on 22.22.3). Current Vite requires a modern Node release.
- A hosted Supabase project you own. No local PostgreSQL installation is necessary.
- For scans: install Tesseract from a distribution you trust, add `tesseract.exe` to PATH, then verify `tesseract --version`. Native-text PDFs work without it. Optional Docker backend includes Tesseract.

From the repository root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup.ps1
notepad .env
```

Setup creates `.venv`, installs Python dependencies and runs `npm ci`. `backend/requirements.lock.txt` records the environment tested here; use `pip install -r backend/requirements.lock.txt` for those exact versions instead of the supported ranges. No secrets are committed.

### 2. Configure Supabase

1. Create a dedicated development project in the Supabase dashboard. Select your region and a strong database password; keep it outside this repository.
2. Project settings → API/Connect: copy the project URL and **publishable key** into `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `VITE_SUPABASE_URL`, and `VITE_SUPABASE_PUBLISHABLE_KEY` in root `.env`. The `VITE_` values are intentionally public.
3. Copy the **server secret key** into `SUPABASE_SECRET_KEY` only. Never prefix it with `VITE_`, paste it into frontend code, or expose it through an endpoint.
4. Auth signing keys: use an asymmetric **ES256 or RS256** key. Legacy shared-secret HS256 JWTs are intentionally not supported. Set `SUPABASE_JWT_ISSUER=https://<your-ref>.supabase.co/auth/v1`, `SUPABASE_JWKS_URL=https://<your-ref>.supabase.co/auth/v1/.well-known/jwks.json`, audience `authenticated`. These URLs come from your own project, not an invented government endpoint.
5. SQL Editor: execute every file under `supabase/migrations/` in filename order, **once**. Then execute `supabase/seed.sql`. Alternatively use the Supabase CLI link/push process in [supabase/README.md](supabase/README.md). Do not use both methods to reapply the same migration.
6. The migrations create tables, RLS policies, private `application-documents` and `application-reports` buckets, immutable-history guards, upload-lock guards and submission snapshot triggers. Confirm both buckets are private in the dashboard. Keep default bucket names; changing names requires a matching policy migration.
7. Auth URL configuration: Site URL `http://localhost:5173`; add `http://localhost:5173/reset-password` to redirect URLs. For a hosted preview, configure that exact preview URL and matching recovery URL instead. Configure email delivery for password recovery; no email provider is fabricated. Disable public signup if not needed.
8. Set `FRONTEND_URL=http://localhost:5173` (exact allowed CORS origin), `BACKEND_URL=http://localhost:8000`, `OCR_ENGINE=tesseract`, `LLM_PROVIDER=none`.

### 3. Create development accounts and trusted profiles

In Supabase Auth → Users, create three **synthetic development accounts** (institution, reviewer, administrator), with passwords you choose. Confirm email through your configured provider or the authorized dashboard process. There are no built-in passwords or pre-seeded Auth users.

Copy each real Auth UUID from that project. Replace the angle-bracket placeholders below; never use placeholder IDs as real records:

```powershell
.\.venv\Scripts\python.exe backend\scripts\provision_user.py --user-id <ADMIN_AUTH_UUID> --role admin
.\.venv\Scripts\python.exe backend\scripts\provision_user.py --user-id <REVIEWER_AUTH_UUID> --role reviewer
.\.venv\Scripts\python.exe backend\scripts\provision_user.py --user-id <INSTITUTION_AUTH_UUID> --role institution --institution-id 10000000-0000-4000-8000-000000000001
```

The last institution ID is the fictional Meridian institution created by `seed.sql`. For isolation testing, create another institution account associated with fictional Riverstone (`10000000-0000-4000-8000-000000000002`). A user cannot self-provision or self-elevate. The script is a trusted local administrative tool requiring your server secret.

### 4. Generate and seed the synthetic scenarios

```powershell
.\.venv\Scripts\python.exe scripts\generate_fixtures.py
.\.venv\Scripts\python.exe scripts\seed_demo.py --user-id <INSTITUTION_AUTH_UUID> --reviewer-id <REVIEWER_AUTH_UUID>
```

This uploads generated fictional PDFs to private Storage, inserts extracted fields, evaluates demo rules, assigns the reviewer, and adds the four simulated verification cases. It adds twelve cases **on every run**, so use a disposable test project. Generated PDFs are ignored by Git and reproducible. Cloud execution has not been verified here.

### 5. Start and sign in

```powershell
.\scripts\start.ps1
# Frontend: http://localhost:5173
# OpenAPI:  http://localhost:8000/docs
# Stop only tracked process trees:
.\scripts\stop.ps1
```

Or use two terminals:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000
npm --prefix frontend run dev
```

Sign in with the email/password **you created**. If Auth succeeds but no profile is present/active, the workspace denies access and explains provisioning. API fetches use relative URLs; Vite proxies `/api` to FastAPI. Browser code never calls a separate localhost backend.

Optional OCR-equipped backend: `docker compose up --build backend`, then `npm --prefix frontend run dev`. Docker is optional and untested in this environment.

## End-to-end demonstration

1. Institution: New application → select fictional institution → DEMO category → academic year → save draft.
2. On application details, upload synthetic PDFs with the applicable categories. Each category's newest version is the active evidence; previous versions remain downloadable. Uploads are locked after submission.
3. Submit. Extraction jobs run outside SQL triggers and generate real preliminary findings. Missing evidence is flagged, not interpreted as statutory rejection.
4. Administrator: Review tab → assign the active reviewer. Reviewer sees only assigned cases.
5. Reviewer: Evidence tab → select original → inspect page-linked fields; Findings → open evidence; Review → record a reasoned rectification request.
6. Institution: upload corrected evidence in `RECTIFICATION_REQUIRED`, then resubmit. Findings and rule versions from older runs remain in history; new results do not erase them.
7. Reviewer: Verification tab → run a **SIMULATED** scenario or request manual follow-up. No real issuer is contacted.
8. Report tab: download JSON/PDF; the report is generated from stored data, preserves evidence and simulation labels, and is saved in private Storage. History shows append-only application events.

See [user manual](docs/user_manual.md) and [scenario guide](docs/demo_scenarios.md).

## Tests and measured metrics

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
npm --prefix frontend test
npm --prefix frontend run build
npm --prefix frontend audit
.\.venv\Scripts\python.exe scripts\metrics.py
```

The offline API workflow test uses a **test-only Supabase double**, not an alternative production database/auth system. The opt-in live isolation test requires actual pre-provisioned synthetic accounts; see [security tests](docs/security.md). No government service is needed. Synthetic native-text results must not be represented as OCR accuracy or forgery detection performance.

## Project map

```text
frontend/src/     components, layouts, hooks, pages, services, routes/types/utils boundaries
backend/app/      api, security, repositories, services, schemas, document_ai, rules,
                  verification, infrastructure, reporting and extension boundaries
backend/tests/   deterministic processing, JWT/security, workflow and opt-in live RLS
supabase/        authoritative SQL migrations, config and fictional seed
scripts/         PowerShell lifecycle, fixture generation, cloud seed, measured metrics
integrations/    production integration README-only placeholders
regulatory_sources/   official source and verified-rule README-only placeholders
infrastructure_models/plugins/   validated model placeholder (no weights)
docs/            architecture, API, database, security, user and operator guides
```

## Integration handover

Implemented locally: PDF extraction, deterministic rules, image hash/metadata indicators, report generation and internal notifications. Tesseract needs its local binary. Simulated only: mock issuer statuses. Unconfigured: AICTE, issuer/accreditation/repository APIs, QR trust, digital-signature trust, validated vision model and external notifications. **No confidential document is sent to an LLM.**

The required README-only directories describe exactly what to supply: `integrations/{aicte,issuing_authorities,accreditation_sources,digital_repositories,notifications}/`, `regulatory_sources/{official_handbooks,official_regulations,verified_rules}/`, `infrastructure_models/plugins/`. See [master integration guide](integrations/README.md).

## Troubleshooting / known limitations

- Unconfigured login: fill root `.env` with the project URL/public key, restart Vite. No guest bypass is provided.
- 401 with a valid Supabase session: verify asymmetric signing keys, issuer, audience, JWKS URL and system clock.
- 403/profile not provisioned: run the trusted profile script for the actual Auth UUID, check account status and institution.
- 404 on another case: intentionally hides unauthorized resources. Administrator must explicitly assign reviewers.
- OCR job ERROR: install Tesseract, check PATH and use Process / retry. Native text extraction requires no OCR binary. Regex extraction is a limited baseline, not a general layout-understanding model.
- Interrupted job after process exit: stop all workers; run `backend/scripts/recover_jobs.py` and follow its confirmation prompt. In-process jobs are **not durable**, and pending work does not auto-resume. Do not deploy multiple worker processes without a real queue/lease design.
- API failure after a write: most cross-table writes are not a single database transaction. Reload and inspect history before retrying. Storage upload compensation is implemented when document metadata insertion fails.
- Retention: `RETENTION_DAYS` is an exposed operator setting, **not an automatic purge**. An approved policy and purge/archive process must be configured before accepting confidential production data.
- Read lists have documented page/cap limits; reports/validation do not yet stream arbitrarily large case files. Scoped counts use exact database counts.
- Production still needs malware scanning, sandboxed resource-bounded parsers, durable queue, distributed rate limiting, restore/retention tests, accessibility/browser E2E audit, richer schema-aware field extraction, official rule validation, and live cloud security acceptance tests.
