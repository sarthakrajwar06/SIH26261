"""Trusted local operator only. Uses server secret; never expose as a public endpoint."""
import sys,argparse,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.repositories.store import system_db

def main():
    p=argparse.ArgumentParser();p.add_argument('--user-id',type=uuid.UUID,required=True);p.add_argument('--role',choices=['institution','reviewer','admin'],required=True);p.add_argument('--institution-id',type=uuid.UUID)
    a=p.parse_args()
    if a.role=='institution' and not a.institution_id:p.error('Institution users require --institution-id')
    db=system_db();db.auth.admin.get_user_by_id(str(a.user_id))
    data=dict(id=str(a.user_id),role=a.role,institution_id=str(a.institution_id) if a.institution_id else None,account_status='ACTIVE')
    db.table('profiles').upsert(data).execute()
    db.table('audit_logs').insert(dict(actor_id=str(a.user_id),action='TRUSTED_OPERATOR_PROFILE_PROVISIONED',entity_type='profiles',entity_id=str(a.user_id),metadata={'role':a.role,'method':'local trusted operator'})).execute()
    print('Profile provisioned. No password or token was recorded.')
if __name__=='__main__':main()
