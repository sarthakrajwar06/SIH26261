begin;
create table public.application_versions (
 id uuid primary key default gen_random_uuid(), application_id uuid not null references public.applications(id),
 snapshot jsonb not null, created_at timestamptz not null default now()
);
alter table public.application_versions enable row level security;
revoke all on public.application_versions from anon,authenticated;
grant select on public.application_versions to authenticated;
grant all on public.application_versions to service_role;
create policy version_read on public.application_versions for select to authenticated using(public.can_access_application(application_id));
create trigger immutable_history before update or delete on public.application_versions for each row execute function public.reject_history_mutation();
create function public.capture_submission() returns trigger language plpgsql security definer set search_path='' as $$
begin
 if new.status='PROCESSING' and old.status in ('DRAFT','RECTIFICATION_REQUIRED') then
 insert into public.application_versions(application_id,snapshot) values(new.id,
 jsonb_build_object('application',to_jsonb(new),'category',(select to_jsonb(c) from public.application_categories c where c.id=new.category_id),
 'document_versions',coalesce((select jsonb_agg(to_jsonb(d)) from public.application_documents d where d.application_id=new.id),'[]'::jsonb)));
 end if;
 return new;
end $$;
create trigger capture_submission after update on public.applications for each row execute function public.capture_submission();
create index on public.application_versions(application_id,created_at);
commit;
