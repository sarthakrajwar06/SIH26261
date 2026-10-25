# Supabase setup

The SQL files in `migrations/` are the **only authoritative schema history**. No SQLAlchemy/Alembic migrations or local PostgreSQL server are used. A fresh hosted Supabase project provides `auth`, `storage`, `anon`, `authenticated` and `service_role` prerequisites.

## Apply

Dashboard method: execute `202610250001_foundation.sql`, `202610250002_snapshots.sql`, `202610250003_document_lock.sql`, then `seed.sql` in SQL Editor on a fresh development project. Each migration is transactional; do not rerun the table-creation files on an already migrated schema. On failure, inspect the real database error instead of silently skipping constraints.

CLI alternative from repository root (install Supabase CLI following its current official instructions):

```powershell
supabase login
supabase link --project-ref <YOUR_ACTUAL_PROJECT_REF>
supabase db push
# Then execute supabase/seed.sql in SQL Editor.
```

`config.toml` supports an optional Supabase CLI local stack (Docker), but hosted Supabase is the standard workflow. CLI authentication/database password prompts belong to the CLI, not chat or committed files.

## Result

- Normalized application, evidence, profile, rule/version/run, review and notification tables.
- RLS enabled for every public table. All ordinary client writes revoked. Scoped SELECT policies plus three owner-controlled scope helpers.
- Private storage buckets with 20 MiB file-size and MIME allowlists. SELECT policies match real metadata records, not just folder prefixes; no public bucket or ordinary client upload policy.
- Append-only findings, verifications, audit events, review actions, rule versions and submission snapshots. Original document metadata cannot change; processing status/analysis may change.
- Document insert locks the parent row and rejects changes to submitted cases. Submission snapshots include category and evidence-version metadata.
- Seed contains two fictional institutions, two demo categories and six logical demo rules. No Auth users or credentials, no official rules.

## Acceptance checks still required

Apply on a disposable project, inspect `pg_policies`, confirm bucket privacy, provision institution A/B and reviewer accounts, seed both tenants, execute `backend/tests/test_live_rls.py` with opt-in settings. Exercise direct Storage, REST and FastAPI access with institution and reviewer tokens. Verify denied INSERT/UPDATE/DELETE and compare files after reprocessing. SQL syntax parsing alone does not demonstrate runtime RLS enforcement.

Changing bucket names requires a new reviewed migration to update bucket IDs and Storage policies. Do not enable public access to work around an authorization failure.
