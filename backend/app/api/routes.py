import re, time, uuid, json, logging
from collections import defaultdict, deque
from uuid import UUID
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from starlette.concurrency import run_in_threadpool
from app.core.config import settings
from app.core.request_context import request_id
from app.security.auth import context, Context
from app.schemas.models import ApplicationCreate, ApplicationPatch, Review, RuleCreate, RulePatch, RuleVersion, VerifyRequest, ProfilePatch, Assignment
from app.repositories.store import system_db, insert, update, audit, notify
from app.services.workflow import current_documents, active_rules, validate, process_job, process_application, now
from app.document_ai.extract import inspect_file
from app.verification.adapters import MockAdapter, UnconfiguredAdapter, QRAdapter, DigitalSignatureAdapter
from app.reporting.reports import build_report, pdf_report

app = FastAPI(title='AICTE Insight',version='0.1.0', description='Preliminary scrutiny; not an official approval system.')
app.add_middleware(CORSMiddleware,allow_origins=[settings().frontend_url],allow_methods=['GET','POST','PATCH'],allow_headers=['Authorization','Content-Type'],allow_credentials=False)
logger = logging.getLogger('insight')
# Single-process local rate limit. Deploy behind an authenticated distributed gateway in production.
requests = defaultdict(deque)
@app.middleware('http')
async def protections(request: Request, call_next):
    key = request.client.host if request.client else 'unknown'
    q = requests[key]; current = time.monotonic()
    while q and q[0] < current-60: q.popleft()
    if len(q) >= 180: return JSONResponse({'detail':'Rate limit exceeded'},429)
    q.append(current)
    if len(requests)>10000:
        for k in list(requests):
            if not requests[k] or requests[k][-1]<current-60: del requests[k]
    # Also enforced while reading UploadFile, not only by trusting Content-Length.
    try:
        if int(request.headers.get('content-length','0')) > (settings().max_upload_size_mb+1)*1024*1024:
            return JSONResponse({'detail':'Request exceeds upload limit'},413)
    except ValueError: return JSONResponse({'detail':'Invalid content length'},400)
    correlation=str(uuid.uuid4()); marker=request_id.set(correlation)
    try:
        response = await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Cache-Control']='no-store'
        response.headers['X-Request-ID']=correlation
        return response
    finally:
        request_id.reset(marker)

@app.exception_handler(Exception)
async def safe_error(request, exc):
    logger.error('Request failed (%s)',type(exc).__name__)
    return JSONResponse({'detail':'Operation failed. Check server configuration or retry; no changes should be assumed successful.'},500)

P='/api/v1'
@app.get('/health')
def health(): return {'status':'ok','configured':bool(settings().supabase_url),'worker':'in-process; not durable'}
@app.get(P+'/auth/me')
def me(ctx: Context=Depends(context)): return ctx.profile

def listing(ctx, table, page=1, page_size=25, **filters):
    if page<1 or not 1<=page_size<=100: raise HTTPException(422,'Invalid pagination')
    q=ctx.db.table(table).select('*',count='exact')
    for k,v in filters.items():
        if v is not None: q=q.eq(k,str(v))
    r=q.range((page-1)*page_size,page*page_size-1).execute()
    return {'items':r.data,'total':r.count,'page':page,'page_size':page_size}

@app.get(P+'/institutions')
def institutions(ctx: Context=Depends(context)): return listing(ctx,'institutions')
@app.get(P+'/institutions/{id}')
def institution(id:UUID,ctx:Context=Depends(context)): return ctx.one('institutions',id)
@app.get(P+'/categories')
def categories(ctx:Context=Depends(context)): return listing(ctx,'application_categories',page_size=100)
@app.get(P+'/applications')
def applications(page:int=1,page_size:int=25,status:str|None=None,search:str='',sort:str='newest',ctx:Context=Depends(context)):
    if page<1 or not 1<=page_size<=100: raise HTTPException(422,'Invalid pagination')
    q=ctx.db.table('applications').select('*',count='exact')
    if status: q=q.eq('status',status)
    if search:
        if len(search)>80 or not re.fullmatch(r'[\w -]+',search): raise HTTPException(422,'Search supports letters, numbers, spaces and hyphens')
        q=q.ilike('reference','%'+search+'%')
    r=q.order('created_at',desc=sort!='oldest').range((page-1)*page_size,page*page_size-1).execute()
    return {'items':r.data,'total':r.count,'page':page,'page_size':page_size}
@app.get(P+'/dashboard')
def dashboard(ctx:Context=Depends(context)):
    # Head-only exact counts, not a truncated row sample.
    states=['DRAFT','SUBMITTED','PROCESSING','PRELIMINARY_REVIEW_COMPLETE','RECTIFICATION_REQUIRED','UNDER_MANUAL_REVIEW','READY_FOR_OFFICIAL_REVIEW','CLOSED']
    counts={s:ctx.db.table('applications').select('id',count='exact',head=True).eq('status',s).execute().count for s in states}
    return {'counts':counts,'total':sum(counts.values()),'recent':ctx.db.table('applications').select('*').order('created_at',desc=True).limit(5).execute().data}
@app.post(P+'/applications',status_code=201)
def create_application(data:ApplicationCreate,ctx:Context=Depends(context)):
    ctx.require('institution','admin')
    ctx.one('institutions',data.institution_id); ctx.one('application_categories',data.category_id)
    if ctx.role=='institution' and str(data.institution_id)!=ctx.profile['institution_id']: raise HTTPException(403,'Institution scope mismatch')
    row=insert('applications',dict(data.model_dump(mode='json'),created_by=ctx.uid))
    audit(ctx,'APPLICATION_CREATED','applications',row['id'],row['id'])
    return row
@app.get(P+'/applications/{id}')
def application(id:UUID,ctx:Context=Depends(context)): return ctx.one('applications',id)

def editable(ctx,id):
    ctx.require('institution','admin')
    a=ctx.one('applications',id)
    if a['status'] not in ('DRAFT','RECTIFICATION_REQUIRED'): raise HTTPException(409,'Application is locked; reviewer must request rectification')
    return a
@app.patch(P+'/applications/{id}')
def patch_application(id:UUID,data:ApplicationPatch,ctx:Context=Depends(context)):
    editable(ctx,id); update('applications',id,dict(data.model_dump(),updated_at=now()))
    audit(ctx,'APPLICATION_UPDATED','applications',id,id)
    return ctx.one('applications',id)
@app.post(P+'/applications/{id}/submit')
def submit(id:UUID,bg:BackgroundTasks,ctx:Context=Depends(context)):
    a=editable(ctx,id)
    docs=current_documents(ctx,id)
    if not docs: raise HTTPException(422,'Upload at least one document. Missing checklist evidence will be flagged, not treated as statutory rejection.')
    for d in docs:
        active=ctx.db.table('processing_jobs').select('id').eq('document_id',d['id']).in_('status',['QUEUED','PROCESSING']).execute().data
        if active: raise HTTPException(409,'A document job is active; wait for completion before submitting')
    # Compare-and-set transition prevents duplicate submissions in competing requests.
    changed=system_db().table('applications').update({'status':'PROCESSING','submitted_at':now(),'updated_at':now()}).eq('id',str(id)).eq('status',a['status']).execute().data
    if not changed: raise HTTPException(409,'Application changed; reload')
    jobs=[]
    for d in docs:
        if d['processing_status']!='COMPLETE':
            existing=ctx.db.table('processing_jobs').select('*').eq('document_id',d['id']).in_('status',['QUEUED','PROCESSING']).execute().data
            job=existing[0] if existing else insert('processing_jobs',{'document_id':d['id']})
            jobs.append((d,job))
    audit(ctx,'APPLICATION_SUBMITTED','applications',id,id)
    bg.add_task(process_application,ctx,a,jobs)
    return changed[0]
@app.post(P+'/applications/{id}/rectification')
def rectification(id:UUID,data:Review,ctx:Context=Depends(context)):
    return perform_review(id,Review(action='RECTIFICATION_REQUIRED',reason=data.reason),ctx)

@app.post(P+'/applications/{id}/documents',status_code=201)
async def upload(id:UUID,document_category:str=Form(...),file:UploadFile=File(...),ctx:Context=Depends(context)):
    a=await run_in_threadpool(editable,ctx,id)
    if not re.fullmatch(r'[a-z_]{3,60}',document_category): raise HTTPException(422,'Invalid document category')
    data=await file.read(min(settings().max_upload_size_mb,20)*1024*1024+1)
    try: mime,checksum=await run_in_threadpool(inspect_file,data,min(settings().max_upload_size_mb,20)*1024*1024)
    except ValueError as exc: raise HTTPException(422,str(exc))
    filename=re.sub(r'[^A-Za-z0-9._-]','_', (file.filename or 'document').replace('\\','/').split('/')[-1])[:100]
    did=str(uuid.uuid4()); path=f"{a['institution_id']}/{id}/{did}/{filename}"
    versions=await run_in_threadpool(lambda:ctx.db.table('application_documents').select('version').eq('application_id',str(id)).eq('document_category',document_category).order('version',desc=True).limit(1).execute().data)
    version=versions[0]['version']+1 if versions else 1
    db=system_db()
    await run_in_threadpool(lambda:db.storage.from_(settings().supabase_documents_bucket).upload(path,data,{'content-type':mime,'upsert':'false'}))
    try:
        row=await run_in_threadpool(insert,'application_documents',dict(id=did,application_id=str(id),document_category=document_category,storage_path=path,original_filename=filename,mime_type=mime,size=len(data),checksum=checksum,version=version,uploaded_by=ctx.uid))
    except Exception:
        await run_in_threadpool(lambda:db.storage.from_(settings().supabase_documents_bucket).remove([path]))
        raise
    await run_in_threadpool(audit,ctx,'DOCUMENT_UPLOADED','application_documents',did,id,{'version':version,'checksum':checksum})
    return row
@app.get(P+'/applications/{id}/documents')
def documents(id:UUID,ctx:Context=Depends(context)):
    ctx.one('applications',id)
    return listing(ctx,'application_documents',page_size=100,application_id=id)
@app.get(P+'/documents/{id}')
def document(id:UUID,ctx:Context=Depends(context)):
    d=ctx.one('application_documents',id)
    d['fields']=ctx.db.table('extracted_fields').select('*').eq('document_id',str(id)).execute().data
    d['jobs']=ctx.db.table('processing_jobs').select('*').eq('document_id',str(id)).execute().data
    return d
@app.get(P+'/documents/{id}/content')
def content(id:UUID,ctx:Context=Depends(context)):
    d=ctx.one('application_documents',id)
    data=system_db().storage.from_(settings().supabase_documents_bucket).download(d['storage_path'])
    return Response(data,media_type=d['mime_type'],headers={'Content-Disposition':f'inline; filename="{d["original_filename"]}"','Content-Security-Policy':"sandbox; default-src 'none'"})
@app.post(P+'/documents/{id}/process')
def process(id:UUID,bg:BackgroundTasks,ctx:Context=Depends(context)):
    d=ctx.one('application_documents',id); a=ctx.one('applications',d['application_id'])
    if ctx.role=='institution' and a['status'] not in ('DRAFT','RECTIFICATION_REQUIRED'): raise HTTPException(409,'Application locked')
    active=ctx.db.table('processing_jobs').select('id').eq('document_id',str(id)).in_('status',['QUEUED','PROCESSING']).execute().data
    if active: raise HTTPException(409,'Active job exists; see recovery documentation for interrupted jobs')
    job=insert('processing_jobs',{'document_id':str(id)})
    audit(ctx,'EXTRACTION_QUEUED','processing_jobs',job['id'],d['application_id'])
    bg.add_task(process_job,ctx,d,job['id']); return job
@app.post(P+'/applications/{id}/validate')
def validate_application(id:UUID,ctx:Context=Depends(context)):
    a=ctx.one('applications',id)
    if a['status']=='PROCESSING': raise HTTPException(409,'Wait for document processing')
    return validate(ctx,a)
@app.get(P+'/applications/{id}/findings')
def findings(id:UUID,history:bool=False,ctx:Context=Depends(context)):
    ctx.one('applications',id)
    q=ctx.db.table('validation_findings').select('*').eq('application_id',str(id))
    if not history:
        runs=ctx.db.table('validation_runs').select('id').eq('application_id',str(id)).order('created_at',desc=True).limit(1).execute().data
        if not runs: return {'items':[]}
        q=q.eq('run_id',runs[0]['id'])
    return {'items':q.execute().data}
@app.get(P+'/findings/{id}')
def finding(id:UUID,ctx:Context=Depends(context)): return ctx.one('validation_findings',id)

@app.post(P+'/documents/{id}/verify')
def verify(id:UUID,data:VerifyRequest,ctx:Context=Depends(context)):
    ctx.require('reviewer','admin'); d=ctx.one('application_documents',id)
    fields=ctx.db.table('extracted_fields').select('*').eq('document_id',str(id)).execute().data
    adapter=MockAdapter(data.scenario) if data.mode=='SIMULATED' else QRAdapter() if data.mode=='QR' else DigitalSignatureAdapter() if data.mode=='DIGITAL_SIGNATURE' else UnconfiguredAdapter(data.mode)
    result=adapter.verify(d,fields)
    if data.mode=='MANUAL': result.update(status='MANUAL_REVIEW_REQUIRED',explanation='Manual follow-up requested. Record the authority response as a reasoned review action; no official verification asserted.')
    row=insert('source_verifications',dict(result,document_id=str(id),issuing_authority=data.authority))
    audit(ctx,'SOURCE_VERIFICATION','source_verifications',row['id'],d['application_id'],{'mode':data.mode,'status':result['status']})
    notify(ctx.one('applications',d['application_id']),'SOURCE_VERIFICATION',f"{data.mode}: {result['status']}")
    return row
@app.get(P+'/documents/{id}/verification')
def verifications(id:UUID,ctx:Context=Depends(context)):
    ctx.one('application_documents',id); return listing(ctx,'source_verifications',document_id=id)
@app.get(P+'/verifications/{id}')
def verification(id:UUID,ctx:Context=Depends(context)): return ctx.one('source_verifications',id)

@app.get(P+'/rules')
def rules(ctx:Context=Depends(context)):
    return {'items':ctx.db.table('validation_rules').select('*,validation_rule_versions(*)').execute().data}
@app.get(P+'/rules/{id}')
def rule(id:UUID,ctx:Context=Depends(context)):
    row=ctx.one('validation_rules',id); row['versions']=ctx.db.table('validation_rule_versions').select('*').eq('rule_id',str(id)).order('version',desc=True).execute().data; return row

def check_rule(v):
    if not v.demo_only and not v.expert_confirmed: raise HTTPException(422,'Production rules require documented domain-expert confirmation')
    if v.effective_to and v.effective_to<v.effective_from: raise HTTPException(422,'Invalid effective date range')
    required={'required_document':['category'],'required_field':['field'],'expiry':['field'],'comparison':['field','institution_field'],'threshold':['field','minimum']}.get(v.evaluation_type,[])
    if any(k not in v.parameters for k in required): raise HTTPException(422,'Missing evaluator parameters: '+', '.join(required))
@app.post(P+'/rules',status_code=201)
def create_rule(data:RuleCreate,ctx:Context=Depends(context)):
    ctx.require('admin'); check_rule(data.version)
    row=insert('validation_rules',{'code':data.code,'enabled':False})
    insert('validation_rule_versions',dict(data.version.model_dump(mode='json'),rule_id=row['id'],version=1))
    update('validation_rules',row['id'],{'enabled':data.enabled})
    audit(ctx,'RULE_CREATED','validation_rules',row['id']); return row
@app.patch(P+'/rules/{id}')
def patch_rule(id:UUID,data:RulePatch,ctx:Context=Depends(context)):
    ctx.require('admin'); ctx.one('validation_rules',id)
    update('validation_rules',id,data.model_dump()); audit(ctx,'RULE_TOGGLED','validation_rules',id)
    return ctx.one('validation_rules',id)
@app.post(P+'/rules/{id}/versions')
def version_rule(id:UUID,data:RuleVersion,ctx:Context=Depends(context)):
    ctx.require('admin'); check_rule(data); ctx.one('validation_rules',id)
    rows=ctx.db.table('validation_rule_versions').select('version').eq('rule_id',str(id)).order('version',desc=True).limit(1).execute().data
    row=insert('validation_rule_versions',dict(data.model_dump(mode='json'),rule_id=str(id),version=(rows[0]['version']+1 if rows else 1)))
    audit(ctx,'RULE_VERSION_ADDED','validation_rule_versions',row['id']); return row

def perform_review(id:UUID,data:Review,ctx:Context,finding_id=None):
    ctx.require('reviewer','admin'); a=ctx.one('applications',id)
    if a['status'] in ('DRAFT','PROCESSING','CLOSED'): raise HTTPException(409,'Case cannot be reviewed in current state')
    row=insert('review_actions',dict(application_id=str(id),finding_id=finding_id,reviewer_id=ctx.uid,**data.model_dump()))
    state=data.action if data.action in ('RECTIFICATION_REQUIRED','READY_FOR_OFFICIAL_REVIEW','CLOSED') else 'UNDER_MANUAL_REVIEW'
    update('applications',id,{'status':state,'updated_at':now()})
    audit(ctx,'REVIEW_'+data.action,'review_actions',row['id'],id)
    notify(a,'REVIEW_ACTION',data.action+': '+data.reason)
    return row
@app.post(P+'/applications/{id}/review-actions')
def review_action(id:UUID,data:Review,ctx:Context=Depends(context)):
    return perform_review(id,data,ctx)
@app.post(P+'/findings/{id}/review')
def review_finding(id:UUID,data:Review,ctx:Context=Depends(context)):
    ctx.require('reviewer','admin'); f=ctx.one('validation_findings',id)
    return perform_review(UUID(f['application_id']),data,ctx,finding_id=str(id))
@app.get(P+'/applications/{id}/review-actions')
def review_history(id:UUID,ctx:Context=Depends(context)):
    ctx.one('applications',id); return listing(ctx,'review_actions',page_size=100,application_id=id)
@app.get(P+'/applications/{id}/audit')
def application_audit(id:UUID,page:int=1,ctx:Context=Depends(context)):
    ctx.one('applications',id); return listing(ctx,'audit_logs',page=page,application_id=id)
@app.get(P+'/audit')
def all_audit(page:int=1,ctx:Context=Depends(context)):
    ctx.require('admin'); return listing(ctx,'audit_logs',page=page)


def report_data(ctx,id):
    a=ctx.one('applications',id); docs=current_documents(ctx,id); fields=[]; verifications=[]
    for d in docs:
        fields.extend(ctx.db.table('extracted_fields').select('*').eq('document_id',d['id']).execute().data)
        verifications.extend(ctx.db.table('source_verifications').select('*').eq('document_id',d['id']).execute().data)
    fs=findings(id,False,ctx)['items']
    vids={f['rule_version_id'] for f in fs if f.get('rule_version_id')}
    versions=ctx.db.table('validation_rule_versions').select('*').in_('id',list(vids)).execute().data if vids else []
    report=build_report(a,docs,fields,fs,verifications,ctx.db.table('review_actions').select('*').eq('application_id',str(id)).execute().data,versions)
    category=ctx.one('application_categories',a['category_id'])
    report['applicable_checklist']=category
    report['missing_documents']=[c for c in category['required_documents'] if not any(d['document_category']==c for d in docs)]
    return report

def save_report(ctx,id,data,format):
    a=ctx.one('applications',id); rid=str(uuid.uuid4()); path=f"{a['institution_id']}/{id}/{rid}/report.{format}"
    system_db().storage.from_(settings().supabase_reports_bucket).upload(path,data,{'content-type':'application/pdf' if format=='pdf' else 'application/json'})
    insert('reports',{'id':rid,'application_id':str(id),'storage_path':path,'format':format})
    audit(ctx,'REPORT_GENERATED','reports',rid,id)
@app.get(P+'/applications/{id}/report')
def json_report(id:UUID,ctx:Context=Depends(context)):
    report=report_data(ctx,id); save_report(ctx,id,json.dumps(report).encode(),'json'); return report
@app.get(P+'/applications/{id}/report.pdf')
def pdf(id:UUID,ctx:Context=Depends(context)):
    data=pdf_report(report_data(ctx,id)); save_report(ctx,id,data,'pdf')
    return Response(data,media_type='application/pdf',headers={'Content-Disposition':'attachment; filename="preliminary-report.pdf"'})
@app.get(P+'/notifications')
def notifications(ctx:Context=Depends(context)): return listing(ctx,'notifications',page_size=100,recipient_id=ctx.uid)
@app.post(P+'/notifications/{id}/read')
def read_notification(id:UUID,ctx:Context=Depends(context)):
    n=ctx.one('notifications',id)
    if n['recipient_id']!=ctx.uid: raise HTTPException(404,'Not found')
    update('notifications',id,{'read_at':now()}); return {'ok':True}
@app.get(P+'/admin/users')
def users(ctx:Context=Depends(context)):
    ctx.require('admin'); return listing(ctx,'profiles',page_size=100)
@app.patch(P+'/admin/users/{id}')
def user_patch(id:UUID,data:ProfilePatch,ctx:Context=Depends(context)):
    ctx.require('admin'); ctx.one('profiles',id)
    if str(id)==ctx.uid: raise HTTPException(409,'Use a second trusted administrator to change your own role')
    if data.role=='institution' and not data.institution_id: raise HTTPException(422,'Institution required')
    if data.institution_id: ctx.one('institutions',data.institution_id)
    update('profiles',id,dict(data.model_dump(mode='json'),updated_at=now()))
    audit(ctx,'PROFILE_CHANGED','profiles',id,metadata=data.model_dump(mode='json')); return {'ok':True}
@app.post(P+'/applications/{id}/assign')
def assign(id:UUID,data:Assignment,ctx:Context=Depends(context)):
    ctx.require('admin'); ctx.one('applications',id); p=ctx.one('profiles',data.reviewer_id)
    if p['role']!='reviewer' or p['account_status']!='ACTIVE': raise HTTPException(422,'Active reviewer required')
    row=insert('reviewer_assignments',dict(application_id=str(id),reviewer_id=str(data.reviewer_id)))
    audit(ctx,'REVIEWER_ASSIGNED','reviewer_assignments',row['id'],id); return row
@app.get(P+'/system/integrations')
def integrations(ctx:Context=Depends(context)):
    return {'items':[{'name':n,'status':status,'mode':mode} for n,status,mode in [
        ('Supabase Auth / Database / Storage','CONFIGURED','LIVE'),('Local PDF extraction','AVAILABLE','LOCAL'),
        ('Tesseract OCR','REQUIRES_LOCAL_BINARY','LOCAL'),('Issuing-authority verification','NOT_CONFIGURED','OFFICIAL'),
        ('Synthetic verification adapter','AVAILABLE','SIMULATED'),('AICTE official services','NOT_CONFIGURED','OFFICIAL'),
        ('QR / digital signature trust','NOT_CONFIGURED','OFFICIAL'),('Infrastructure vision model','NOT_CONFIGURED','LOCAL'),
        ('Paid LLM','DISABLED','NONE'),('Email / SMS','NOT_CONFIGURED','EXTERNAL')]],
        'retention_days':settings().retention_days,'retention_enforcement':'Manual purge required; no automatic deletion job configured'}

from pydantic import BaseModel,Field
class InstitutionInput(BaseModel):
    name:str=Field(min_length=3,max_length=250)
    identifier:str=Field(min_length=3,max_length=100)
    location:str=Field(default='',max_length=250)
    institution_type:str=Field(default='DEMO',max_length=100)
class CategoryInput(BaseModel):
    name:str=Field(min_length=3,max_length=200)
    description:str=Field(min_length=10,max_length=2000)
    required_documents:list[str]=Field(default_factory=list,max_length=40)
    demo_only:bool=True

@app.post(P+'/institutions',status_code=201)
def create_institution(data:InstitutionInput,ctx:Context=Depends(context)):
    ctx.require('admin');r=insert('institutions',data.model_dump());audit(ctx,'INSTITUTION_CREATED','institutions',r['id']);return r
@app.post(P+'/categories',status_code=201)
def create_category(data:CategoryInput,ctx:Context=Depends(context)):
    ctx.require('admin')
    if any(not re.fullmatch(r'[a-z_]{3,60}',x) for x in data.required_documents):raise HTTPException(422,'Invalid checklist category')
    if not data.demo_only:raise HTTPException(422,'Production checklists must be configured through a reviewed migration with authoritative references')
    r=insert('application_categories',data.model_dump());audit(ctx,'CATEGORY_CREATED','application_categories',r['id']);return r
@app.get(P+'/applications/{id}/versions')
def application_versions(id:UUID,ctx:Context=Depends(context)):
    ctx.one('applications',id);return listing(ctx,'application_versions',page_size=100,application_id=id)
