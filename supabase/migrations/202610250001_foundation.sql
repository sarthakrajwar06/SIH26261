begin;
create extension if not exists pgcrypto;
create table public.institutions (
 id uuid primary key default gen_random_uuid(), name text not null, identifier text not null unique,
 institution_type text not null default 'DEMO', location text not null default '', created_at timestamptz not null default now()
);
create table public.profiles (
 id uuid primary key references auth.users(id) on delete cascade,
 role text not null check(role in ('institution','reviewer','admin')) default 'institution',
 institution_id uuid references public.institutions(id), account_status text not null default 'ACTIVE' check(account_status in ('ACTIVE','DISABLED')),
 created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
 check(role <> 'institution' or institution_id is not null)
);
create table public.application_categories (
 id uuid primary key default gen_random_uuid(), name text not null unique, description text not null,
 required_documents text[] not null default '{}', demo_only boolean not null default true
);
create table public.applications (
 id uuid primary key default gen_random_uuid(), institution_id uuid not null references public.institutions(id),
 reference text not null unique default ('INS-' || upper(substr(gen_random_uuid()::text,1,8))),
 category_id uuid not null references public.application_categories(id), academic_year text not null check(academic_year ~ '^\d{4}-\d{2}$'), programme text not null default '',
 status text not null default 'DRAFT' check(status in ('DRAFT','SUBMITTED','PROCESSING','PRELIMINARY_REVIEW_COMPLETE','RECTIFICATION_REQUIRED','UNDER_MANUAL_REVIEW','READY_FOR_OFFICIAL_REVIEW','CLOSED')),
 created_by uuid not null references public.profiles(id), submitted_at timestamptz,
 created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table public.reviewer_assignments (
 id uuid primary key default gen_random_uuid(), application_id uuid not null references public.applications(id), reviewer_id uuid not null references public.profiles(id), unique(application_id,reviewer_id)
);
create table public.application_documents (
 id uuid primary key default gen_random_uuid(), application_id uuid not null references public.applications(id), document_category text not null,
 storage_path text not null unique, original_filename text not null, mime_type text not null check(mime_type in ('application/pdf','image/png','image/jpeg')),
 size bigint not null check(size>0 and size<=20971520), checksum text not null check(length(checksum)=64), version integer not null default 1,
 processing_status text not null default 'QUEUED' check(processing_status in ('QUEUED','PROCESSING','COMPLETE','ERROR')),
 analysis jsonb not null default '{}', uploaded_by uuid not null references public.profiles(id), uploaded_at timestamptz not null default now(),
 unique(application_id,document_category,version)
);
create table public.processing_jobs (
 id uuid primary key default gen_random_uuid(), document_id uuid not null references public.application_documents(id),
 status text not null default 'QUEUED' check(status in ('QUEUED','PROCESSING','COMPLETE','ERROR')), error text,
 created_at timestamptz not null default now(), finished_at timestamptz
);
create unique index one_active_job on public.processing_jobs(document_id) where status in ('QUEUED','PROCESSING');
create table public.extracted_fields (
 id uuid primary key default gen_random_uuid(), document_id uuid not null references public.application_documents(id),
 field_name text not null, raw_value text not null, normalized_value text, page_number integer not null check(page_number>0), excerpt text,
 coordinates jsonb, confidence numeric check(confidence between 0 and 1), processed_at timestamptz not null default now()
);
create table public.validation_rules (
 id uuid primary key default gen_random_uuid(), code text not null unique, enabled boolean not null default false, created_at timestamptz not null default now()
);
create table public.validation_rule_versions (
 id uuid primary key default gen_random_uuid(), rule_id uuid not null references public.validation_rules(id), version integer not null check(version>0),
 title text not null, evaluation_type text not null check(evaluation_type in ('required_document','required_field','expiry','comparison','threshold','manual','external')),
 parameters jsonb not null default '{}', source_reference text not null, source_url text not null default '', provision text not null default '',
 effective_from date not null, effective_to date, category_ids uuid[] not null default '{}', severity text not null check(severity in ('INFO','WARNING','HIGH')),
 suggested_action text not null, demo_only boolean not null default true, expert_confirmed boolean not null default false,
 created_at timestamptz not null default now(), unique(rule_id,version),
 check(effective_to is null or effective_to>=effective_from), check(demo_only or expert_confirmed)
);
create table public.validation_runs (
 id uuid primary key default gen_random_uuid(), application_id uuid not null references public.applications(id), created_at timestamptz not null default now()
);
create table public.validation_findings (
 id uuid primary key default gen_random_uuid(), application_id uuid not null references public.applications(id), run_id uuid not null references public.validation_runs(id),
 rule_id uuid references public.validation_rules(id), rule_version_id uuid references public.validation_rule_versions(id),
 category text not null, status text not null check(status in ('PASS','FAIL','WARNING','NOT_APPLICABLE','PENDING','INCONCLUSIVE','MANUAL_REVIEW_REQUIRED')),
 severity text not null, explanation text not null, expected_value text, observed_value text, evidence jsonb not null default '[]', suggested_action text not null,
 manual_review_required boolean not null default true, created_at timestamptz not null default now()
);
create table public.source_verifications (
 id uuid primary key default gen_random_uuid(), document_id uuid not null references public.application_documents(id), issuing_authority text not null,
 verification_mode text not null check(verification_mode in ('SIMULATED','MANUAL','OFFICIAL','QR','DIGITAL_SIGNATURE')),
 source_identifier text not null, status text not null check(status in ('VERIFIED','MISMATCH_DETECTED','EXPIRED','PENDING','SOURCE_UNAVAILABLE','MANUAL_REVIEW_REQUIRED','UNSUPPORTED')),
 matched_fields jsonb not null default '[]', mismatched_fields jsonb not null default '[]', response_reference text, verified_at timestamptz not null default now(), explanation text not null
);
create table public.review_actions (
 id uuid primary key default gen_random_uuid(), application_id uuid not null references public.applications(id), finding_id uuid references public.validation_findings(id),
 reviewer_id uuid not null references public.profiles(id), action text not null, reason text not null check(length(reason)>=10), created_at timestamptz not null default now()
);
create table public.audit_logs (
 id uuid primary key default gen_random_uuid(), actor_id uuid references public.profiles(id), application_id uuid references public.applications(id),
 action text not null, entity_type text not null, entity_id uuid, request_id uuid not null default gen_random_uuid(), metadata jsonb not null default '{}', outcome text not null default 'SUCCESS', created_at timestamptz not null default now()
);
create table public.notifications (
 id uuid primary key default gen_random_uuid(), recipient_id uuid not null references public.profiles(id), application_id uuid references public.applications(id),
 type text not null, message text not null, read_at timestamptz, created_at timestamptz not null default now()
);
create table public.reports (
 id uuid primary key default gen_random_uuid(), application_id uuid not null references public.applications(id), storage_path text not null unique, format text not null check(format in ('json','pdf')),
 created_at timestamptz not null default now()
);
create index on public.applications(institution_id,created_at desc);
create index on public.application_documents(application_id);
create index on public.application_documents(checksum);
create index on public.extracted_fields(document_id);
create index on public.validation_findings(application_id,run_id);
create index on public.source_verifications(document_id);
create index on public.audit_logs(application_id,created_at);
create index on public.notifications(recipient_id);
create index on public.reviewer_assignments(reviewer_id);

-- Owner-controlled helpers avoid recursive policies. Not executable by anonymous users.
create function public.current_role() returns text language sql stable security definer set search_path='' as $$
 select role from public.profiles where id=auth.uid() and account_status='ACTIVE'
$$;
create function public.can_access_application(target uuid) returns boolean language sql stable security definer set search_path='' as $$
 select exists(select 1 from public.applications a join public.profiles p on p.id=auth.uid() and p.account_status='ACTIVE'
 where a.id=target and (p.role='admin' or (p.role='institution' and a.institution_id=p.institution_id)
 or (p.role='reviewer' and exists(select 1 from public.reviewer_assignments r where r.application_id=a.id and r.reviewer_id=p.id))))
$$;
create function public.can_access_document(target uuid) returns boolean language sql stable security definer set search_path='' as $$
 select exists(select 1 from public.application_documents where id=target and public.can_access_application(application_id))
$$;
revoke all on function public.current_role(),public.can_access_application(uuid),public.can_access_document(uuid) from public, anon;
grant execute on function public.current_role(),public.can_access_application(uuid),public.can_access_document(uuid) to authenticated,service_role;

-- Clients may read scoped records. ALL mutations go through authorized FastAPI routes.
DO $$ declare t text; begin
 foreach t in array array['institutions','profiles','application_categories','applications','reviewer_assignments','application_documents','processing_jobs','extracted_fields','validation_rules','validation_rule_versions','validation_runs','validation_findings','source_verifications','review_actions','audit_logs','notifications','reports'] loop
 execute format('alter table public.%I enable row level security',t);
 execute format('revoke all on public.%I from anon, authenticated',t);
 execute format('grant select on public.%I to authenticated',t);
 execute format('grant all on public.%I to service_role',t);
 end loop;
end $$;
create policy profile_read on public.profiles for select to authenticated using (id=auth.uid() or public.current_role()='admin');
create policy institutions_read on public.institutions for select to authenticated using (public.current_role()='admin' or id=(select institution_id from public.profiles where id=auth.uid() and account_status='ACTIVE') or exists(select 1 from public.applications a where a.institution_id=institutions.id and public.can_access_application(a.id)));
create policy categories_read on public.application_categories for select to authenticated using(public.current_role() is not null);
create policy applications_read on public.applications for select to authenticated using(public.can_access_application(id));
DO $$ declare t text; begin
 foreach t in array array['reviewer_assignments','application_documents','validation_runs','validation_findings','review_actions','reports'] loop
 execute format('create policy scoped_read on public.%I for select to authenticated using(public.can_access_application(application_id))',t);
 end loop;
 foreach t in array array['processing_jobs','extracted_fields','source_verifications'] loop
 execute format('create policy document_read on public.%I for select to authenticated using(public.can_access_document(document_id))',t);
 end loop;
end $$;
create policy rules_read on public.validation_rules for select to authenticated using(public.current_role() is not null);
create policy versions_read on public.validation_rule_versions for select to authenticated using(public.current_role() is not null);
create policy audit_read on public.audit_logs for select to authenticated using(public.current_role()='admin' or (application_id is not null and public.can_access_application(application_id)));
create policy notifications_read on public.notifications for select to authenticated using(recipient_id=auth.uid() and public.current_role() is not null);

-- Even a backend bug cannot rewrite immutable evidence/history using UPDATE/DELETE.
create function public.reject_history_mutation() returns trigger language plpgsql set search_path='' as $$ begin raise exception 'Append-only history'; end $$;
DO $$ declare t text; begin
 foreach t in array array['audit_logs','review_actions','validation_findings','validation_rule_versions','source_verifications'] loop
 execute format('create trigger immutable_history before update or delete on public.%I for each row execute function public.reject_history_mutation()',t);
 end loop;
end $$;
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types) values
 ('application-documents','application-documents',false,20971520,array['application/pdf','image/png','image/jpeg']),
 ('application-reports','application-reports',false,20971520,array['application/pdf','application/json']);
-- Match an actual database record, never authorize by a caller-supplied path prefix alone.
create policy document_download on storage.objects for select to authenticated using(bucket_id='application-documents' and exists(select 1 from public.application_documents d where d.storage_path=name and public.can_access_application(d.application_id)));
create policy report_download on storage.objects for select to authenticated using(bucket_id='application-reports' and exists(select 1 from public.reports r where r.storage_path=name and public.can_access_application(r.application_id)));
commit;
