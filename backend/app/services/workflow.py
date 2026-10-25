from datetime import datetime, timezone
from app.repositories.store import system_db, insert, update, audit, notify
from app.document_ai.extract import extract
from app.core.config import settings
from app.rules.engine import evaluate

def now(): return datetime.now(timezone.utc).isoformat()

def current_documents(ctx, application_id):
    docs = ctx.db.table('application_documents').select('*').eq('application_id',str(application_id)).order('version',desc=True).execute().data
    # All versions preserved. Only latest category version used for scrutiny.
    latest = {}
    for d in docs: latest.setdefault(d['document_category'],d)
    return list(latest.values())

def active_rules(ctx, application=None):
    identities = ctx.db.table('validation_rules').select('*').eq('enabled',True).execute().data
    versions = ctx.db.table('validation_rule_versions').select('*').order('version',desc=True).execute().data
    ids = {r['id'] for r in identities}; result = {}
    for v in versions:
        if v.get('effective_from','0001-01-01') > now()[:10] or (v.get('effective_to') and v['effective_to'] < now()[:10]): continue
        if application and v.get('category_ids') and application['category_id'] not in v['category_ids']: continue
        if v['rule_id'] in ids: result.setdefault(v['rule_id'],v)
    return list(result.values())

def validate(ctx, application):
    docs = current_documents(ctx,application['id'])
    fields = []
    for d in docs: fields.extend(ctx.db.table('extracted_fields').select('*').eq('document_id',d['id']).execute().data)
    institution = ctx.one('institutions',application['institution_id'])
    findings = evaluate(application,institution,docs,fields,active_rules(ctx,application))
    # Checklist belongs to category too; supports new categories before rules are authored.
    category = ctx.one('application_categories',application['category_id'])
    for kind in category['required_documents']:
        if not any(d['document_category']==kind for d in docs) and not any(f['category']=='CHECKLIST' and f['expected_value']==kind for f in findings):
            findings.append(dict(application_id=application['id'],category='CHECKLIST',status='FAIL',severity='WARNING',explanation='Category checklist evidence missing (DEMO)' if category['demo_only'] else 'Category checklist evidence missing',expected_value=kind,observed_value='missing',evidence=[],suggested_action='Supply evidence',manual_review_required=True))
    run = insert('validation_runs',{'application_id':application['id']})
    if findings: system_db().table('validation_findings').insert([dict(f,run_id=run['id']) for f in findings]).execute()
    audit(ctx,'VALIDATION_RUN','validation_runs',run['id'],application['id'])
    notify(application,'VALIDATION_COMPLETE','Preliminary findings are available. These are not an official decision.')
    return findings

def process_job(ctx, document, job_id):
    db = system_db()
    try:
        claimed=db.table('processing_jobs').update({'status':'PROCESSING'}).eq('id',str(job_id)).eq('status','QUEUED').execute().data
        if not claimed: return
        update('application_documents',document['id'],{'processing_status':'PROCESSING'})
        data = db.storage.from_(settings().supabase_documents_bucket).download(document['storage_path'])
        result = extract(data,document['mime_type'],settings().ocr_engine)
        db.table('extracted_fields').delete().eq('document_id',document['id']).execute()
        if result['fields']:
            db.table('extracted_fields').insert([dict(f,document_id=document['id']) for f in result['fields']]).execute()
        analysis = {k:v for k,v in result.items() if k!='fields'}
        update('application_documents',document['id'],{'processing_status':'COMPLETE','analysis':analysis})
        update('processing_jobs',job_id,{'status':'COMPLETE','finished_at':now()})
        audit(ctx,'EXTRACTION_COMPLETE','application_documents',document['id'],document['application_id'])
    except Exception:
        update('application_documents',document['id'],{'processing_status':'ERROR'})
        update('processing_jobs',job_id,{'status':'ERROR','error':'Extraction failed. Check file integrity, OCR installation and server configuration.','finished_at':now()})
        audit(ctx,'EXTRACTION_FAILED','application_documents',document['id'],document['application_id'])

def process_application(ctx, application, jobs):
    for document, job in jobs: process_job(ctx, document, job['id'])
    try:
        validate(ctx,application)
        update('applications',application['id'],{'status':'PRELIMINARY_REVIEW_COMPLETE','updated_at':now()})
        notify(application,'PROCESSING_COMPLETE','Document processing finished; review inconclusive findings manually.')
    except Exception:
        update('applications',application['id'],{'status':'UNDER_MANUAL_REVIEW','updated_at':now()})
        audit(ctx,'PROCESSING_REQUIRES_MANUAL_REVIEW','applications',application['id'],application['id'])
