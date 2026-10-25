# Integration operations

See [master guide](../integrations/README.md) for required inputs and [regulatory governance](regulatory_rules.md).

Adapters expose `verify(document, fields)` and return mode, status, source ID, checked time, matched/mismatched fields, response reference and explanation. The request retains document/application linkage in the database. `MockAdapter` alone returns synthetic successful/mismatched outcomes; all responses explicitly carry SIMULATED. `UnconfiguredAdapter`, QR and signature placeholders return UNSUPPORTED; manual requests return MANUAL_REVIEW_REQUIRED.

No user-supplied endpoint is fetched, no CAPTCHA is bypassed, no credentials are stored under integration folders and no real government response is fabricated. Implement an authorized adapter in backend code only after receiving documentation/scope, with timeout, retry/backoff, allowlisted endpoints, issuer trust configuration and sanitized response provenance. Test with the authority's authorized sandbox; deploy behind an explicit controlled mode switch. Do not silently fall back from real to mock verification. Persist source failures/inconclusive status; notify and route for human follow-up.

Internal notifications work independently. External notification delivery and any LLM provider are disabled. Optional vision input/output contract exists; no model or loader capable of executing arbitrary external files is configured.
