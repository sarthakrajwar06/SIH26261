begin;
-- Serialize a document insert against submission so uploads cannot slip into a locked case.
create function public.guard_document_insert() returns trigger language plpgsql security definer set search_path='' as $$
declare current_status text;
begin
 select status into current_status from public.applications where id=new.application_id for update;
 if current_status not in ('DRAFT','RECTIFICATION_REQUIRED') then raise exception 'Application is locked for document changes'; end if;
 return new;
end $$;
create trigger document_insert_guard before insert on public.application_documents for each row execute function public.guard_document_insert();
-- Original file metadata may never be altered, even by the processor.
create function public.guard_document_original() returns trigger language plpgsql set search_path='' as $$
begin
 if (new.application_id,new.document_category,new.storage_path,new.original_filename,new.mime_type,new.size,new.checksum,new.version,new.uploaded_by,new.uploaded_at)
 is distinct from (old.application_id,old.document_category,old.storage_path,old.original_filename,old.mime_type,old.size,old.checksum,old.version,old.uploaded_by,old.uploaded_at)
 then raise exception 'Original document metadata is immutable'; end if;
 return new;
end $$;
create trigger document_original_guard before update on public.application_documents for each row execute function public.guard_document_original();
commit;
