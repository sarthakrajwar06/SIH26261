# Security model and acceptance tests

## Implemented controls

- Trusted asymmetric JWT verification (ES256/RS256 only), issuer/audience/expiry/subject requirements, cached JWKS lookup, active profile check per request.
- No signup self-assignment path; initial profiles through a local server-secret operator script. Role changes require an administrator and cannot target the caller's own role.
- User-scoped RLS reads plus explicit role/resource checks before server-secret writes/downloads. Unauthorized resources return 404, not confirmation that another tenant's record exists.
- Private buckets, metadata-record-bound download policies, safe filenames, actual PDF/image validation, 20 MiB cap, image pixel/PDF page limits, checksums, preserved original versions.
- Immutable original file metadata and append-only history database triggers; document insert/submission row locking.
- Restricted CORS, no tokens/passwords in logs/responses, generic server errors, no LLM uploads, `nosniff`, `no-store`, private blob fetching, confirmation dialogs and accessible labels.
- Auth changes clear frontend query caches so a later user does not see another session's cached records.
- Single-process/IP rate limiting (180 requests/minute). This is a local safeguard, not a production distributed gateway.

## Live acceptance test (not run in the unconfigured sandbox)

Use a disposable Supabase project with both institution A and B seeded. Generate a report for B first. Do not use personal or production records. Provide these variables only in your local process:

```powershell
$env:RUN_LIVE_SUPABASE_TESTS="1"
$env:SUPABASE_URL="<YOUR_PROJECT_URL>"
$env:SUPABASE_PUBLISHABLE_KEY="<YOUR_PUBLIC_KEY>"
$env:TEST_USER_A_EMAIL="<YOUR_SYNTHETIC_ACCOUNT_A_EMAIL>"
$env:TEST_USER_A_PASSWORD=Read-Host "Synthetic A password"
$env:TEST_USER_B_EMAIL="<YOUR_SYNTHETIC_ACCOUNT_B_EMAIL>"
$env:TEST_USER_B_PASSWORD=Read-Host "Synthetic B password"
.\.venv\Scripts\python.exe -m pytest backend/tests/test_live_rls.py -v
```

The test signs in through actual Supabase Auth, verifies disjoint application visibility and direct foreign-ID reads, rejects ordinary writes and denies foreign private documents/reports. It does **not** yet cover every table/operation or reviewer assignment mutation. Also manually exercise all REST tables, direct Storage paths, API report endpoints and an unassigned reviewer. A live skipped test is not evidence of RLS correctness.

Offline JWT tests cover correct signature, wrong signature/issuer/audience/expiry; API tests cover missing auth, role checks, locked uploads, workflow and report generation with test doubles. The SQL static test is only a guardrail. Never describe it as a live isolation test.

## Production gates / limitations

1. Parsers run in-process in the baseline. File signatures and keyword active-content rejection are not comprehensive malware protection. Add antivirus/quarantine, process isolation, CPU/memory/time limits, decompression limits and a patched PDF-rendering sandbox before untrusted production intake.
2. Add durable worker leases/retries/idempotency and transaction-scoped audit/business writes. API calls may partially succeed if a later audit/notification write fails.
3. Add distributed identity-based rate limits, reverse-proxy request bounds, TLS, CSP/security-header hardening and operational monitoring. Do not forward arbitrary trusted proxy addresses.
4. Retention days are configuration only; no automatic purge is claimed. Agree legal basis, duration, report/audit retention, legal holds, archive and deletion permissions, then implement/test a privileged purge policy. Do not accept real confidential data until this is resolved.
5. Auth audit events are not comprehensively ingested. Use Supabase Auth logging plus an approved export policy. No MFA enforcement, backup restore drill, penetration test or formal accessibility audit has been completed.
6. Findings/review observations are currently case-shared. A separate reviewer-only confidential note model is not implemented.
7. Production rule activation uses an explicit expert-confirmed flag from a trusted administrator, not a cryptographically signed four-eyes approval workflow.
8. QR codes and PDF signatures need an issuer trust store, revocation/chain rules and validation; merely decoding a URL cannot verify authenticity. No arbitrary URL fetcher is implemented (avoids SSRF).
