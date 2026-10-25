import io
from datetime import date
import pymupdf as fitz
import pytest
from PIL import Image
from app.document_ai.extract import inspect_file, extract, normalize, image_hash
from app.rules.engine import evaluate
from app.verification.adapters import MockAdapter, UnconfiguredAdapter, QRAdapter, DigitalSignatureAdapter
from app.reporting.reports import pdf_report, build_report

@pytest.fixture
def pdf_bytes():
    doc=fitz.open(); p=doc.new_page();p.insert_text((40,40),'DEMO certificate\nInstitution ID: DEMO-001\nInstitution Name: Fictional Institute\nExpiry Date: 2020-01-01\nFaculty Count: 12\nReference Number: DEMO-REF')
    data=doc.tobytes();doc.close();return data

def test_pdf_extraction_with_evidence(pdf_bytes):
    mime,digest=inspect_file(pdf_bytes,200000)
    assert mime=='application/pdf' and len(digest)==64
    result=extract(pdf_bytes,mime)
    assert result['classification']=='certificate'
    fields={f['field_name']:f for f in result['fields']}
    assert fields['institution_identifier']['normalized_value']=='DEMO-001'
    assert fields['expiry_date']['normalized_value']=='2020-01-01'
    assert all(f['page_number']==1 and f['excerpt'] and f['processed_at'] for f in result['fields'])
    assert fields['institution_identifier']['confidence'] is None

@pytest.mark.parametrize('data',[b'',b'not a pdf',b'%PDF-broken',b'<script>alert(1)</script>'])
def test_reject_bad_files(data):
    with pytest.raises(ValueError):inspect_file(data,1000)

def test_size_and_encryption(pdf_bytes):
    with pytest.raises(ValueError):inspect_file(pdf_bytes,20)
    d=fitz.open(stream=pdf_bytes,filetype='pdf')
    encrypted=d.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256,owner_pw='test',user_pw='test')
    with pytest.raises(ValueError):inspect_file(encrypted,200000)

def test_png_and_mocked_ocr(monkeypatch):
    im=Image.new('RGB',(80,80),'white');b=io.BytesIO();im.save(b,format='PNG');data=b.getvalue()
    mime,_=inspect_file(data,10000)
    assert mime=='image/png'
    monkeypatch.setattr('app.document_ai.extract.ocr',lambda image:('Faculty Count: 19',0.8))
    result=extract(data,mime)
    assert result['fields'][0]['normalized_value']=='19'
    assert result['fields'][0]['confidence']==0.8
    assert len(result['visual_hash'])==16

def test_normalization():
    assert normalize('institution_identifier',' demo-001 ')=='DEMO-001'
    assert normalize('faculty_count','0012')=='12'

def test_scanned_pdf_uses_ocr(monkeypatch):
    d=fitz.open();d.new_page();data=d.tobytes()
    monkeypatch.setattr('app.document_ai.extract.ocr',lambda image:('Institution ID: DEMO-SCAN',0.75))
    r=extract(data,'application/pdf')
    assert r['fields'][0]['normalized_value']=='DEMO-SCAN'

APP={'id':'app','category_id':'category'}
INST={'identifier':'DEMO-001'}
def rule(kind,params,**kwargs):return dict(id='v1',rule_id='r1',title='DEMO rule',evaluation_type=kind,parameters=params,severity='WARNING',**kwargs)
def field(name,value,doc='d1'):return dict(document_id=doc,field_name=name,normalized_value=value,page_number=1,excerpt='DEMO '+value)

def test_missing_expiry_mismatch_consistency_duplicate():
    docs=[dict(id='d1',document_category='certificate',checksum='same',processing_status='COMPLETE'),dict(id='d2',document_category='other',checksum='same',processing_status='COMPLETE')]
    fields=[field('expiry_date','2020-01-01'),field('institution_identifier','WRONG'),field('faculty_count','12'),field('faculty_count','18','d2')]
    rules=[rule('required_document',{'category':'undertaking'}),rule('expiry',{'field':'expiry_date'}),rule('comparison',{'field':'institution_identifier'})]
    r=evaluate(APP,INST,docs,fields,rules,date(2026,1,1))
    assert {f['category'] for f in r}>={'CHECKLIST','EXPIRY','IDENTITY','CONSISTENCY','DUPLICATE'}
    assert next(f for f in r if f['category']=='EXPIRY')['status']=='FAIL'
    assert all(f['evidence'] for f in r if f['category']!='CHECKLIST')
    assert all(f['rule_version_id']=='v1' for f in r if f['category'] in ('CHECKLIST','EXPIRY','IDENTITY'))

def test_inapplicable_rules_and_invalid_dates():
    rules=[rule('manual',{},category_ids=['different']),rule('manual',{},effective_from='2099-01-01'),rule('expiry',{'field':'expiry_date'})]
    r=evaluate(APP,INST,[],[field('expiry_date','not-date')],rules,date(2026,1,1))
    assert len(r)==1 and r[0]['status']=='INCONCLUSIVE'

def test_uncertain_fields_and_processing():
    r=evaluate(APP,INST,[dict(id='d',checksum='x',processing_status='ERROR')],[],[rule('required_field',{'field':'reference_number'})])
    assert all(f['status']=='INCONCLUSIVE' and f['manual_review_required'] for f in r)

@pytest.mark.parametrize('scenario,status',[('success','VERIFIED'),('mismatch','MISMATCH_DETECTED'),('unavailable','SOURCE_UNAVAILABLE'),('pending','PENDING')])
def test_simulation_label(scenario,status):
    r=MockAdapter(scenario).verify({},[])
    assert r['verification_mode']=='SIMULATED' and r['status']==status
    assert 'SIMULATED' in r['explanation']

@pytest.mark.parametrize('adapter',[UnconfiguredAdapter(),QRAdapter(),DigitalSignatureAdapter()])
def test_unconfigured_fails_safely(adapter):assert adapter.verify({},[])['status']=='UNSUPPORTED'

def test_report_pdf_preserves_notice_and_simulation():
    report=build_report(APP,[],[],[],[MockAdapter('success').verify({},[])],[],[])
    data=pdf_report(report)
    with fitz.open(stream=data,filetype='pdf') as d:
        text=''.join(p.get_text() for p in d)
        assert 'not an official' in text and 'SIMULATED' in text
        assert 'VERIFIED' in text
