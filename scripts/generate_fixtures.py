"""Repeatable fictional PDFs and labels. No real institution or person data."""
import json
from pathlib import Path
import pymupdf as fitz
ROOT=Path(__file__).resolve().parents[1]
SCENARIOS=['complete','missing_required_document','expired_certificate','identifier_mismatch','faculty_discrepancy','duplicate_document','metadata_anomaly','simulated_success','simulated_mismatch','source_unavailable','verification_pending','infrastructure_incomplete']

def make_pdf(kind,scenario,identifier='DEMO-MERIDIAN-001'):
    fields={'institution_identifier': 'DEMO-WRONG-999' if scenario=='identifier_mismatch' else identifier,
            'institution_name':'DEMO Meridian Institute of Technology',
            'reference_number':f'DEMO-{scenario.upper()}-{kind.upper()}',
            'faculty_count':'18' if scenario=='faculty_discrepancy' and kind=='faculty_list' else '24'}
    if kind=='certificate':fields['expiry_date']='2020-01-01' if scenario=='expired_certificate' else '2099-12-31'
    text=['SYNTHETIC DEMO DOCUMENT - NOT VALID FOR OFFICIAL USE',kind.replace('_',' ').upper(),
          'Institution ID: '+fields['institution_identifier'],'Institution Name: '+fields['institution_name'],
          'Reference Number: '+fields['reference_number'],'Faculty Count: '+fields['faculty_count']]
    if 'expiry_date' in fields:text.append('Expiry Date: '+fields['expiry_date'])
    if kind=='infrastructure':text.append('DEMO infrastructure evidence association only; physical inspection required.')
    d=fitz.open();p=d.new_page();p.insert_text((40,55),'\n'.join(text),fontsize=10)
    meta={'title':'SYNTHETIC DEMO '+scenario,'author':'Fictional test generator','creationDate':'D:20260101000000Z','modDate':'D:20261001000000Z' if scenario=='metadata_anomaly' else 'D:20260101000000Z'}
    d.set_metadata(meta);data=d.tobytes();d.close()
    return data,fields

def generate():
    target=ROOT/'data/synthetic';target.mkdir(parents=True,exist_ok=True);labels=[]
    for scenario in SCENARIOS:
        data,fields=make_pdf('certificate',scenario)
        path=target/(scenario+'.pdf');path.write_bytes(data)
        labels.append({'file':path.name,'scenario':scenario,'fields':fields})
    (ROOT/'data/fixtures/labels.json').write_text(json.dumps(labels,indent=2))
    return labels
if __name__=='__main__':
    labels=generate();print(f'Generated {len(labels)} fictional PDFs in data/synthetic (ignored by Git).')
