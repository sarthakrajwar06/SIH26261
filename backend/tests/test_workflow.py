"""Transport-to-processing workflow with a test-only in-memory Supabase double.
This is NOT a replacement database/auth provider in the delivered application.
Live cloud RLS and Storage tests remain separately opt-in.
"""
from collections import defaultdict
from types import SimpleNamespace
from uuid import uuid4
from datetime import datetime,timezone
from fastapi.testclient import TestClient
import pymupdf as fitz
import pytest
from app.api.routes import app
from app.security.auth import context,Context

class Query:
    def __init__(self,db,table):self.db=db;self.table=table;self.filters=[];self.operation='select';self.data=None;self.ordering=None;self.cap=None;self.bounds=None;self.head=False
    def select(self,*args,**kwargs):self.head=kwargs.get('head',False);return self
    def eq(self,k,v):self.filters.append(lambda r:r.get(k)==v);return self
    def in_(self,k,v):self.filters.append(lambda r:r.get(k) in v);return self
    def order(self,key,desc=False):self.ordering=(key,desc);return self
    def limit(self,n):self.cap=n;return self
    def range(self,a,b):self.bounds=(a,b);return self
    def insert(self,data):self.operation='insert';self.data=data;return self
    def update(self,data):self.operation='update';self.data=data;return self
    def delete(self):self.operation='delete';return self
    def execute(self):
        rows=[r for r in self.db.tables[self.table] if all(f(r) for f in self.filters)]
        if self.operation=='insert':
            rows=[]
            for item in (self.data if isinstance(self.data,list) else [self.data]):
                r={'id':str(uuid4()),'created_at':datetime.now(timezone.utc).isoformat(),**item}
                if self.table=='applications':r.update(status='DRAFT',reference='DEMO-TEST',updated_at=r['created_at'])
                if self.table=='application_documents':r.update(processing_status='QUEUED',analysis={})
                if self.table=='processing_jobs':r.update(status='QUEUED')
                self.db.tables[self.table].append(r);rows.append(r)
        elif self.operation=='update':
            for r in rows:r.update(self.data)
        elif self.operation=='delete':
            for r in rows:self.db.tables[self.table].remove(r)
        count=len(rows)
        if self.ordering:rows=sorted(rows,key=lambda x:x.get(self.ordering[0],''),reverse=self.ordering[1])
        if self.bounds:rows=rows[self.bounds[0]:self.bounds[1]+1]
        if self.cap is not None:rows=rows[:self.cap]
        return SimpleNamespace(data=[dict(r) for r in rows] if not self.head else [],count=count)

class Memory:
    def __init__(self):self.tables=defaultdict(list);self.files={};self.storage=self
    def table(self,t):return Query(self,t)
    def from_(self,b):return self
    def upload(self,path,data,*args):self.files[path]=data
    def download(self,path):return self.files[path]
    def remove(self,paths):
        for p in paths:self.files.pop(p,None)

def test_synthetic_submission_review_rectification_report(monkeypatch):
    db=Memory();uid=str(uuid4());iid=str(uuid4());cid=str(uuid4())
    db.tables['institutions']=[dict(id=iid,identifier='DEMO-001',name='DEMO Fictional Institute')]
    db.tables['application_categories']=[dict(id=cid,required_documents=['certificate','infrastructure'],demo_only=True)]
    ctx=Context(db,{'id':uid,'role':'institution','institution_id':iid},'test-only-token')
    app.dependency_overrides[context]=lambda:ctx
    for module in ['app.api.routes','app.repositories.store','app.services.workflow']:
        monkeypatch.setattr(module+'.system_db',lambda:db)
    try:
        client=TestClient(app)
        response=client.post('/api/v1/applications',json={'institution_id':iid,'category_id':cid,'academic_year':'2026-27','programme':'DEMO'})
        assert response.status_code==201,response.text
        aid=response.json()['id'];base='/api/v1/applications/'+aid
        assert client.post(base+'/submit').status_code==422
        d=fitz.open();p=d.new_page();p.insert_text((40,40),'DEMO certificate\nInstitution ID: DEMO-001\nExpiry Date: 2020-01-01');data=d.tobytes()
        r=client.post(base+'/documents',data={'document_category':'certificate'},files={'file':('demo.pdf',data,'application/pdf')})
        assert r.status_code==201,r.text
        did=r.json()['id']
        assert client.post(base+'/submit').status_code==200
        assert client.get(base).json()['status']=='PRELIMINARY_REVIEW_COMPLETE'
        assert client.get('/api/v1/documents/'+did).json()['fields']
        assert client.post(base+'/documents',data={'document_category':'other'},files={'file':('blocked.pdf',data)}).status_code==409
        fs=client.get(base+'/findings').json()['items']
        assert any(f['expected_value']=='infrastructure' for f in fs)
        ctx.profile['role']='reviewer'
        r=client.post(base+'/review-actions',json={'action':'RECTIFICATION_REQUIRED','reason':'DEMO please provide infrastructure evidence.'})
        assert r.status_code==200,r.text
        ctx.profile['role']='institution'
        assert client.post(base+'/review-actions',json={'action':'CLOSED','reason':'Unauthorized closure attempt'}).status_code==403
        r=client.post(base+'/documents',data={'document_category':'infrastructure'},files={'file':('evidence.pdf',data)})
        assert r.status_code==201
        assert client.post(base+'/submit').status_code==200
        assert any(f['category']=='DUPLICATE' for f in client.get(base+'/findings').json()['items'])
        ctx.profile['role']='reviewer'
        assert client.post('/api/v1/documents/'+did+'/verify',json={'mode':'SIMULATED','scenario':'success'}).json()['verification_mode']=='SIMULATED'
        assert client.post(base+'/review-actions',json={'action':'REVIEWED','reason':'DEMO original evidence inspected; no official decision.'}).status_code==200
        report=client.get(base+'/report')
        assert report.status_code==200 and report.json()['verifications'][0]['verification_mode']=='SIMULATED'
        pdf=client.get(base+'/report.pdf')
        assert pdf.status_code==200 and pdf.content.startswith(b'%PDF-')
        assert len(db.tables['review_actions'])==2
        assert len(db.tables['audit_logs'])>=10
        assert len(db.tables['reports'])==2
        assert any(n['type']=='PROCESSING_COMPLETE' for n in db.tables['notifications'])
    finally:app.dependency_overrides.clear()
