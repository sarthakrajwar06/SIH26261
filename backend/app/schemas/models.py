from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import date

class ApplicationCreate(BaseModel):
    institution_id: UUID
    category_id: UUID
    academic_year: str = Field(pattern=r'^\d{4}-\d{2}$')
    programme: str = Field(default='', max_length=200)

class ApplicationPatch(BaseModel):
    academic_year: str = Field(pattern=r'^\d{4}-\d{2}$')
    programme: str = Field(default='', max_length=200)

class Review(BaseModel):
    action: Literal['OBSERVATION','REVIEWED','RECTIFICATION_REQUIRED','ADDITIONAL_EVIDENCE','MANUAL_VERIFICATION','READY_FOR_OFFICIAL_REVIEW','CLOSED']
    reason: str = Field(min_length=10, max_length=4000)

class RuleVersion(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    evaluation_type: Literal['required_document','required_field','expiry','comparison','threshold','manual','external']
    parameters: dict = Field(default_factory=dict)
    source_reference: str = Field(min_length=3, max_length=2000)
    source_url: str = ''
    provision: str = ''
    effective_from: date
    effective_to: date | None = None
    category_ids: list[UUID] = Field(default_factory=list)
    severity: Literal['INFO','WARNING','HIGH'] = 'WARNING'
    suggested_action: str = 'Request evidence and review manually'
    demo_only: bool = True
    expert_confirmed: bool = False

class RuleCreate(BaseModel):
    code: str = Field(pattern=r'^[A-Z0-9_-]{3,80}$')
    enabled: bool = False
    version: RuleVersion

class RulePatch(BaseModel):
    enabled: bool

class VerifyRequest(BaseModel):
    mode: Literal['SIMULATED','MANUAL','OFFICIAL','QR','DIGITAL_SIGNATURE'] = 'MANUAL'
    scenario: Literal['success','mismatch','unavailable','pending'] = 'pending'
    authority: str = Field(default='Unconfigured', max_length=200)

class ProfilePatch(BaseModel):
    role: Literal['institution','reviewer','admin']
    institution_id: UUID | None = None
    account_status: Literal['ACTIVE','DISABLED'] = 'ACTIVE'

class Assignment(BaseModel):
    reviewer_id: UUID
