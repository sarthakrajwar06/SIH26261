# Database model

All IDs are UUIDs. Migrations are authoritative; `supabase/seed.sql` contains only fictional records.

- `institutions` ← `profiles` and `applications`. Profiles reference `auth.users`; active institution roles require an association.
- `application_categories` stores the demo checklist and description. Application captures category, year, programme, creator, internal status and submission time.
- `reviewer_assignments` explicitly scopes reviewer visibility; no global reviewer read permission.
- `application_documents` → application; version unique per application/category, private storage path unique; original checksum, bytesize/MIME and uploader preserved.
- `processing_jobs` → document; partial unique index prevents multiple active jobs for one document. Current extracted fields retain page, excerpt, confidence and timestamp.
- `validation_rules` → immutable `validation_rule_versions`. Version parameters/evidence conditions are flexible JSON; frequently queried status/type/effective dates are typed columns.
- `validation_runs` → immutable `validation_findings`, which link the exact rule version, source evidence, observed/expected values and manual-review requirement.
- `source_verifications` and `review_actions` append observations rather than modifying original evidence/findings.
- `audit_logs` link actor, application, entity, outcome, request UUID and non-sensitive metadata.
- `notifications` are recipient-scoped; only the backend can mark read.
- `reports` point to privately stored immutable generated files. `application_versions` snapshot submission metadata/category/documents.

RLS is enabled for every exposed table; direct ordinary writes are denied. Audit and review data are visible to authorized case users. Do not place reviewer-confidential information in these shared observation records without adding a visibility model and corresponding policy.

Indexes support institution/date, application/document, checksums, assignment, recipient and finding/run reads. Foreign keys preserve linkage; history triggers reject UPDATE/DELETE on append-only tables. Production retention must account for these guards with an approved archival design, not blindly disable them.

Seeded rules are synthetic and historical evaluations must never be relabeled as official provisions. Production category updates should be new reviewed migrations, preserving prior submission snapshots.
