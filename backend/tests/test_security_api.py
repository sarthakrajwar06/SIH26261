from pathlib import Path
from uuid import uuid4
from unittest.mock import patch
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.api.routes import app,check_rule
from app.security.auth import verify_token,Context
from app.core.config import Settings
from app.schemas.models import RuleVersion,ProfilePatch
from datetime import date,datetime,timezone,timedelta

client=TestClient(app)
def test_no_token_denied():
    for path in ['/api/v1/auth/me','/api/v1/applications','/api/v1/rules','/api/v1/applications/'+str(uuid4())+'/report.pdf']:
        assert client.get(path).status_code==401

def test_health_no_auth():assert client.get('/health').status_code==200

def test_role_escalation_denied():
    c=Context(None,{'id':'x','role':'institution'},'token')
    with pytest.raises(HTTPException) as e:c.require('admin')
    assert e.value.status_code==403

@pytest.fixture
def signing():
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    claims={'sub':str(uuid4()),'aud':'authenticated','iss':'https://test.supabase.co/auth/v1','iat':datetime.now(timezone.utc),'exp':datetime.now(timezone.utc)+timedelta(minutes=5)}
    conf=Settings(supabase_url='https://test.supabase.co',supabase_publishable_key='test',_env_file=None)
    return key,claims,conf

@pytest.mark.parametrize('change',[{}, {'aud':'wrong'},{'iss':'https://attacker.invalid'},{'exp':0}])
def test_jwt_signature_issuer_audience_expiry(signing,change):
    key,claims,conf=signing;claims.update(change);token=jwt.encode(claims,key,algorithm='RS256')
    class Key:pass
    k=Key();k.key=key.public_key()
    with patch('app.security.auth.settings',return_value=conf),patch('app.security.auth.jwks_client') as jc:
        jc.return_value.get_signing_key_from_jwt.return_value=k
        if change:
            with pytest.raises(HTTPException) as e:verify_token(token)
            assert e.value.status_code==401
        else:assert verify_token(token)['sub']==claims['sub']

def test_bad_signature_denied(signing):
    key,claims,conf=signing;other=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    token=jwt.encode(claims,other,algorithm='RS256')
    class K:pass
    k=K();k.key=key.public_key()
    with patch('app.security.auth.settings',return_value=conf),patch('app.security.auth.jwks_client') as jc:
        jc.return_value.get_signing_key_from_jwt.return_value=k
        with pytest.raises(HTTPException):verify_token(token)

def test_unverified_production_rule_rejected():
    v=RuleVersion(title='Unconfirmed provision',evaluation_type='manual',source_reference='UNCONFIRMED',effective_from=date.today(),demo_only=False)
    with pytest.raises(HTTPException):check_rule(v)

def test_rule_params_checked():
    v=RuleVersion(title='Demo rule',evaluation_type='threshold',parameters={},source_reference='DEMO only',effective_from=date.today())
    with pytest.raises(HTTPException):check_rule(v)

def test_sensitive_tables_have_rls_and_no_client_write_grants():
    # Static guardrail, NOT a substitute for executing live RLS tests.
    sql=(Path(__file__).resolve().parents[2]/'supabase/migrations/202610250001_foundation.sql').read_text()
    assert 'enable row level security' in sql
    assert 'revoke all on public.%I from anon, authenticated' in sql
    assert 'grant select on public.%I to authenticated' in sql
    assert 'public.can_access_application' in sql
    assert "storage_path=name" in sql
    assert 'immutable_history before update or delete' in sql
    assert "('application-documents','application-documents',false" in sql

def test_openapi_no_untrusted_finding_id_on_application_action():
    op=client.get('/openapi.json').json()['paths']['/api/v1/applications/{id}/review-actions']['post']
    assert not any(p['name']=='finding_id' for p in op.get('parameters',[]))

@pytest.mark.parametrize('method,path',[
    ('get','/applications/{id}'),('get','/applications/{id}/report'),('get','/applications/{id}/report.pdf'),
    ('get','/documents/{id}/content'),('get','/documents/{id}'),('get','/applications/{id}/findings'),
    ('get','/applications/{id}/audit'),('post','/applications/{id}/validate'),('post','/documents/{id}/process')])
def test_foreign_resource_fails_before_privileged_access(method,path):
    from app.security.auth import context
    c=Context(None,{'id':str(uuid4()),'role':'reviewer'},'test-only')
    def denied(*args):raise HTTPException(404,'Record not found or not authorized')
    c.one=denied
    app.dependency_overrides[context]=lambda:c
    try:
        with patch('app.api.routes.system_db') as privileged:
            response=getattr(client,method)('/api/v1'+path.format(id=uuid4()))
            assert response.status_code==404
            privileged.assert_not_called()
    finally:app.dependency_overrides.clear()
