"""Opt-in actual Supabase isolation checks. Supply two pre-provisioned synthetic users.
Never runs against government services. See docs/security.md.
"""
import os
import pytest
from supabase import create_client

pytestmark=pytest.mark.skipif(not os.getenv('RUN_LIVE_SUPABASE_TESTS'),reason='No configured Supabase test project / synthetic accounts')

def test_live_cross_institution_and_storage_isolation():
    url=os.environ['SUPABASE_URL'];key=os.environ['SUPABASE_PUBLISHABLE_KEY']
    a=create_client(url,key);b=create_client(url,key)
    a.auth.sign_in_with_password({'email':os.environ['TEST_USER_A_EMAIL'],'password':os.environ['TEST_USER_A_PASSWORD']})
    b.auth.sign_in_with_password({'email':os.environ['TEST_USER_B_EMAIL'],'password':os.environ['TEST_USER_B_PASSWORD']})
    apps_a=a.table('applications').select('*').execute().data
    apps_b=b.table('applications').select('*').execute().data
    assert apps_a and apps_b,'Seed applications for both institutions before running'
    assert not ({x['id'] for x in apps_a}&{x['id'] for x in apps_b})
    foreign=apps_b[0]['id']
    assert a.table('applications').select('*').eq('id',foreign).execute().data==[]
    assert a.table('validation_findings').select('*').eq('application_id',foreign).execute().data==[]
    for table in ('profiles','applications','audit_logs','validation_rules'):
        with pytest.raises(Exception):a.table(table).insert({'id':'00000000-0000-4000-8000-000000000009'}).execute()
    for table,bucket in [('application_documents','application-documents'),('reports','application-reports')]:
        rows=b.table(table).select('*').eq('application_id',foreign).execute().data
        assert rows,f'Seed a private {table} record for institution B'
        assert a.table(table).select('*').eq('application_id',foreign).execute().data==[]
        with pytest.raises(Exception):a.storage.from_(bucket).download(rows[0]['storage_path'])
