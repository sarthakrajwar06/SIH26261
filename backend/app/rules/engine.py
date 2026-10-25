"""Versioned, deterministic preliminary checks, independent of transport/database."""
from datetime import date
from collections import defaultdict

NOTICE = 'Preliminary decision support only; not an official AICTE approval or rejection.'

def evaluate(application, institution, documents, fields, rules, today=None):
    today = today or date.today()
    findings = []
    def add(code, status, explanation, evidence=None, expected=None, observed=None, rule=None, severity='WARNING'):
        findings.append({'application_id': application['id'], 'rule_id': rule.get('rule_id') if rule else None,
            'rule_version_id': rule.get('id') if rule else None, 'category': code, 'status': status,
            'severity': rule.get('severity',severity) if rule else severity, 'explanation': explanation,
            'expected_value': str(expected) if expected is not None else None,
            'observed_value': str(observed) if observed is not None else None,
            'evidence': evidence or [], 'suggested_action': rule.get('suggested_action','Inspect evidence; request clarification where needed') if rule else 'Inspect evidence; request clarification where needed',
            'manual_review_required': status not in ('PASS','NOT_APPLICABLE')})
    def evidence(f): return {'document_id': f['document_id'], 'page': f['page_number'], 'excerpt': f.get('excerpt','')}
    for rule in rules:
        if rule.get('effective_from','0001-01-01') > str(today) or (rule.get('effective_to') and rule['effective_to'] < str(today)): continue
        if rule.get('category_ids') and application['category_id'] not in rule['category_ids']: continue
        p, kind = rule.get('parameters',{}), rule['evaluation_type']
        selected = [f for f in fields if f['field_name'] == p.get('field')]
        if kind == 'required_document':
            exists = any(d['document_category'] == p.get('category') for d in documents)
            add('CHECKLIST', 'PASS' if exists else 'FAIL', rule['title'], expected=p.get('category'), observed='received' if exists else 'missing', rule=rule)
        elif kind == 'required_field':
            add('FIELD', 'PASS' if selected else 'INCONCLUSIVE', rule['title'], [evidence(f) for f in selected], expected=p.get('field'), observed=len(selected), rule=rule)
        elif kind == 'expiry':
            if not selected: add('EXPIRY','INCONCLUSIVE','No expiry date extracted',rule=rule)
            for f in selected:
                try: status = 'FAIL' if date.fromisoformat(f['normalized_value']) < today else 'PASS'
                except ValueError: status = 'INCONCLUSIVE'
                add('EXPIRY',status,rule['title'],[evidence(f)],str(today),f['normalized_value'],rule)
        elif kind == 'comparison':
            expected = institution.get(p.get('institution_field','identifier'))
            for f in selected:
                add('IDENTITY','PASS' if f['normalized_value'].casefold() == str(expected).casefold() else 'WARNING',rule['title'],[evidence(f)],expected,f['normalized_value'],rule)
        elif kind == 'threshold':
            for f in selected:
                try: status = 'PASS' if float(f['normalized_value']) >= float(p['minimum']) else 'FAIL'
                except (ValueError,KeyError,TypeError): status = 'INCONCLUSIVE'
                add('THRESHOLD',status,rule['title'],[evidence(f)],p.get('minimum'),f['normalized_value'],rule)
        else: add(kind.upper(),'MANUAL_REVIEW_REQUIRED',rule['title'],rule=rule)
    for name in ('institution_identifier','reference_number','faculty_count','intake','payment_status'):
        group = [f for f in fields if f['field_name'] == name]
        if len({f['normalized_value'] for f in group}) > 1:
            add('CONSISTENCY','WARNING',f'Conflicting {name} values; differences may have a legitimate explanation',[evidence(f) for f in group],observed=[f['normalized_value'] for f in group])
    for f in fields:
        if f.get('confidence') is not None and f['confidence'] < 0.8:
            add('EXTRACTION_UNCERTAINTY','MANUAL_REVIEW_REQUIRED','Low OCR confidence; confirm the extracted value against the original. This is not authenticity confidence.',[evidence(f)],observed=f['normalized_value'])
    hashes = defaultdict(list)
    for d in documents:
        hashes[d['checksum']].append(d)
        if d.get('processing_status') in ('ERROR','QUEUED','PROCESSING'):
            add('PROCESSING','INCONCLUSIVE','Document extraction is incomplete',[{'document_id':d['id']}])
        meta = d.get('analysis') or {}
        if meta.get('metadata',{}).get('modDate') and meta.get('metadata',{}).get('creationDate') and meta['metadata']['modDate'] != meta['metadata']['creationDate']:
            add('METADATA','WARNING','PDF creation and modification dates differ. This is a weak indicator, not evidence of forgery.',[{'document_id':d['id']}])
    for group in hashes.values():
        if len(group) > 1: add('DUPLICATE','WARNING','Identical SHA-256 checksum in multiple uploads',[{'document_id':d['id']} for d in group])
    images = [d for d in documents if (d.get('analysis') or {}).get('visual_hash')]
    for i, a in enumerate(images):
        for b in images[i+1:]:
            if a['checksum'] != b['checksum'] and (int(a['analysis']['visual_hash'],16) ^ int(b['analysis']['visual_hash'],16)).bit_count() <= 5:
                add('VISUAL_SIMILARITY','WARNING','Images have similar perceptual hashes; manual inspection required. Similarity does not prove manipulation.',[{'document_id':a['id']},{'document_id':b['id']}])
    return findings
