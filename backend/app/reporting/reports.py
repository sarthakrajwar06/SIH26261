import json
from datetime import datetime, timezone
import pymupdf as fitz
from app.rules.engine import NOTICE

def build_report(application, documents, fields, findings, verifications, actions, rules):
    return dict(application=application, documents=documents, extracted_fields=fields, findings=findings,
                verifications=verifications, reviewer_observations=actions, rule_versions=rules,
                generated_at=datetime.now(timezone.utc).isoformat(), notice=NOTICE,
                simulated_notice='SIMULATED verification is not official verification.',
                outstanding_issues=[f for f in findings if f['status'] not in ('PASS','NOT_APPLICABLE')])

def pdf_report(report):
    # Plain text into PDF (no HTML/JS injection), paginate without truncating evidence.
    doc = fitz.open()
    lines = ['AICTE INSIGHT | PRELIMINARY REPORT', report['notice'], report['simulated_notice'], '']
    import textwrap
    for line in json.dumps(report, indent=2, ensure_ascii=True).splitlines():
        lines.extend(textwrap.wrap(line, 100, replace_whitespace=False) or [''])
    for offset in range(0,len(lines),55):
        page = doc.new_page()
        page.insert_text((36,40),'\n'.join(lines[offset:offset+55]), fontsize=8, fontname='cour')
    data = doc.tobytes()
    doc.close()
    return data
