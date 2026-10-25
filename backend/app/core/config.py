from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[3] / '.env', extra='ignore')
    supabase_url: str = ''
    supabase_publishable_key: str = ''
    supabase_secret_key: str = ''
    supabase_jwt_issuer: str = ''
    supabase_jwks_url: str = ''
    supabase_jwt_audience: str = 'authenticated'
    supabase_documents_bucket: str = 'application-documents'
    supabase_reports_bucket: str = 'application-reports'
    frontend_url: str = 'http://localhost:5173'
    max_upload_size_mb: int = 20
    ocr_engine: str = 'tesseract'
    llm_provider: str = 'none'
    retention_days: int = 365

@lru_cache
def settings():
    return Settings()
