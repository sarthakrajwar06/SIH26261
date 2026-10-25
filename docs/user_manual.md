# User manual

## Institution workspace

Sign in with a provisioned Supabase account. Overview counts are live database counts within your scope. Applications supports reference search, state filter, date ordering and pagination. Create a draft using the two metadata steps; the next steps live in application details (Supporting documents, then Review/Submit). Institution fields are managed by a trusted administrator rather than arbitrary user-entered identifiers.

Choose the checklist category for each file. Upload original PDF, PNG or JPEG. Re-uploading a category creates its next version; all originals remain in the evidence list. Only the latest version per category is evaluated. There is no destructive remove-original button. Process individual drafts or submit the application for automatic extraction/validation. Uploads lock outside DRAFT/RECTIFICATION_REQUIRED. Missing checklist documents generate findings; submission is not an official statutory declaration.

Evidence tab shows original, fields, page/excerpt, OCR confidence (when available), and jobs. Low confidence is not fraud. Retry failed extraction after fixing OCR configuration. Findings explain expected/observed values and open their document/page references. Reports are private. Notifications show processing and review changes. Rectification unlocks uploads; corrections need resubmission.

## Reviewer workspace

Only explicitly assigned applications are visible. Select case → Evidence → original document and extracted fields. Findings → evidence links or Record disposition. Review action needs a reason of at least ten characters. Actions never erase system findings. Request rectification/additional evidence/manual issuer follow-up, record observations or readiness for official review. CLOSED and READY_FOR_OFFICIAL_REVIEW are internal states, not approval/rejection.

Verification tab provides four explicitly SIMULATED mock outcomes and manual follow-up. The mock does not contact an issuer. Authoritative verification/signature/QR adapters remain unconfigured. Review history and application audit preserve observations. Do not add confidential reviewer-only notes: the current record model is shared with authorized case users.

## Administrator workspace

Provision Auth users through Supabase and trusted local profile script. Use User management for subsequent authorized role/institution/status changes (not your own). Assign reviewers in a case's Review tab. Rules page reads source/version metadata and offers trusted JSON authoring with explicit demo/source labels; production provisions require expert confirmation. Integration status distinguishes local/simulated/unconfigured systems. System audit shows application and administrative events.

## Error handling

A 404 may mean nonexistent or out-of-scope. Contact an administrator instead of changing IDs. A 409 means workflow is locked, a job already exists or state changed. A generic server failure may occur after a partial write; reload history before retrying. Reports downloaded to your computer are your responsibility to protect and delete under policy.
