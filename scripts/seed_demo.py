"""Seed synthetic workflow records into an explicitly configured Supabase project.
No credentials/accounts are invented. Run after provision_user.py with an existing institution user.
"""
import sys,argparse,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from generate_fixtures import SCENARIOS,make_pdf,generate
from app.repositories.store import system_db,insert,audit
from app.security.auth import Context
from app.document_ai.extract import inspect_file,extract
from app.services.workflow import validate,now
from app.core.config import settings
from app.verification.adapters import MockAdapter

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--user-id',required=True,type=uuid.UUID);parser.add_argument('--reviewer-id',type=uuid.UUID)
    args=parser.parse_args();db=system_db()
    rows=db.table('profiles').select('*').eq('id',str(args.user_id)).execute().data
    if not rows or rows[0]['role']!='institution':raise SystemExit('Provision an institution profile first.')
    profile=rows[0];institution=db.table('institutions').select('*').eq('id',profile['institution_id']).execute().data[0]
    ctx=Context(db,profile,'');generate()
    for scenario in SCENARIOS:
        a=insert('applications',dict(institution_id=profile['institution_id'],category_id='20000000-0000-4000-8000-000000000001',academic_year='2026-27',programme='DEMO scenario: '+scenario,created_by=str(args.user_id),status='DRAFT'))
        documents=[];duplicate=None
        for kind in ['undertaking','certificate','faculty_list','infrastructure']:
            if scenario=='missing_required_document' and kind=='undertaking':continue
            if scenario=='infrastructure_incomplete' and kind=='infrastructure':continue
            data,_=make_pdf(kind,scenario,institution['identifier'])
            if scenario=='duplicate_document':
                if duplicate is None:duplicate=data
                elif kind=='certificate':data=duplicate
            mime,checksum=inspect_file(data,20*1024*1024);did=str(uuid.uuid4());filename=f'DEMO-{scenario}-{kind}.pdf';path=f"{profile['institution_id']}/{a['id']}/{did}/{filename}"
            db.storage.from_(settings().supabase_documents_bucket).upload(path,data,{'content-type':mime})
            result=extract(data,mime)
            doc=insert('application_documents',dict(id=did,application_id=a['id'],document_category=kind,storage_path=path,original_filename=filename,mime_type=mime,size=len(data),checksum=checksum,version=1,processing_status='COMPLETE',analysis={k:v for k,v in result.items() if k!='fields'},uploaded_by=str(args.user_id)))
            if result['fields']:db.table('extracted_fields').insert([dict(f,document_id=did) for f in result['fields']]).execute()
            documents.append(doc)
            audit(ctx,'SYNTHETIC_DOCUMENT_SEEDED','application_documents',did,a['id'])
        if args.reviewer_id:insert('reviewer_assignments',{'application_id':a['id'],'reviewer_id':str(args.reviewer_id)})
        db.table('applications').update({'status':'PROCESSING','submitted_at':now()}).eq('id',a['id']).execute()
        validate(ctx,a)
        db.table('applications').update({'status':'PRELIMINARY_REVIEW_COMPLETE'}).eq('id',a['id']).execute()
        mode={'simulated_success':'success','simulated_mismatch':'mismatch','source_unavailable':'unavailable','verification_pending':'pending'}.get(scenario)
        if mode:
            result=MockAdapter(mode).verify(documents[0],[])
            insert('source_verifications',dict(result,document_id=documents[0]['id'],issuing_authority='DEMO fictional authority'))
        audit(ctx,'SYNTHETIC_APPLICATION_SEEDED','applications',a['id'],a['id'],{'scenario':scenario})
        print(scenario,a['reference'])
    print('Seeded 12 fictional applications. Re-running adds another set; use a dedicated test project.')
if __name__=='__main__':main()
