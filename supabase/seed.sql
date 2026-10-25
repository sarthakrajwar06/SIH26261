-- Fictional development data. No production provisions or official claims.
insert into public.institutions(id,name,identifier,location) values
 ('10000000-0000-4000-8000-000000000001','DEMO Meridian Institute of Technology','DEMO-MERIDIAN-001','Fictional campus, India'),
 ('10000000-0000-4000-8000-000000000002','DEMO Riverstone Technical Institute','DEMO-RIVERSTONE-002','Fictional campus, India') on conflict do nothing;
insert into public.application_categories(id,name,description,required_documents) values
 ('20000000-0000-4000-8000-000000000001','DEMO Extension of Approval','Synthetic checklist, not an official AICTE requirement',array['undertaking','certificate','faculty_list','infrastructure']),
 ('20000000-0000-4000-8000-000000000002','DEMO Programme Change','Synthetic programme-change checklist',array['undertaking','programme_evidence']) on conflict do nothing;
DO $$ declare rid uuid; cat uuid := '20000000-0000-4000-8000-000000000001'; kind text; begin
 foreach kind in array array['undertaking','certificate','faculty_list','infrastructure'] loop
 insert into public.validation_rules(code,enabled) values('DEMO-REQUIRED-'||upper(kind),true) on conflict(code) do nothing returning id into rid;
 if rid is not null then insert into public.validation_rule_versions(rule_id,version,title,evaluation_type,parameters,source_reference,effective_from,category_ids,severity,suggested_action)
 values(rid,1,'DEMO required evidence: '||kind,'required_document',jsonb_build_object('category',kind),'Synthetic development checklist; not a regulatory provision','2020-01-01',array[cat],'WARNING','Supply evidence or request manual review'); end if;
 end loop;
 insert into public.validation_rules(code,enabled) values('DEMO-EXPIRY',true) on conflict do nothing returning id into rid;
 if rid is not null then insert into public.validation_rule_versions(rule_id,version,title,evaluation_type,parameters,source_reference,effective_from,severity,suggested_action)
 values(rid,1,'DEMO certificate expiry check','expiry','{"field":"expiry_date"}','Synthetic date check','2020-01-01','WARNING','Confirm validity with issuer'); end if;
 insert into public.validation_rules(code,enabled) values('DEMO-IDENTITY',true) on conflict do nothing returning id into rid;
 if rid is not null then insert into public.validation_rule_versions(rule_id,version,title,evaluation_type,parameters,source_reference,effective_from,severity,suggested_action)
 values(rid,1,'DEMO institution identifier consistency','comparison','{"field":"institution_identifier","institution_field":"identifier"}','Synthetic identity consistency check','2020-01-01','HIGH','Confirm identifiers against authorized records'); end if;
end $$;
