from functools import lru_cache
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from supabase import create_client
from app.core.config import settings

bearer = HTTPBearer(auto_error=False)

@lru_cache
def jwks_client(url):
    return jwt.PyJWKClient(url)

# Asymmetric Supabase signing keys only. No unverified claims or algorithm negotiation.
def verify_token(token: str):
    s = settings()
    if not s.supabase_url or not s.supabase_publishable_key:
        raise HTTPException(503, 'Supabase is not configured')
    try:
        key = jwks_client(s.supabase_jwks_url or s.supabase_url + '/auth/v1/.well-known/jwks.json').get_signing_key_from_jwt(token)
        return jwt.decode(token, key.key, algorithms=['ES256', 'RS256'],
                          audience=s.supabase_jwt_audience,
                          issuer=s.supabase_jwt_issuer or s.supabase_url + '/auth/v1',
                          options={'require': ['exp', 'iat', 'sub', 'aud', 'iss']})
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(401, 'Invalid or expired session')

class Context:
    def __init__(self, db, profile, token):
        self.db, self.profile, self.token = db, profile, token
    @property
    def uid(self): return self.profile['id']
    @property
    def role(self): return self.profile['role']
    def require(self, *roles):
        if self.role not in roles: raise HTTPException(403, 'Role not authorized')
    def one(self, table, id):
        rows = self.db.table(table).select('*').eq('id', str(id)).execute().data
        if not rows: raise HTTPException(404, 'Record not found or not authorized')
        return rows[0]

def context(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if not credentials: raise HTTPException(401, 'Sign in required')
    claims = verify_token(credentials.credentials)
    s = settings()
    db = create_client(s.supabase_url, s.supabase_publishable_key)
    db.postgrest.auth(credentials.credentials)
    # Storage also needs the user token, not the publishable key.
    db.storage.session.headers['Authorization'] = 'Bearer ' + credentials.credentials
    rows = db.table('profiles').select('*').eq('id', claims['sub']).execute().data
    if not rows or rows[0]['account_status'] != 'ACTIVE':
        raise HTTPException(403, 'Account is not provisioned or is inactive')
    return Context(db, rows[0], credentials.credentials)
