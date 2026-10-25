# Rules and source governance

Demo checks are development examples, **not AICTE legal requirements**. No threshold or provision has been invented as an official rule.

A logical `validation_rules` record has an enabled flag and code. Each immutable version includes title, evaluator, parameters, source reference/URL/provision, effective interval, category UUIDs, severity, suggested action, demo label and expert-confirmed marker. A new version appends; it never rewrites old results. Active selection picks the newest currently effective applicable version. Existing findings retain exact version links. Date applicability is currently evaluated at run date, not a fully modeled academic-period legal regime.

Supported evaluator shapes:

```json
{"evaluation_type":"required_document","parameters":{"category":"certificate"}}
{"evaluation_type":"required_field","parameters":{"field":"institution_identifier"}}
{"evaluation_type":"expiry","parameters":{"field":"expiry_date"}}
{"evaluation_type":"comparison","parameters":{"field":"institution_identifier","institution_field":"identifier"}}
{"evaluation_type":"threshold","parameters":{"field":"faculty_count","minimum":24}}
{"evaluation_type":"manual","parameters":{}}
{"evaluation_type":"external","parameters":{}}
```

The numeric value above is purely an authoring-shape example, not an AICTE threshold. External/manual evaluators require human follow-up rather than asserting verification. Cross-document faculty/intake/reference/identifier/payment conflicts, duplicates, OCR uncertainty and metadata indicators are reusable baseline functions outside endpoint code. A preliminary FAIL is not a rejection.

## Convert official provisions safely

1. User supplies the actual authoritative handbook/regulation/amendments and source metadata to the appropriate README-only folder.
2. Confirm effective dates, category/period applicability, exceptions and required evidence with a qualified domain expert.
3. Draft a disabled rule with traceable provision and parameters. Add positive, negative, boundary, exception and inconclusive fixtures.
4. Compare against human-labeled cases. Record expert approval in your governance process, then set `expert_confirmed=true`, `demo_only=false` and activate through trusted administration.
5. Maintain the original source/hash, explanation and measured error analysis. Revisions require new immutable versions. Historical demo evaluations stay labeled demo.

Current authoring checks require evaluator parameters and effective-date ordering but are not an exhaustive legal rule DSL validator. Rich applicability expressions, exceptions, immutable source-document registry and a two-person approval workflow remain future work.
