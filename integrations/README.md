# Master integration handover

## Current modes

| Capability | Delivered behavior |
|---|---|
| Supabase | SDK-backed persistence, Auth and private Storage software; user must configure project and test deployment |
| Native PDF extraction | Local PyMuPDF, exercised against generated fixtures |
| Scanned OCR | Tesseract interface; install binary/language data locally; recognition not measured here |
| Rules/consistency | Local deterministic checks; seeded rules explicitly DEMO |
| Mock issuer | Four statuses, every result `verification_mode=SIMULATED` |
| AICTE / issuers / accreditation / repositories | NOT CONFIGURED; no invented endpoint or response |
| QR / signatures | Interfaces only; UNSUPPORTED without authorized trust/verification adapter |
| Infrastructure | Completeness and manual review only; no validated vision model |
| Notifications | Internal database notifications; no external email/SMS integration |
| LLM | Disabled; no paid dependency and no external document disclosure |

Each subfolder README lists exact documentation/authorization required. Official handbooks/regulations belong to the separate `regulatory_sources/` handover directories. Model licenses/weights/validation belong to `infrastructure_models/plugins/` after explicit review, not a fabricated model placeholder.

## Live-adapter process

1. Receive actual official documentation, lawful credentials, endpoint allowlist and authorized scope. Never ask a tool to bypass a CAPTCHA, rate limit or access control.
2. Implement `VerificationAdapter` in backend code; sanitize inputs, restrict destinations, validate TLS, configure timeout and bounded retries. Persist actual source/time/response references without logging secrets or entire confidential responses.
3. Test authorized sandbox success, mismatch, expired, unavailable, pending, unsupported and manual-follow-up paths. External providers are not required by the offline suite.
4. Use an explicit reviewed server-side registry/configuration to enable that adapter. No live registry toggle is wired today; adding a fake dashboard toggle would misrepresent integration status.
5. Preserve `verification_mode=OFFICIAL` only for genuinely authorized live source calls, and never silently substitute SIMULATED results when live verification fails. Human review remains mandatory for inconclusive cases.
6. For QR/signature verification, validate issuer trust, cryptographic chain and revocation rules; never equate decoding a QR code with authenticity.
7. For external notifications, configure approved sender/templates and least-privileged credentials; internal notifications remain independent.

No credentials should be placed in these folders. Use ignored local `.env` for development and managed secrets for deployment. Limit retention and external disclosure according to an approved policy.
