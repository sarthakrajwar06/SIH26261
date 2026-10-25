# Manual handover: digital_repositories

**Status: NOT CONFIGURED.** This production directory is intentionally empty except for this guide. Do not add fake endpoints, credentials, official records, regulations, or model files.

## User must supply

Supported repository and official verification documentation; written authorization; issuer trust roots/certificates, chain/revocation policy; supported signature and QR formats. A QR URL alone is not proof of authenticity.

## Safe activation

Keep secrets in an authorized secret store or ignored server environment. Implement/review the relevant backend adapter, add fixture and failure tests, verify access scope in an approved sandbox, and explicitly enable live mode. Never relabel demo outputs as official verification. See the repository integration and security guides.
