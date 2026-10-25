# Manual handover: notifications

**Status: NOT CONFIGURED.** This production directory is intentionally empty except for this guide. Do not add fake endpoints, credentials, official records, regulations, or model files.

## User must supply

Chosen email/SMS provider documentation; authorized sender settings and credentials stored outside Git; approved templates, consent/delivery policy and sandbox test destinations.

## Safe activation

Keep secrets in an authorized secret store or ignored server environment. Implement/review the relevant backend adapter, add fixture and failure tests, verify access scope in an approved sandbox, and explicitly enable live mode. Never relabel demo outputs as official verification. See the repository integration and security guides.
