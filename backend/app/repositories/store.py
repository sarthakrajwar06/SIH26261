from functools import lru_cache
import uuid
from app.core.request_context import request_id
from supabase import create_client
from fastapi import HTTPException
from app.core.config import settings

@lru_cache
def system_db():
    s = settings()
    if not s.supabase_secret_key: raise HTTPException(503, 'Server Supabase secret key not configured')
    return create_client(s.supabase_url, s.supabase_secret_key)

def insert(table, data):
    return system_db().table(table).insert(data).execute().data[0]

def update(table, id, data):
    return system_db().table(table).update(data).eq('id',str(id)).execute().data

def audit(ctx, action, entity, id, application_id=None, metadata=None):
    insert('audit_logs',dict(actor_id=ctx.uid, action=action, entity_type=entity, entity_id=str(id), application_id=str(application_id) if application_id else None, metadata=metadata or {}, request_id=request_id.get() or str(uuid.uuid4())))

def notify(application, type, message):
    insert('notifications',dict(recipient_id=application['created_by'], application_id=application['id'], type=type, message=message))
