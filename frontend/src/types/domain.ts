export type Role='institution'|'reviewer'|'admin';
export type WorkflowState='DRAFT'|'SUBMITTED'|'PROCESSING'|'PRELIMINARY_REVIEW_COMPLETE'|'RECTIFICATION_REQUIRED'|'UNDER_MANUAL_REVIEW'|'READY_FOR_OFFICIAL_REVIEW'|'CLOSED';
export interface Profile {id:string;role:Role;institution_id:string|null;account_status:'ACTIVE'|'DISABLED'}
export interface Application {id:string;reference:string;institution_id:string;category_id:string;academic_year:string;programme:string;status:WorkflowState;created_at:string;updated_at:string}
export interface EvidenceReference {document_id:string;page?:number;excerpt?:string}
export interface Finding {id:string;application_id:string;rule_version_id:string|null;category:string;status:string;severity:string;explanation:string;expected_value:string|null;observed_value:string|null;evidence:EvidenceReference[];suggested_action:string;manual_review_required:boolean}
export interface Page<T> {items:T[];total:number;page:number;page_size:number}
