"""Explicit operator recovery after a server crash. Stop all workers first."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.repositories.store import system_db
from app.services.workflow import now
if __name__=='__main__':
    if input('Workers must be stopped. Mark all active jobs interrupted? Type RECOVER: ')!='RECOVER':raise SystemExit('Cancelled')
    db=system_db();rows=db.table('processing_jobs').select('*').in_('status',['QUEUED','PROCESSING']).execute().data
    for row in rows:
        db.table('processing_jobs').update({'status':'ERROR','error':'Interrupted; operator recovery performed','finished_at':now()}).eq('id',row['id']).execute()
        db.table('application_documents').update({'processing_status':'ERROR'}).eq('id',row['document_id']).execute()
    db.table('applications').update({'status':'UNDER_MANUAL_REVIEW'}).eq('status','PROCESSING').execute()
    db.table('audit_logs').insert({'action':'OPERATOR_JOB_RECOVERY','entity_type':'processing_jobs','metadata':{'count':len(rows)}}).execute()
    print('Recovered',len(rows),'jobs. Restart server, then use Process / retry extraction.')
