# Manual handover: plugins

**Status: NOT CONFIGURED.** This production directory is intentionally empty except for this guide. Do not add fake endpoints, credentials, official records, regulations, or model files.

## User must supply

Validated specialized model and license; compatible weights and runtime; input/output schema; trust provenance; validation data; measured performance, limitations and deployment resource budget. No model accuracy is asserted.

## Safe activation

Keep secrets in an authorized secret store or ignored server environment. Implement/review the relevant backend adapter, add fixture and failure tests, verify access scope in an approved sandbox, and explicitly enable live mode. Never relabel demo outputs as official verification. See the repository integration and security guides.
